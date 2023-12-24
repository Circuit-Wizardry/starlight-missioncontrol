import utime
import select
import math
import starlight
import json
import time
import gpio
import sys
import fusion
import machine
from machine import Pin

time.sleep(3);

def getAltitude(pressure):
    return (145366.45 * (1.0 - pow(pressure / 1013.25, 0.190284))); # returns altitude in feet


# ----------HARDWARE------------
outputs = [gpio.GPIO(0, 6), gpio.GPIO(1, 7)]

connected = False
mode = 0;

poll_obj = select.poll()
poll_obj.register(sys.stdin,1)
led = Pin(24, Pin.OUT)

read_data = [];

# ON STARTUP do something
# startup modes:
# 0 - programming mode/default mode
# 1 - flight mode
file = open("data.json", "r")
x = file.read()
x = x.replace("'", '"');
y = 0
try:
    y = json.loads(x)
except:
    print("defaulting to startupMode 0")
    y = json.loads('{"startupMode":0}')
mode = y["startupMode"]

# Set our pyro channel settings

try:
    for i in range(len(y["features"])):
        if y["features"][i]["type"] == "PYRO": # gpio is included for "emulate pyro charge"
            if y["features"][i]["data"]["action"] == "none":
                outputs[i].setTrigger(0);
            if y["features"][i]["data"]["action"] == "main":
                if y["features"][i]["data"]["apogee"] == True:
                    outputs[i].setTrigger(1);
                else:   
                    outputs[i].setTrigger(2);
                    outputs[i].setCustom(y["features"][i]["data"]["height"]);
            if y["features"][i]["data"]["action"] == "drogue": # drogue only has one option: apogee
                outputs[i].setTrigger(1);
            if y["features"][i]["data"]["action"] == "custom": # custom: this is where things get fun :)
                outputs[i].setTrigger(y["features"][i]["data"]["trigger"]);
                outputs[i].setCustom(y["features"][i]["data"]["value"]);
                outputs[i].setFireLength(y["features"][i]["data"]["time"] * 12.5);
except:
    led.value(1)
    time.sleep(0.1)
    led.value(0)
    time.sleep(0.1)
    led.value(1)
    time.sleep(0.1)
    led.value(0)
            

        
        
# outputs[0].setTrigger(y["features"][0]["data"]["action"]);
# outputs[1].setTrigger(y["features"][1]["data"]["action"]);

# Clean up files
file.close()
time.sleep(0.25);
x = x.replace('"startupMode":1', '"startupMode":0');
file = open("data.json", "w")
file.write(x)
file.close()


while mode == 0:
    # Programming Mode
    
    # Read serial
    while poll_obj.poll(0):
        read_data.append(sys.stdin.read(1))
    
    if not connected:
        for i in range(len(read_data)):
            # 0x11 is start byte then next byte determines "type" of operation. 0x12 means successfully connected
            if read_data[i] == '\x11':
                if read_data[i+1] == '\x12':
                    led.value(1);
                    connected = True;
                    read_data = [];

                    # send curent data.json to MissionControl
                    data_file = open('data.json', 'r')
                    count = 0
                    while True:
                        chunk = data_file.read(1)
                        if chunk == "": # if chunk is empty
                            break;
                        print(chunk, end="")
                        count += 1;
                    
                    data_file.close()
                    
                    utime.sleep(0.25);
                    led.value(0);
                    break;
                    
    
        # Searching for connection. sc is starlight's code to send
        print("sc");
        utime.sleep(0.25);

    if connected:
        writing_data = False;
        data_to_write = [];
        for i in range(len(read_data)):
            # 0x11 is start byte then next byte determines "type" of operation. 0x13 means writing data
            if writing_data:
                data_to_write.append(str(read_data[i]));
            if read_data[i] == '\x11':
                if read_data[i+1] == '\x13':
                    writing_data = True;
        if writing_data:
            led.value(1);
            data_to_write[0] = ""; # get rid of the x13 that appears for some reason
            file = open("data.json", "w")
            file.write(''.join(data_to_write))
            file.close()
            utime.sleep(0.05)
            led.value(0);
            file_check = open("data.json", "r")
            try:
                json.loads(file_check.read())
                writing_data = False;
                read_data = [];
            except:
                pass;
            file_check.close()
      
    if connected:
        for i in range(len(read_data)):
            # 0x11 is start byte then next byte determines "type" of operation. 0x14 means ready to recieve
            if writing_data:
                data_to_write.append(str(read_data[i]));
            if read_data[i] == '\x11':
                if read_data[i+1] == '\x14':
                    file = open('flight_data.txt', 'r')
                    count = 0
                    while True:
                        chunk = file.read(1)
                        if "b" in chunk and count > 1: # count greater than one in order to avoid stopping read at the start
                            break;
                        print(chunk, end="")
                        count += 1;

    if connected:
        for i in range(len(read_data)):
            # 0x11 is start byte then next byte determines "type" of operation. 0x16 means disconnect
            if writing_data:
                data_to_write.append(str(read_data[i]));
            if read_data[i] == '\x11':
                if read_data[i+1] == '\x16':
                    connected = False;
                    led.value(1);
                    time.sleep(0.25);
                    led.value(0);



i2c = machine.I2C(1, scl=machine.Pin(3), sda=machine.Pin(2), freq=9600)

gyr = starlight.ICM42605(i2c, 0x68) # create our ICM-42605 object
gyr.config_gyro() # set up our gyroscope/accelerometer
gyr.enable() # enable our gyroscope/accelerometer
#gyr.get_bias() # calibrate our gyroscope/accelerometer

temp = starlight.BMP388(i2c, 0x76) # create our BMP388 object
temp.enable_temp_and_pressure() # enable our sensors
temp.calibrate() # calibrate our sensors
f = fusion.Fusion()

# temp.setGroundPressure(temp.getPressure());

time.sleep(3); # giving a grace period before board is "ready"


accelX = 0;
accelY = 0;
accelZ = 0;

file = open("flight_data.txt", "w")
file.write('b');
count = 0

event = 0;

apoapsis = 10000;
apoapsis_timeout = 0;
reached_apoapsis = False;
pressure_values = []
baseline_pressure = 0;

limiter = time.ticks_ms();
lastTime = time.ticks_ms();
hz = 0;

baseline_pressure = temp.getPressure();

l_val = False;

while mode == 1: # our main loop
    if l_val == True:
        led.value(False);
        l_val = False;
    else:
        led.value(True);
        l_val = True;
    
    lastTime = time.ticks_ms();
    data = gyr.get_accel_and_gyro_data()
    f.update_nomag((data[0], data[1], data[2]), (data[3], data[4], data[5]))

    gyr.get_acceleration()
    count += 1;
    hz += 1;
    
    gpevent = gpio.getEvent()
    if gpevent > 0:
        event = gpevent;
    
    # Raw accelaration values
    accelX = gyr.ax #+ math.sin(f.pitch * (math.pi/180));
    accelY = gyr.ay #- math.cos(f.pitch * (math.pi/180)) * math.sin(f.roll * (math.pi/180))
    accelZ = gyr.az #- math.cos(f.pitch * (math.pi/180)) * math.cos(f.roll * (math.pi/180))
    
    
    # Pressure averaging
    pressure = temp.getPressure();
    
    pressure_values.append(pressure);
    
    if len(pressure_values) > 5:
        pressure_values.pop(0);
        
    avg_pressure = 0;
    for i in range(len(pressure_values)):
        avg_pressure += pressure_values[i];
    
    avg_pressure = avg_pressure / len(pressure_values);
    
    
    # Apogee detection
    if avg_pressure - pressure > 0.05:
        apoapsis = avg_pressure;
        apoapsis_timeout = 0;
    elif abs(avg_pressure - apoapsis) > 0.1 and len(pressure_values) == 5:
        if apoapsis == 10000:
            apoapsis = avg_pressure;
            baseline_pressure = avg_pressure;
        apoapsis_timeout += 1;
    else:
        apoapsis_timeout = 0;
        
    if apoapsis_timeout > 3 and not reached_apoapsis:
        reached_apoapsis = True;
        print("apoapsis")
        gpio.runTrigger(outputs, 1);
        led.value(1)
        event = 2;
    
    altitude = getAltitude(avg_pressure);
    
    print(altitude)
    
    # Log data
    file.write(str(event) + ',' + str(accelX) + ',' + str(accelY) + ',' + str(accelZ) + ',' + str(altitude) + ',' + str(temp.getTemperature()) + ',' + str(f.roll) + ',' + str(f.pitch) + ':')
    
    # Save logged data
    if count % 50 == 0:
        print("Pitch: " + str("%.2f" % f.pitch) + " Roll: " + str("%.2f" % f.roll) + "\naX: " + str(accelX) + "\naY: " + str(accelY) + "\naZ: " + str(accelZ) )
        file.close()
        file = open("flight_data.txt", "a")
        
    event = 0;
    
    gpio.updateTimeouts();
    gpio.checkForRuns(outputs, altitude, reached_apoapsis, accelX, accelY, accelZ);
    

    limiter = time.ticks_ms();
    # Loop control
    time.sleep(((limiter - lastTime - 80) * -1)/1000); # 80 = loop every 80 ms = 12.5hz
    limiter = time.ticks_ms();

    
    hz = 1/((limiter - lastTime)/1000);
#     print(hz);
    
    

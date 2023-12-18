import utime
import select
import math
import starlight
import json
import time
import sys
import fusion
from machine import Pin

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
y = 0;
try:
    y = json.loads(x)
except:
    y = json.loads('{"startupMode": 0 }')
mode = y["startupMode"]


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
                    utime.sleep(0.25);
                    led.value(0);
                    break;
                    
    
        # Searching for connection
        print("sc");
        utime.sleep(0.25);

    if connected:
        writing_data = False;
        data_to_write = [];
        for i in range(len(read_data)):
            # 0x11 is start byte then next byte determines "type" of operation. 0x13 means data
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

accelX = 0;
accelY = 0;
accelZ = 0;

file = open("flight_data.txt", "w")
file.write('b');
count = 0

event = 0;

while mode == 1: # our main loop
    data = gyr.get_accel_and_gyro_data()
    f.update_nomag((data[0], data[1], data[2]), (data[3], data[4], data[5]))

    gyr.get_acceleration()
    count += 1;
    
    accelX = gyr.ax + math.sin(f.pitch * (math.pi/180));
    accelY = gyr.ay - math.cos(f.pitch * (math.pi/180)) * math.sin(f.roll * (math.pi/180))
    accelZ = gyr.az - math.cos(f.pitch * (math.pi/180)) * math.cos(f.roll * (math.pi/180))
    
    if accelY > 1:
        event = 1
        print('launch!')
    
    
    file.write(str(event) + ',' + str(accelX) + ',' + str(accelY) + ',' + str(accelZ) + ',' + str(temp.getPressure()) + ',' + str(temp.getTemperature()) + ',' + str(f.roll) + ',' + str(f.pitch) + ':')
    
    if count % 50 == 0:
        print("Pitch: " + str("%.2f" % f.pitch) + " Roll: " + str("%.2f" % f.roll) + "\naX: " + str(accelX) + "\naY: " + str(accelY) + "\naZ: " + str(accelZ) )

    event = 0;
    
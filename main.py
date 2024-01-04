import utime
import select
import math
import starlight
import json
import time
import gpio
import _thread
import sys
import fusion
import machine
from machine import Pin, PWM

defaultJson = '{"startupMode":0,"features":[{"data":{"action":"none"},"id":0,"type":"PYRO"},{"data":{"action":"none"},"id":1,"type":"PYRO"},{"data":{"action":"none"},"id":2,"type":"GPIO"},{"data":{"action":"none"},"id":3,"type":"GPIO"},{"data":{"action":"none"},"id":4,"type":"GPIO"},{"data":{"action":"none"},"id":5,"type":"GPIO"},{"data":{"action":"none"},"id":6,"type":"GPIO"},{"data":{"action":"none"},"id":7,"type":"GPIO"}]}'

def getAltitude(pressure):
    return (145366.45 * (1.0 - pow(pressure / 1013.25, 0.190284))) # returns altitude in feet

def clamp(n, minn, maxn):
    if n < minn:
        return minn
    elif n > maxn:
        return maxn
    else:
        return n

time.sleep(3)

baseline_altitude = 0
def getAltitude(pressure):
    return (145366.45 * (1.0 - pow(pressure / 1013.25, 0.190284))) # returns altitude in feet


# ----------HARDWARE------------
# pyro channels and GPIO pins are treated the same in firmware
outputs = [gpio.GPIO(0, 7), gpio.GPIO(1, 6), gpio.GPIO(2, 0), gpio.GPIO(3, 1), gpio.GPIO(4, 16), gpio.GPIO(5, 17), gpio.GPIO(6, 18), gpio.GPIO(7, 19)]
leds = [Pin(24, Pin.OUT)]
buzzers = []

# -- HARDWARE FUNCTIONS --
def toggleLeds():
    for i in range(len(leds)):
        if leds[i].value() == 0:
            leds[i].value(1)
        else:
            leds[i].value(0)

def buzz_blocking(duration):
    for i in range(len(buzzers)):
        buzzers[i].value(1)
        time.sleep(duration)
        buzzers[i].value(0)


connected = False
mode = 0

poll_obj = select.poll()
poll_obj.register(sys.stdin,1)

read_data = []

# ON STARTUP do something
# startup modes:
# 0 - programming mode/default mode
# 1 - flight mode
file = None
x = ""

try:
    file = open("data.json", "r")
except:
    file = open("data.json", "w")
    file.write(defaultJson)
    file.close()
    file = open("data.json", "r")

x = file.read()
x = x.replace("'", '"')
y = 0
try:
    y = json.loads(x)
except:
    print("defaulting to startupMode 0")
    y = json.loads(defaultJson)
mode = y["startupMode"]

# Set our pyro channel settings
tvc_enabled = False

try:
    for i in range(len(y["features"])):
        print(y["features"][i]["type"])
        if y["features"][i]["type"] == "PYRO" or y["features"][i]["type"] == "GPIO": # gpio is included for "emulate pyro charge"
            action = y["features"][i]["data"]["action"]
            if action == "none":
                outputs[i].setTrigger(0)
            if action == "main":
                outputs[i].setFireLength(12.5 * 5)
                if y["features"][i]["data"]["apogee"] == True:
                    outputs[i].setTrigger(1)
                else:   
                    outputs[i].setTrigger(2)
                    outputs[i].setCustom(y["features"][i]["data"]["height"])
            if action == "drogue": # drogue only has one option: apogee
                outputs[i].setTrigger(1)
                outputs[i].setFireLength(12.5 * 5) # 5 seconds
            if action == "custom": # custom: this is where things get fun :)
                outputs[i].setTrigger(y["features"][i]["data"]["trigger"])
                outputs[i].setCustom(y["features"][i]["data"]["value"])
                outputs[i].setFireLength(y["features"][i]["data"]["time"] * 12.5)
            if action == "output": # output - we either put in LEDs or buzzers
                print("output!")
                if y["features"][i]["data"]["data"]["action"] == "buzzer":
                    print("buzzer found")
                    buzzers.append(Pin(y["features"][i]["data"]["pin"], Pin.OUT))
                if y["features"][i]["data"]["data"]["action"] == "led":
                    leds.append(Pin(y["features"][i]["data"]["pin"], Pin.OUT))

except:
    print("error lmao")
    toggleLeds()
    time.sleep(0.1)
    toggleLeds()
    time.sleep(0.1)
    toggleLeds()
    time.sleep(0.1)
    toggleLeds()
            

       
# outputs[0].setTrigger(y["features"][0]["data"]["action"])
# outputs[1].setTrigger(y["features"][1]["data"]["action"])

# Clean up files
file.close()
time.sleep(0.25)

# two short beeps to signal board is on
buzz_blocking(0.1)
time.sleep(0.25)
buzz_blocking(0.1)

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
                    toggleLeds()
                    connected = True
                    read_data = []

                    # send curent data.json to MissionControl
                    data_file = open('data.json', 'r')
                    count = 0
                    while True:
                        chunk = data_file.read(1)
                        if chunk == "": # if chunk is empty
                            break
                        print(chunk, end="")
                        count += 1
                    
                    data_file.close()
                    
                    buzz_blocking(0.1)
                    utime.sleep(0.25)
                    toggleLeds()
                    break
                    
    
        # Searching for connection. sc is starlight's code to send
        print("sc")
        utime.sleep(0.25)

    if connected:
        writing_data = False
        data_to_write = []
        for i in range(len(read_data)):
            # 0x11 is start byte then next byte determines "type" of operation. 0x13 means writing data
            if writing_data:
                data_to_write.append(str(read_data[i]))
            if read_data[i] == '\x11':
                if read_data[i+1] == '\x13':
                    writing_data = True
        if writing_data:
            toggleLeds()
            data_to_write[0] = "" # get rid of the x13 that appears for some reason
            file = open("data.json", "w")
            file.write(''.join(data_to_write))
            file.close()
            utime.sleep(0.05)
            toggleLeds()
            file_check = open("data.json", "r")
            try:
                json.loads(file_check.read())
                writing_data = False
                read_data = []
            except:
                pass
            file_check.close()
      
    if connected:
        for i in range(len(read_data)):
            # 0x11 is start byte then next byte determines "type" of operation. 0x14 means ready to recieve
            if writing_data:
                data_to_write.append(str(read_data[i]))
            if read_data[i] == '\x11':
                if read_data[i+1] == '\x14':
                    file = open('flight_data.txt', 'r')
                    count = 0
                    while True:
                        chunk = file.read(1)
                        if "b" in chunk and count > 1: # count greater than one in order to avoid stopping read at the start
                            break
                        print(chunk, end="")
                        count += 1

    if connected:
        for i in range(len(read_data)):
            # 0x11 is start byte then next byte determines "type" of operation. 0x16 means disconnect
            if writing_data:
                data_to_write.append(str(read_data[i]))
            if read_data[i] == '\x11':
                if read_data[i+1] == '\x16':
                    connected = False
                    toggleLeds()
                    time.sleep(0.25)
                    toggleLeds()




# That's the end of the "configuration mode" code.
# Below is the flight mode code.
# A gap is included in order to separate them












































i2c = machine.I2C(1, scl=machine.Pin(3), sda=machine.Pin(2), freq=100000)

gyr = starlight.ICM42605(i2c, 0x68) # create our ICM-42605 object
gyr.config_gyro() # set up our gyroscope/accelerometer
gyr.enable() # enable our gyroscope/accelerometer

temp = starlight.BMP388(i2c, 0x76) # create our BMP388 object
temp.enable_temp_and_pressure() # enable our sensors
temp.calibrate() # calibrate our sensors
f = fusion.Fusion()

pressure = 0
temperature = 0

launched = False
landed = False
apogee = False
burnout = False
calibrated = False
calibrating = False

event = 0

# clear file
flightDataClear = open("flight_data.txt", "w")
flightDataClear.write("b")
flightDataClear.close()


# Thread for data collection
def thread_func():
    global calibrating
    global calibrated
    global pressure
    global temperature
    __t1_cnt = 0
    while True:
        __t1_cnt += 1
        if calibrating:
            gyr.get_bias()
            calibrating = False
            calibrated = True
        gyr.read_fifo()
        gyr.get_acceleration()
        data = gyr.get_accel_and_gyro_data()
        
        _ptemp = temp.getPressure()
        _ttemp = temp.getTemperature()
        
        if not _ptemp == -1:
            pressure = _ptemp
        if not _ttemp == -1:
            temperature = _ttemp
        
        f.update_nomag((data[0], data[1], data[2]), (data[3], data[4], data[5]))
        
        # code to save flight data
        if __t1_cnt % 20 == 0:
            file = open("flight_data.txt", "a")
            file.write(str(event) + ',' + str(time.ticks_ms()) + ',' + str(gyr.ax) + ',' + str(gyr.ay) + ',' + str(gyr.az) + ',' + str(getAltitude(pressure) - getAltitude(bsln_pressure)) + ',' + str(temperature) + ',' + str(f.roll) + ',' + str(f.pitch) + ':')
            file.close()
        
_thread.start_new_thread(thread_func, ())

# gx and gz are what we want for TVC
gx_trgt = 0
gz_trgt = 0

gx_err = 0
gz_err = 0

gain_px = 0.25
gain_pz = 0.25

gain_ix = 0.2
gain_iz = 0.2

gain_dx = 0.05
gain_dz = 0.05

ix = 0
iz = 0

hz = 100000

count = 0
bsln_time = time.ticks_us()

# before the main loop starts, we calculate our baseline pressure with some delays
bsln_pressure = 0
for i in range(10):
    bsln_pressure += pressure
    time.sleep(0.001) # sleep for 1ms

bsln_pressure = bsln_pressure / 10

apogee_counter = 0
apogee_height = 0


# Switch back to startupMode 0 RIGHT BEFORE starting logging
x = x.replace('"startupMode":1', '"startupMode":0')
fl = open("data.json", "w")
fl.write(x)
fl.close()
while True: # our main loop
    loop_time = time.ticks_us()
    count += 1
    _ax = gyr.ax
    _ay = gyr.ay
    _az = gyr.az
    
    if _ay < 1 and not launched:
        # this is pre-launch mode when determining whether we're upright or not
        if not calibrated and not calibrating and _ay > 0.95:
            print("calibrating")
            calibrating = True
    
    if _ay > 1.5 and not launched:
        gyr.gx = 0
        gyr.gy = 0
        gyr.gz = 0
        gpio.runTrigger(outputs, 5, 0)
        print("Launched!")
        launched = True
    
    if getAltitude(pressure - bsln_pressure) > apogee_height and launched and not apogee:
        apogee_height = getAltitude(pressure - bsln_pressure)
    if getAltitude(pressure - bsln_pressure) < apogee_height and launched and not apogee:
        apogee_counter += 1
        if apogee_counter > 4:
            # detect apogee
            gpio.runTrigger(outputs, 1, 0)
            apogee = True
            pass

    # PI controller(s). we need two - one for X and one for Z
    if launched and not apogee and tvc_enabled:
        x_sp_pv = gyr.gx/200 - gx_trgt
        z_sp_pv = gyr.gz/200 - gz_trgt
        
        __prop_x = x_sp_pv # proportion (how far away we are from desired value)
        __prop_z = z_sp_pv # "                                                 "
        
        ix += x_sp_pv/hz # integral (is reset when interval +-1 is reached)
        iz += z_sp_pv/hz # "                                              "
        
        if abs(x_sp_pv) < 1: # reset integral
            ix = 0
        if abs(z_sp_pv) < 1:
            iz = 0
            
        # clamp integral
        ix = clamp(ix, -20, 20)
        iz = clamp(iz, -20, 20)
        
        # calculate our error
        x_ut = (__prop_x * gain_px) + (ix * gain_ix)
        z_ut = (__prop_z * gain_pz) + (iz * gain_iz)
        
        x_degrees_compensation = clamp((ix / 2), -5, 5) # ix from -10 to 10 will influence x degrees
        z_degrees_compensation = clamp((iz / 2), -5, 5) # iz from -10 to 10 will influence z degrees

        print(x_degrees_compensation, z_degrees_compensation)

    hz = (1/(time.ticks_us()-loop_time)) * 1000 * 1000

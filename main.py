import utime
import select
import json
import sys
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
y = json.loads(x)
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
                    connected = True;
                    read_data = [];
                    break;
                    
    
        # Searching for connection
        print("sc");
        utime.sleep(0.25);

    if connected:
        writing_data = False;
        data_to_write = [];
        for i in range(len(read_data)):
            # 0x11 is start byte then next byte determines "type" of operation. 0x12 means successfully connected
            if writing_data:
                data_to_write.append(str(read_data[i]));
            if read_data[i] == '\x11':
                if read_data[i+1] == '\x13':
                    writing_data = True;
        if writing_data:
            data_to_write[0] = ""; # get rid of the x13 that appears for some reason
            file = open("data.json", "w")
            file.write(''.join(data_to_write))
            file.close()
                    

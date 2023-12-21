from machine import Pin

class GPIO:
    pin = 0;
    trigger = 0;
    fireLength = 0;
    
    def __init__(self, pin):
        this.pin = pin;
    
    def setTrigger(trigger):
        this.trigger = trigger;
        
    def setFireLength(fireLength):
        this.fireLength = fireLength;
        
    def getTrigger():
        # 0 is none
        # 1 is apogee
        # 2 is altitude going DOWN
        # 3 is altutude going UP
        # 4 is at motor burnout
        # 5 is at landing
        return trigger;
    
    def getFireLength():
        # in ms
        return 1000;
    
    def trigger():
        pyro = Pin(pin, Pin.OUT);
        pyro.value(1);
        return (pyro, fireLength);
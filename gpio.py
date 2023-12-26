from machine import Pin

timeouts = []

global event
event = 0

def getEvent():
    global event
    if event > 0:
        s = event
        event = 0
        print("sent event " + str(s))
        return s
    else:
        return 0

def runTrigger(pins, triggerId, eventId):
    for i in range(len(pins)):
        print("finding " + str(pins[i].getTrigger()))
        if pins[i].getTrigger() == triggerId:
            print("found: " + str(pins[i].getTrigger()))
            pins[i].trigger(eventId)
            timeouts.append([pins[i], pins[i].getFireLength()])


def updateTimeouts():
    for i in range(len(timeouts)):
        if timeouts[i][1] < 1:
            timeouts[i][0].deactivate()
            timeouts.pop(i)
            break
        else:
            timeouts[i][1] -= 1
            
def checkForRuns(pins, pressure, apogee, accelX, accelY, accelZ):
    for i in range(len(pins)):
        if pins[i].getTrigger() == 2: # altitude going DOWN
            if apogee and pressure < pins[i].getCustom() and not pins[i].isTriggered():
                pins[i].trigger(0)
                timeouts.append([pins[i], pins[i].getFireLength()])
        if pins[i].getTrigger() == 3: # altitude going UP
            if not apogee and pressure > pins[i].getCustom() and not pins[i].isTriggered():
                pins[i].trigger(1)
                timeouts.append([pins[i], pins[i].getFireLength()])


class GPIO:
    _pin = 0
    _trigger = 0
    _custom = 0
    _triggered = False
    _fireLength = 12.5
    _identifier = 0
    _pyro = Pin(_pin, Pin.OUT)
    
    def __init__(self, identifier, pin):
        self._pin = pin
        self._custom = 0
        self._identifier = identifier
        self._pyro = Pin(self._pin, Pin.OUT)
    
    def setTrigger(self, trigger):
        self._trigger = trigger
        
    def setCustom(self, custom):
        self._custom = custom
        
    def getCustom(self):
        return self._custom
        
    def setFireLength(self, fireLength):
        self._fireLength = fireLength
        
    def getTrigger(self):
        # 0 is none
        # 1 is apogee
        # 2 is altitude going DOWN
        # 3 is altutude going UP
        # 4 ___ seconds after apogee
        # 5 at launch detected
        # 6 ___ seconds after launch detected
        # 7 at motor burnout
        # 8 ___ seconds after motor burnout
        # 9 at landing
        # 10 ___ seconds after landing
        return self._trigger
    
    def getFireLength(self):
        # in updates/second
        return self._fireLength
    
    def isTriggered(self):
        return self._triggered
    
    def deactivate(self):
        print("turned off pin " + str(self._pin))
        self._pyro.value(0)
    
    def trigger(self, event_id):
        global event
        if not self.isTriggered():
            print("triggered pin " + str(self._pin))
            event = event_id
            self._pyro.value(1)
            self._triggered = True
            return (self._pyro, self._fireLength)
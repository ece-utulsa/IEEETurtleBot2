from gpiozero import LED, Button
import time

shovel_time = 10.1
arms_time = 1.1
acc_time = 10.1

def init():
    # set pins
    shovel = LED(11)
    acc = LED(23)
    arms = LED(25)
    # homing
    acc.on()
    arms.on()
    shovel.on()

def shovel_down():
    shovel.on()
    time.sleep(shovel_time)
    return True

def shovel_up():
    shovel.off()
    time.sleep(shovel_time)
    return True

def arm_in():
    arms.on()
    time.sleep(arms_time)
    return True
    
def arm_out():
    arms.off()
    time.sleep(arms_time)
    return True

def tilt():
    acc.off()
    time.sleep(acc_time)
    return True

def untilt():
    acc.on()
    time.sleep(acc_time)
    return True

from gpiozero import DigitalOutputDevice
from gpiozero import DigitalInputDevice
from time import sleep

dump_shovel = DigitalOutputDevice(8)
return_shovel = DigitalOutputDevice(23)
arms_in = DigitalOutputDevice(25)
arms_out = DigitalOutputDevice(24)

busy = DigitalInputDevice(6, pull_up = False)

def dump():
    dump_shovel.on()
    if not busy.is_active:
        dump_shovel.off()
        return True
    else:
        return False

def reset_shovel():
    return_shovel.on()
    if not busy.is_active:
        return_shovel.off()
        return True
    else:
        return False

def arm_in():
    arms_in.on()
    if not busy.is_active:
        arms_in.off()
        return True
    else:
        return False
    
def arm_out():
    arms_out.on()
    if not busy.is_active:
        arms_out.off()
        return True
    else:
        return False


# # examples
# dump()
# sleep(2)
# reset_shovel()
# sleep(2)
# arm_in()
# sleep(2)
# arm_out()

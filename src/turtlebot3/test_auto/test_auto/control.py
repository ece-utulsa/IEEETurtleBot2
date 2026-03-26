from gpiozero import DigitalOutputDevice
from gpiozero import DigitalInputDevice
from time import sleep

return_shovel = DigitalOutputDevice(23)
arms_in = DigitalOutputDevice(25)
arms_out = DigitalOutputDevice(24)
dump_shovel = DigitalOutputDevice(6)

#busy = DigitalInputDevice(6, pull_up = False)

def dump():
    dump_shovel.on()
    # if not busy.is_activ:
    #     dump_shovel.off()
    #     return True
    # else:
    #     return False
    sleep(5)
    return True

def reset_shovel():
    return_shovel.on()
    # if not busy.is_active:
    #     return_shovel.off()
    #     return True
    # else:
    #     return False
    sleep(5)
    return True

def arm_in():
    arms_in.on()
    # if not busy.is_active:
    #     arms_in.off()
    #     return True
    # else:
    #     return False
    sleep(1)
    return True
    
def arm_out():
    arms_out.on()
    # if not busy.is_active:
    #     arms_out.off()
    #     return True
    # else:
    #     return False
    sleep(1)
    return True


# # examples
# dump()
# sleep(2)
# reset_shovel()
# sleep(2)
# arm_in()
# sleep(2)
# arm_out()

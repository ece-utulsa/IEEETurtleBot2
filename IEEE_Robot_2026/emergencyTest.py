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

    while True:
        if not busy.is_active:
            dump_shovel.off()
            break
        sleep(0.1)

def reset_shovel():
    return_shovel.on()

    while True:
        if not busy.is_active:
            return_shovel.off()
            break
        sleep(0.1)

def arm_in():
    arms_in.on()

    while True:
        if not busy.is_active:
            arms_in.off()
            break
        sleep(0.1)
def arm_out():
    arms_out.on()

    while True:
        if not busy.is_active:
            arms_out.off()
            break
        sleep(0.1)


# examples
dump()
sleep(2)
reset_shovel()
sleep(2)
arm_in()
sleep(2)
arm_out()

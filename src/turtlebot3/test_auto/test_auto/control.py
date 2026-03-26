from gpiozero import LED, Button
import time

#shovel  = LED(11)
#acc = LED(23)
arms = LED(25)

shovel_time = 10
arms_time = 2
acc_time = 10

def shovel_down():
    shovel.on()
    # if not busy.is_activ:
    #     dump_shovel.off()
    #     return True
    # else:
    #     return False
    time.sleep(shovel_time)
    return True

def shovel_up():
    shovel.off()
    # if not busy.is_active:
    #     return_shovel.off()
    #     return True
    # else:
    #     return False
    time.sleep(shovel_time)
    return True

def arm_in():
    arms.on()
    # if not busy.is_active:
    #     arms_in.off()
    #     return True
    # else:
    #     return False
    time.sleep(arms_time)
    return True
    
def arm_out():
    arms.off()
    # if not busy.is_active:
    #     arms_out.off()
    #     return True
    # else:
    #     return False
    time.sleep(arms_time)
    return True

def acc_in():
    acc.on()
    time.sleep(acc_time)
    return True

def acc_out():
    acc.off()
    time.sleep(acc_time)
    return True


# # examples
# dump()
# sleep(2)
# reset_shovel()
# sleep(2)
# arm_in()
# sleep(2)
# arm_out()

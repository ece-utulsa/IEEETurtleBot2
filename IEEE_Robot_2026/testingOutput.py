from gpiozero import LED, Button
import time

shovel  = LED(11)
acc = LED(23)
arms = LED(25)

shovel.on()
acc.off()
arms.off()
time.sleep(5)

while True:
    arms.off()
    shovel.off()
    arms.on()
    acc.on()
    time.sleep(20)

    acc.off()
    arms.off()
    shovel.on()
    arms.on()
    time.sleep(20)


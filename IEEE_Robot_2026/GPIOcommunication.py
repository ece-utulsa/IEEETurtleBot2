from giozero import LED, Button
import time

# set pins
shovel = LED(11)
acc = LED(23)
arms = LED(25)

# dump bucket
arms.off()
time.sleep(1.1)
shovel.off()
time.sleep(10.1)
arms.on()
time.sleep(1.1)
acc.on()
time.sleep(10.1)

input("continue")
print(f"continuing")

acc.off()
time.sleep(10.1)
arms.off()
time.sleep(1.1)
shovel.on()
time.sleep(10.1)
arms.on()
time.sleep(1.1)

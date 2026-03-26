from gpiozero import LED, Button
import time

shovel  = LED(11)
acc = LED(23)
arms = LED(25)

shovel.on()
arms.off()
acc.on()
time.sleep(5)

while True:
  shovel.on()
#  acc.on()
#  arms.on()
  time.sleep(20)

  shovel.off()
 # acc.off()
#  arms.off()
  time.sleep(20)

from gpiozero import LED, Button
import time


busy_pin = Button(24, pull_up=False)

try:
    while True:
        #state = busy_pin.is_pressed
        value = busy_pin.value
        print(f"GPIO 24 (raw value: {value})", end="\r",flush=True)
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n⏹ Stopped by user")

finally:
    print("✅ GPIO reader stopped cleanly")

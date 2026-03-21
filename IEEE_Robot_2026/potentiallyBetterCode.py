import spidev
import RPi.GPIO as GPIO

# --- SPI setup ---
spi = spidev.SpiDev()
spi.open(0, 0)             # bus 0, CE0
spi.max_speed_hz = 10000
spi.mode = 0

# --- GPIO setup ---
GPIO.setmode(GPIO.BCM)
LED_PIN = 17
GPIO.setup(LED_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

print("Waiting for start signal...")

# Block here until Arduino sends HIGH
GPIO.wait_for_edge(LED_PIN, GPIO.RISING)

print("Signal received! Starting program...")

# --- Your main program starts here ---
# Example:
response = spi.xfer2([0x00])[0]
print("SPI received:", response)

# Continue your logic...

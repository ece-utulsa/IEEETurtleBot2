import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)   # bus 0, CE0
spi.max_speed_hz = 10000
spi.mode = 0

while True:
    data = [0xAA, 0x01, 0x02]
    print("Sending:", data)
    spi.xfer2(data)  # use xfer2 for full-duplex
    time.sleep(1)

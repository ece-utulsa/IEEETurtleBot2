import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)             # bus 0, device 0 (CE0)
spi.max_speed_hz = 100000  # 1 MHz – safe start; can try 2–4 MHz later
spi.mode = 0                # usually MODE 0 for Arduino slave (CPOL=0, CPHA=0)

while True:
    # ENSURE values are 0-255 or it will not work / give unexpected results 
    arms_out =  [0xAA,0x02,0x01]
    arms_in = [0xAA, 0x02, 0x00]
    shovel_up = [0xAA, 0x01, 0x01]
    shovel_down = [0xAA, 0x01, 0x00]

    #send data to arduino!
    spi.writebytes(arms_out)
    print(f"Sent:     {arms_out}")

    time.sleep(2)

    spi.writebytes(arms_in)
    print(f"Sent:    {arms_in}")
    time.sleep(2)

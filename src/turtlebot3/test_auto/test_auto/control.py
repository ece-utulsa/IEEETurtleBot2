import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)             # bus 0, device 0 (CE0)
spi.max_speed_hz = 100000  # 1 MHz – safe start; can try 2–4 MHz later
spi.mode = 0                # usually MODE 0 for Arduino slave (CPOL=0, CPHA=0)

def send_spi_command(byte_list):
    spi.writebytes(byte_list)
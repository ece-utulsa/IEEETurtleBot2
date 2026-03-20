import spidev

for dev in [0, 1]:
    spi = spidev.SpiDev()
    spi.open(0, dev)
    spi.max_speed_hz = 100000
    spi.mode = 0
    resp = spi.xfer2([0xAA, 0x02, 0x01])
    print(f"CE{dev}: {resp}")
    spi.close()

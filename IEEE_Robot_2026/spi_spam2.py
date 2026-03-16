import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)             # bus 0, device 0 (CE0)
spi.max_speed_hz = 100000  # 1 MHz – safe start; can try 2–4 MHz later
spi.mode = 0                # usually MODE 0 for Arduino slave (CPOL=0, CPHA=0)

while True:
    # Example: send 3 bytes (you can make this any length)
    to_send = [0xAA,0x20,0x06]          # ENSURE values are 0-255 or it will not work or could give unexpected results 
    #because there is a chnce it has a mess up I would make the first byte some kind of flag like 0xAA (dont use FF because FF is what it sees if there is comms loss, because the pins are pulled high)  in fact if you see 0xFF that may be a bad sign


    # Full-duplex transfer: send list → receive same number of bytes back
    # you could do error checking with response or just ignore it.  I was getting weird data so write bytes is one way to the arduino
    #response = spi.xfer2(to_send)

    spi.writebytes(to_send)
    

    print(f"Sent:     {to_send}")
    #print(f"Received: {response}")
    
    time.sleep(1)

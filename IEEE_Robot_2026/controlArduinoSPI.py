# SPI Master Control Code

import spidev
import time

# --- SPI Setup ---
SPI_BUS = 0
SPI_DEVICE = 0

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)

spi.max_speed_hz = 1000000   # 1 MHz
spi.mode = 0
spi.bits_per_word = 8


# --- Helper function to send command ---
def send_command(cmd, value, param):
    packet = [0xFF, cmd, value, param]
    response = spi.xfer2(packet)   # Send packet and receive response

    # Arduino should return ACK in last byte
    if response[-1] == 0xAA:
        return True
    else:
        return False


# --- Command functions ---

def move_motor(steps: int, direction: int):
    if direction not in (0, 1):
        raise ValueError("Direction must be 0 (down) or 1 (up)")

    success = send_command(0x01, steps, direction)

    if success:
        print(f"Motor moved {steps} steps {'up' if direction else 'down'}")
    else:
        print("Error moving motor")


def move_motor_full(direction: int):
    if direction not in (0, 1):
        raise ValueError("Direction must be 0 or 1")

    success = send_command(0x02, direction, 0x00)

    if success:
        print("Motor moved full distance")
    else:
        print("Error moving motor")


def turn_servos(direction: int):
    if direction not in (0, 1, 2):
        raise ValueError("Direction must be 0, 1, or 2")

    success = send_command(0x03, direction, 0x00)

    if success:
        print("Servos turned")
    else:
        print("Error turning servos")


def set_relay(on: bool):
    success = send_command(0x04, 1 if on else 0, 0x00)

    if success:
        print(f"Relay {'ON' if on else 'OFF'}")
    else:
        print("Error setting relay")


# --- Example Usage ---

move_motor(250, 1)
time.sleep(2)

move_motor(250, 0)
time.sleep(2)

turn_servos(0)
time.sleep(2)

turn_servos(1)
time.sleep(2)

turn_servos(2)

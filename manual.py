#This is in a strange folder to make it easy to run, just deal w it i guess, good luck knowing where to find it
from test_auto.control import send_spi_command

arms_in = [0xAA, 0x02, 0x00]
arms_out =  [0xAA,0x02,0x01]
shovel_up = [0xAA, 0x01, 0x01]
shovel_down = [0xAA, 0x01, 0x00]
actuators_up = [0xAA, 0x03, 0x00] #makes the robot go down so all three wheels are on the ground
actuators_down = [0xAA, 0x03, 0x01] #makes robot go up tilted

print("arms in: ai, arms out: ao, shovel up: su, shovel down: sd, actuators up: au, actuators down: ad")
while True:
    command = input("Enter command (ai, ao, su, sd, au, ad): ")
    if command == "ai":
        send_spi_command(arms_in)
        print(f"Sent:     {arms_in}")
    elif command == "ao": 
        send_spi_command(arms_out)
        print(f"Sent:     {arms_out}")
    elif command == "su":
        send_spi_command(shovel_up)
        print(f"Sent:     {shovel_up}")
    elif command == "sd":
        send_spi_command(shovel_down)
        print(f"Sent:     {shovel_down}")
    elif command == "au":
        send_spi_command(actuators_up)
        print(f"Sent:     {actuators_up}")
    elif command == "ad":
        send_spi_command(actuators_down)
        print(f"Sent:     {actuators_down}")
    else:
        print("Invalid command. Please try again.")
#This is in a strange folder to make it easy to run, just deal w it i guess, good luck knowing where to find it
from test_auto.control import dump
from test_auto.control import reset_shovel
from test_auto.control import arm_in
from test_auto.control import arm_out


print("arms in: ai, arms out: ao, shovel up: su, shovel down: sd, actuators up: au, actuators down: ad")
while True:
    command = input("Enter command (ai, ao, su, sd, au, ad): ")
    if command == "ai":
        arm_in()
        print(f"Sent: arms in")
    elif command == "ao": 
        arm_out()
        print(f"Sent: arms out")
    elif command == "su":
        dump()
        print(f"Sent: shovel up")
    elif command == "sd":
        reset_shovel()
        print(f"Sent: shovel down")
    elif command == "au":
        # send_spi_command(actuators_up)
        print(f"Sent: actuators up")
    elif command == "ad":
        # send_spi_command(actuators_down)
        print(f"Sent: actuators down")
    else:
        print("Invalid command. Please try again.")
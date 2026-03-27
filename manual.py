#This is in a strange folder to make it easy to run, just deal w it i guess, good luck knowing where to find it
from test_auto.control import shovel_up
from test_auto.control import shovel_down
from test_auto.control import arm_in
from test_auto.control import arm_out
from test_auto.control import tilt
from test_auto.control import untilt
from test_auto.control import init

init()
print("arms in: ai, arms out: ao, shovel up: su, shovel down: sd, tilt: t, untilt: ut")
while True:
    command = input("(v7) Enter (ai, ao, su, sd, t, ut): ")
    if command == "ai":
        arm_in()
        print(f"Sent: arms in")
    elif command == "ao": 
        arm_out()
        print(f"Sent: arms out")
    elif command == "su": 
        shovel_up()
        print(f"Sent: shovel up")
    elif command == "sd":
        shovel_down()
        print(f"Sent: shovel down")
    elif command == "t":
        tilt()
        print(f"Sent: tilt")
    elif command == "ut":
        untilt()
        print(f"Sent: untilt")
    else:
        print("Invalid command. Please try again.")
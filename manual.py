#This is in a strange folder to make it easy to run, just deal w it i guess, good luck knowing where to find it
from test_auto.control import shovel_up
from test_auto.control import shovel_down
from test_auto.control import arm_in
from test_auto.control import arm_out
from test_auto.control import acc_in
from test_auto.control import acc_out


print("arms in: ai, arms out: ao, shovel up: su, shovel down: sd, actuators in: aci, actuators out: aco")
while True:
    command = input("(4) Enter (ai, ao, su, sd, aci, aco): ")
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
    elif command == "aci":
        acc_in()
        print(f"Sent: actuators in")
    elif command == "aco":
        acc_out()
        print(f"Sent: actuators out")
    else:
        print("Invalid command. Please try again.")
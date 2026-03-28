#from https://github.com/ROBOTIS-GIT/turtlebot3/blob/main/turtlebot3_example/turtlebot3_example/turtlebot3_relative_move/turtlebot3_relative_move.py

import math
import os
import sys
import termios

import signal #for sigint

from nav_msgs.msg import Odometry
import numpy
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

ros_distro = os.environ.get('ROS_DISTRO', 'humble').lower()
if ros_distro == 'humble':
    from geometry_msgs.msg import Twist as CmdVelMsg
else:
    from geometry_msgs.msg import TwistStamped as CmdVelMsg

from gpiozero import LED, Button
from gpiozero import Device
from gpiozero.pins.rpigpio import RPiGPIOFactory
import time

class SigintSkipper:
    def __init__(self, callback):
        self.callback = callback
    def __enter__(self):
        self.got = False
        self.handler_old = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self.got = (sig, frame)
        self.callback()

    def __exit__(self, type, value, traceback):
        print('exiting sigint skipper')

class Turtlebot3RelativeMove(Node):

    def __init__(self): #python needs to specify self all over the place so that different objects of the same type are distinct
        super().__init__('turtlebot3_relative_move') #its parent/super() is node

        # set pins
        #Device.pin_factory = RPiGPIOFactory()
        print(Device.pin_factory)
        self.shovel = LED(24)
        print(self.shovel.value)
        self.arms = LED(25)

        self.runOnce = False

        self.update_timer = self.create_timer(0.010, self.test) #call that function every 0.01 seconds, i think it does start automatically, idk why it needs to go into a variable

        self.get_logger().info('TurtleBot3 relative move node has been initialised.') #log a message with INFO severity (into the log file i guess, you can find it somewhere in rviz? go ask the ros tutorial)

    #this sets of previous (current) position based on the odometry data (better hope its correct)
    def test(self): #function called when we get data from odometry subscription
        if not self.runOnce:
            self.arms.off()
            print("arms in")
            time.sleep(1)
            self.shovel.off()
            print("shovel up")
            self.runOnce = True

def main(args=None):
    rclpy.init(args=args) #just write this, idk or care what exactly it does
    node = Turtlebot3RelativeMove() #this calls init from above

    #this code is all from Michael's multicontrol mynode
    def finish_callback():
        node.generate_stop()
        stop_twist = CmdVelMsg()
        node.cmd_vel_pub.publish(stop_twist) #publish an empty cmdVelMsg to stop
        node.destroy_node()
        rclpy.shutdown()

    with SigintSkipper(finish_callback):
        #threading.Thread(target=pyglet.app.run, args=tuple()).start() #I think this is just for controller input and i can ignore it
        rclpy.spin(node)
'''
    try:
        rclpy.spin(node) #this starts callbacks including the timer i think, docs here: https://docs.ros2.org/latest/api/rclpy/api/init_shutdown.html

    except KeyboardInterrupt or SystemExit:
        node.generate_stop()
        stop_twist = CmdVelMsg()
        node.cmd_vel_pub.publish(stop_twist) #publish an empty cmdVelMsg to stop

        node.destroy_node()
        rclpy.shutdown()

    finally: #idk when this is supposed to run, it doesn't interrupt the other code i think??; it doesn't work for me lol
        node.generate_stop()
        stop_twist = CmdVelMsg()
        node.cmd_vel_pub.publish(stop_twist) #publish an empty cmdVelMsg to stop

        node.destroy_node()
        rclpy.shutdown()
'''

if __name__ == '__main__': #this just lives here in python
    main()

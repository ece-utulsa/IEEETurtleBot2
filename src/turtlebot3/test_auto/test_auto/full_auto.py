import math
import os
import sys
import termios
import time

import signal #for sigint

from nav_msgs.msg import Odometry
import numpy
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from geometry_msgs.msg import PoseStamped

import subprocess

from std_msgs.msg import Bool

ros_distro = os.environ.get('ROS_DISTRO', 'humble').lower()
if ros_distro == 'humble':
    from geometry_msgs.msg import Twist as CmdVelMsg
else:
    from geometry_msgs.msg import TwistStamped as CmdVelMsg

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

class Turtlebot3Full(Node):
    def __init__(self):
        super().__init__('turtlebot3_full')

        self.step = 0
        self.runStep = False

        self.odom = Odometry()
        self.last_pose_x = 0.0
        self.last_pose_y = 0.0
        self.last_pose_theta = 0.0 #i feel like we actually start at -1.7 or smth??
        self.goal_pose_x = 0.0
        self.goal_pose_y = 0.0
        self.goal_pose_theta = 0.0

        self.goal_pub = self.create_publisher(
            PoseStamped,
            '/nav2ext/goal_pose',
            10
        )

        self.goal_done_sub = self.create_subscription(
            Bool,
            '/nav2ext/goal_done',
            self.goal_done_callback,
            10
        )

        qos = QoSProfile(depth=10)

        self.update_timer = self.create_timer(0.01, self.update_callback)

        self.get_logger().info('turtlebot3 full initialized')

        p1 = subprocess.Popen(
            ["ros2", "launch", "turtlebot3_bringup", "robot.launch.py"],
            cwd="/home/robotics/pi_ws",
        )
        
        time.sleep(1)
        

        p2 = subprocess.Popen(
            ["ros2", "run", "test_auto", "scan_filter"],
            cwd="/home/robotics/desktop_ws/IEEETurtleBot2",
        )

        time.sleep(1)

        p3 = subprocess.Popen(
            ["ros2", "launch", "turtlebot3_navigation2", "navigation2.launch.py", "map:=/home/robotics/desktop_ws/IEEETurtleBot2/src/turtlebot3/newest_map.yaml"],
            cwd="/home/robotics/desktop_ws/IEEETurtleBot2",
        )

        time.sleep(1)

        p4 = subprocess.Popen(
            ["ros2", "run", "test_auto", "nav2ext"],
            cwd="/home/robotics/desktop_ws/IEEETurtleBot2",
        )

        time.sleep(1)

    def update_callback(self):
        if self.runStep:
            return

        if self.goal_pub.get_subscription_count() <1:
            self.get_logger().info('Waiting for nav2ext subscriber')
            return
        
        if self.step == 0:
            self.send_nav_goal(-0.1262, -0.3970, 0.2108)
        elif self.step == 1:
            self.send_nav_goal(-0.7510, -0.5800, 0.2108)
        elif self.step == 2:
            self.send_nav_goal(0.1200, -0.2700 , -2.9292)
    
    def goal_done_callback(self, msg: Bool) -> None:
        if msg.data:
            self.get_logger().info('Navigation goal completed.')
            self.runStep = False
            self.step += 1

    def yaw_to_quaternation(self, yaw: float) -> tuple[float, float]:
        z = math.sin(yaw / 2.0)
        w = math.cos(yaw / 2.0)
        return z, w
    
    def send_nav_goal(self, x: float, y: float, yaw: float) -> None:
        self.runStep = True
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()

        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = 0.0

        z, w = self.yaw_to_quaternation(yaw)
        msg.pose.orientation.x = 0.0
        msg.pose.orientation.y = 0.0
        msg.pose.orientation.z = z
        msg.pose.orientation.w = w

        self.goal_pub.publish(msg)
        self.get_logger().info(

            f'Published nav goal: x={x}, y={y}, yaw={yaw}'
        )
        


def main(args=None):
    rclpy.init(args=args)
    node = Turtlebot3Full()

    def finish_callback():
        node.destroy_node()
        rclpy.shutdown()

    with SigintSkipper(finish_callback):
        rclpy.spin(node)

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

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

from test_auto.control import send_spi_command

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

        self.have_odom = False
        self.backing_up = False
        self.backup_start_x = 0.0
        self.backup_start_y = 0.0
        self.backup_target = 0.0
        self.backup_speed = 0.08

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

        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        qos = QoSProfile(depth=10)

        self.processes = []

        self.update_timer = self.create_timer(0.01, self.update_callback)

        self.get_logger().info('turtlebot3 full initialized')

        p1 = subprocess.Popen(
            ["ros2", "launch", "turtlebot3_bringup", "robot.launch.py"],
            cwd="/home/robotics/pi_ws",
        )
        self.processes.append(p1)
        
        time.sleep(1)
        

        p2 = subprocess.Popen(
            ["ros2", "run", "test_auto", "scan_filter"],
            cwd="/home/robotics/desktop_ws/",
        )
        self.processes.append(p2)

        time.sleep(1)

        p3 = subprocess.Popen(
            ["ros2", "launch", "turtlebot3_navigation2", "navigation2.launch.py", "map:=/home/robotics/desktop_ws/IEEETurtleBot2/src/turtlebot3/newest_map.yaml"],
            cwd="/home/robotics/desktop_ws/",
        )
        self.processes.append(p3)

        time.sleep(1)

        p4 = subprocess.Popen(
            ["ros2", "run", "test_auto", "nav2ext"],
            cwd="/home/robotics/desktop_ws/",
        )
        self.processes.append(p4)

        time.sleep(1)

        self.arms_in = [0xAA, 0x02, 0x00]
        self.arms_out =  [0xAA,0x02,0x01]
        self.shovel_up = [0xAA, 0x01, 0x01]
        self.shovel_down = [0xAA, 0x01, 0x00]


    def start_backup(self, distance_m: float, speed_mps: float = 0.08) -> None:
        if not self.have_odom:
            self.get_logger().warn('no odom yet, cannot start backup')
            return

        self.backup_start_x = self.last_pose_x
        self.backup_start_y = self.last_pose_y
        self.backup_target = distance_m
        self.backup_speed = abs(speed_mps)
        self.backing_up = True

        self.get_logger().info(f'Starting backup for {distance_m} m')

    def update_backup(self) -> None:
        dx = self.last_pose_x - self.backup_start_x
        dy = self.last_pose_y - self.backup_start_y
        traveled = math.sqrt(dx * dx + dy * dy)

        self.get_logger().info(f'Backed up {traveled:.3f} m')

        if traveled >= self.backup_target:
            self.stop_robot()
            self.get_logger().info('Backup complete.')
            self.backing_up = False
            self.step += 1
            return

        twist = Twist()
        twist.linear.x = -self.backup_speed
        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)

    def stop_robot(self) -> None:
        self.cmd_vel_pub.publish(Twist())

    def odom_callback(self, msg: Odometry) -> None:
        self.last_pose_x = msg.pose.pose.position.x
        self.last_pose_y = msg.pose.pose.position.y

        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w
        self.last_pose_theta = 2.0 * math.atan2(qz, qw)

        self.have_odom = True


    def update_callback(self):
        if self.runStep:
            return

        if self.goal_pub.get_subscription_count() <1:
            self.get_logger().info('Waiting for nav2ext subscriber')
            return

        if self.backing_up:
            self.update_backup()
            return
        
        if self.step == 0:
            self.send_nav_goal(-0.1050, -0.2244, 0.2020)
        elif self.step == 1:
            send_spi_command(self.arms_out)
            self.step += 1
        elif self.step == 2:
            self.start_backup(0.46)
        elif self.step == 3:
            time.sleep(0.5)
            send_spi_command(self.arms_in)
            self.step += 1
        elif self.step == 4:
            self.send_nav_goal(0.0806, -0.1274 , -2.5874)


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
        msg.pose.orientation.y =0.0
        msg.pose.orientation.z = z
        msg.pose.orientation.w = w

        self.goal_pub.publish(msg)
        self.get_logger().info(

            f'Published nav goal: x={x}, y={y}, yaw={yaw}'
        )

    def cleanup_processes(self):
        for p in self.processes:
            if p.poll() is None:
                p.terminate()

        for p in self.processes:
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
        


def main(args=None):
    rclpy.init(args=args)
    node = Turtlebot3Full()

    def finish_callback():
        node.cleanup_processes()
        node.destroy_node()
        rclpy.shutdown()

    with SigintSkipper(finish_callback):
        rclpy.spin(node)

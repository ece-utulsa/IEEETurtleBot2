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
from geometry_msgs.msg import PoseWithCovarianceStamped 
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
        self.ready = False

        self.odom = Odometry()
        self.last_pose_x = 0.0
        self.last_pose_y = 0.0
        self.last_pose_theta = 0.0 
        self.amcl_pose_z = 0.0
        self.amcl_pose_w = 0.0
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

        self.pos_pub = self.create_publisher(
            PoseStamped,
            '/nav2ext/pos_pose',
            10
        )

        self.goal_done_sub = self.create_subscription(
            Bool,
            '/nav2ext/goal_done',
            self.goal_done_callback,
            10
        )

        self.amcl_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl',
            self.amcl_callback,
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

        self.update_timer = self.create_timer(0.05, self.update_callback)

        self.get_logger().info('turtlebot3 full initialized')

        p1 = subprocess.Popen(
            ["ros2", "launch", "turtlebot3_bringup", "robot.launch.py"],
            cwd="/home/robotics/pi_ws",
        )
        self.processes.append(p1)
        
        self.wait_for_topic("/odom")
        

        p2 = subprocess.Popen(
            ["ros2", "run", "test_auto", "scan_filter"],
            cwd="/home/robotics/desktop_ws/",
        )
        self.processes.append(p2)

        self.wait_for_topic("/scan_filtered")
        
        p3 = subprocess.Popen(
            ["ros2", "launch", "turtlebot3_navigation2", "navigation2.launch.py", "map:=/home/robotics/desktop_ws/IEEETurtleBot2/src/turtlebot3/newest_map.yaml"],
            cwd="/home/robotics/desktop_ws/",
        )
        self.processes.append(p3)

        self.wait_for_topic("/amcl_pose")

        p4 = subprocess.Popen(
            ["ros2", "run", "test_auto", "nav2ext"],
            cwd="/home/robotics/desktop_ws/",
        )
        self.processes.append(p4)

        self.wait_for_topic("/nav2ext/goal_pose")

        self.vx = 0

        self.arms_in = [0xAA, 0x02, 0x00]
        self.arms_out =  [0xAA,0x02,0x01]

        self.arm_speed = 1

        self.shovel_up = [0xAA, 0x01, 0x01]
        self.shovel_down = [0xAA, 0x01, 0x00]

        self.shovel_speed = 1

        self.actuators_up = [0xAA, 0x03, 0x00]
        self.actuators_down = [0xAA, 0x03, 0x01]

        self.actuator_speed = 1
        
        self.altSleep(5)

        self.navReady = True

        self.amSleeping = False
        self.didSleep = False

        self.amNavigating = False

        self.auto_arms = True

        self.get_logger().info("finish init")
        

    def wait_for_topic(self, topic_name, timeout_sec=None):
        start = time.time()
        while True:
            topics = [name for name, _ in self.get_topic_names_and_types()]
            if topic_name in topics:
                self.get_logger().info(f'Topic {topic_name} is available')
                return True
            if timeout_sec is not None and (time.time() - start) > timeout_sec:
                return False


    def start_backup(self, distance_m: float, speed_mps: float = 0.08) -> None:
        if not self.have_odom:
            self.get_logger().warn('no odom yet, cannot start backup')
            return

        self.backup_start_x = self.last_pose_x
        self.backup_start_y = self.last_pose_y
        self.backup_target = distance_m
        self.backup_speed = speed_mps
        self.back_curr_speed = 0.005 * (abs(speed_mps) / speed_mps)
        self.backing_up = True

        self.get_logger().info(f'Starting backup for {distance_m} m')

    def update_backup(self) -> None:
        dx = self.last_pose_x - self.backup_start_x
        dy = self.last_pose_y - self.backup_start_y
        traveled = math.sqrt(dx * dx + dy * dy)

       # self.get_logger().info(f'Backed up {traveled:.3f} m')

        if traveled >= abs(self.backup_target):
            self.stop_robot()
            self.get_logger().info('Backup complete.')
            self.backing_up = False
            self.step += 1
            return
        if abs(self.back_curr_speed) < abs(self.backup_speed):
            self.back_curr_speed += .001 * (abs(self.backup_speed) / self.backup_speed)
        
        twist = Twist()
        twist.linear.x = -self.back_curr_speed
        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)

    def stop_robot(self) -> None:
        self.cmd_vel_pub.publish(Twist())

    def odom_callback(self, msg: Odometry) -> None:
        self.last_pose_x = msg.pose.pose.position.x
        self.last_pose_y = msg.pose.pose.position.y
        
        self.vx = msg.twist.twist.linear.x

        self.last_pose_z = msg.pose.pose.orientation.z
        self.last_pose_w = msg.pose.pose.orientation.w
        self.last_pose_theta = 2.0 * math.atan2(self.last_pose_z, self.last_pose_w)

        self.have_odom = True

    def amcl_callback(self, msg: Odometry) -> None:
        self.amcl_pose_w = msg.pose.pose.orientation.w
        self.amcl_pose_z = msg.pose.pose.orientation.z


    def update_callback(self):
        if not self.navReady:
            return

        if self.goal_pub.get_subscription_count() <1:
            self.get_logger().info('Waiting for nav2ext subscriber')
            return

        if self.backing_up:
            self.update_backup()
            return

        if self.auto_arms:
            if self.vx < 0:
                send_spi_command(self.arms_out)
            elif self.vx > 0:
                send_spi_command(self.arms_in)
            

        if self.step == 0:
            send_spi_command(self.shovel_down)
            self.get_logger().info('step 0')
            self.mySleep(1)
        #elif self.step == 1:
        #    self.get_logger().info('step 1')
        #    self.amSleeping = False
        #    self.send_nav_goal(-0.1050, -0.2244, 0.2020)
        elif self.step == 1:
            send_spi_command(self.arms_out)
            self.amSleeping = False
            self.step += 1
        elif self.step == 2:
            self.start_backup(0.57, 0.15)
        elif self.step == 3:
            send_spi_command(self.arms_in)
            self.step += 1
        elif self.step == 4:
            self.mySleep(1)
        elif self.step == 5:
            self.amSleeping = False
            self.step += 1
        elif self.step == 6:
            if not self.amNavigating:
                self.send_nav_goal(-0.2, -0.2, 2.9) #yaw was 2.7 
           # if not self.amSleeping:
           #     self.altSleep(5)
           # if self.didSleep:
           #     send_spi_command(self.arms_out)
        elif self.step == 7:
            self.amSleeping = False
            self.didSleep = False
            if not self.amNavigating:
                self.send_nav_goal(0.0, 0.0, 2.9) #was 0.1, -0.2, 2.7
        elif self.step == 8:
            send_spi_command(self.arms_in)
            self.step += 1
        elif self.step == 9:
            self.start_backup(0.34)
           # if not self.amSleeping:      #probably won't do simultaneously. consider.
           #     self.altSleep(1)
           # if self.didSleep:
           #     send_spi_command(self.arms_out)
        elif self.step == 10:
            self.didSleep = False
            self.amSleeping = False
            self.step += 1
        elif self.step == 11:
            self.mySleep(1)
        elif self.step == 12:
            self.amSleeping = False
            send_spi_command(self.shovel_up)
            self.step += 1
        elif self.step == 13:
            self.mySleep(self.shovel_speed)
        elif self.step == 14:
            self.amSleeping = False
            send_spi_command(self.actuators_down)
            self.step += 1
        elif self.step == 15:
            self.mySleep(self.actuator_speed)
        elif self.step == 16:
            self.amSleeping = False
            send_spi_command(self.actuators_up)
            self.step += 1
        elif self.step == 17:
            self.mySleep(self.actuator_speed)
        elif self.step == 18:
            self.amSleeping = False
            send_spi_command(self.shovel_down)
            self.send_new_pos(0.0146, -0.1217, self.last_pose_z, self.last_pose_w) #we calculated heading to be 2.48
            self.step += 1
        elif self.step == 19:
            self.mySleep(self.shovel_speed)
        elif self.step == 20:
            self.start_backup(0.34, -0.08)
        elif self.step == 21:
            self.amSleeping = False
            if not self.amNavigating:
                #self.controller_server.set_parameters(Parameter('general_goal_checker.xy_goal_tolerance', Parameter.Type.DOUBLE, 0.1)) #TODO maybe should store the prev ones somewhere
                #self.controller_server.set_parameters(Parameter('general_goal_checker.yaw_goal_tolerance', Parameter.Type.DOUBLE, 0.05))
                self.send_nav_goal(-0.05, 0.1, -3.0) #was 0.0, 0.0, -3.0

    def mySleep(self, sleepTime):
        if not self.amSleeping:
            self.get_logger().info('start the sleep')
            self.amSleeping = True
            time.sleep(sleepTime)
            self.step += 1
            self.get_logger().info(f'I am done sleeping. Step is {self.step}')

    def altSleep(self, sleepTime):
        self.amSleeping = True
        time.sleep(sleepTime)
        self.didSleep = True
        

    def goal_done_callback(self, msg: Bool) -> None:
        if msg.data and self.amNavigating:
            self.get_logger().info(f'Navigation goal {self.step} completed.')
            self.amNavigating = False
            self.step += 1

    def yaw_to_quaternation(self, yaw: float) -> tuple[float, float]:
        z = math.sin(yaw / 2.0)
        w = math.cos(yaw / 2.0)
        return z, w
    
    def send_new_pos(self, x: float, y: float, z: float, w: float):
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()

        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = 0.0

        msg.pose.orientation.x = 0.0
        msg.pose.orientation.y = 0.0
        msg.pose.orientation.z = z
        msg.pose.orientation.w = w 

        self.pos_pub.publish(msg)

        self.get_logger().info('publish new pos est')


    def send_nav_goal(self, x: float, y: float, yaw: float) -> None:
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

        self.amNavigating = True

    def send_turn_goal(self, yaw: float) -> None:
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()

        msg.pose.position.x = self.last_pose_x
        msg.pose.position.y = self.last_pose_y
        msg.pose.position.z = 0.0

        z, w = self.yaw_to_quaternation(yaw)
        msg.pose.orientation.x = 0.0
        msg.pose.orientation.y = 0.0
        msg.pose.orientation.z = z
        msg.pose.orientation.w = w

        self.goal_pub.publish(msg)
        self.get_logger().info(

            f'Published turn goal: yaw={yaw}'
        )

        self.amNavigating = True

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

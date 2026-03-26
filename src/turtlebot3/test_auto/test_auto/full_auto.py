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

from gpiozero import LED, Button
from test_auto.control import shovel_up
from test_auto.control import shovel_down
from test_auto.control import arm_in
from test_auto.control import arm_out
from test_auto.control import acc_in
from test_auto.control import acc_out

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
        #self.amcl_pose_z = 0.0
        #self.amcl_pose_w = 0.0
        self.goal_pose_x = 0.0
        self.goal_pose_y = 0.0
        self.goal_pose_theta = 0.0

        self.have_odom = False
        #self.have_amcl = False
        self.backing_up = False
        self.turning = False
        
        self.backup_start_x = 0.0
        self.backup_start_y = 0.0
        self.backup_target = 0.0
        self.backup_speed = 0.08

        '''self.goal_pub = self.create_publisher(
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
        )'''

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

        '''p2 = subprocess.Popen(
            ["ros2", "run", "test_auto", "scan_filter"],
            cwd="/home/robotics/desktop_ws/",
        )
        self.processes.append(p2)

        self.wait_for_topic("/scan_filtered")

        p3 = subprocess.Popen( #TODO would be nice if this only started the nodes we need (commenting out waypoint didn't do anything; i think we only could use amcl)
            ["ros2", "launch", "turtlebot3_navigation2", "navigation2.launch.py", "map:=/home/robotics/desktop_ws/IEEETurtleBot2/src/turtlebot3/newest_map.yaml"],
            cwd="/home/robotics/desktop_ws/",
        )
        self.processes.append(p3)

        self.altSleep(5)

        p4 = subprocess.Popen(
            ["ros2", "run", "test_auto", "nav2ext"],
            cwd="/home/robotics/desktop_ws/",
        )
        self.processes.append(p4)

        self.wait_for_topic("/nav2ext/goal_pose")'''

        self.vx = 0

        self.actuator_speed = 1
        
        self.altSleep(5)

        self.navReady = True
        #self.amclReady = False

        self.amSleeping = False
        self.didSleep = False

        self.amNavigating = False

        self.auto_arms = True

        '''self.amcl_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.amcl_callback,
            10
        )'''

        self.initial_x = self.last_pose_x
        self.initial_y = self.last_pose_y

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
        '''if not self.have_amcl:
            self.get_logger().warn('no amcl yet, cannot start')
            return'''
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
    
    #GUYS THIS IS ABSOLUTE to start position in square NOT RELATIVE LIKE BACKUP IS
    def start_turn(self, distance_rad: float, speed_mps: float = 0.5) -> None:
        if not self.have_odom:
            self.get_logger().warn('no odom yet, cannot start turn')
            return
        
        # if self.turn_start_theta > 6.3:
        #     self.turn_start_theta -= 6.28
        # elif self.turn_start_theta < 0:
        #     self.turn_start_theta += 6.28
        
        self.turn_target = distance_rad
        if self.turn_target > 6.3:
            self.turn_target -= 6.28
        elif self.turn_target < 0:
            self.turn_target += 6.28
        
        self.turn_speed = speed_mps
        self.turn_curr_speed = 0.05 * (abs(speed_mps) / speed_mps)
        self.turning = True

        self.get_logger().info(f'Starting turn for {distance_rad} rad')

    def update_turn(self) -> None:
        curr_theta = self.last_pose_theta 
        if curr_theta > 6.28:
            curr_theta -= 6.28
        elif curr_theta < 0:
            curr_theta += 6.28

        self.get_logger().info(f'turned {curr_theta:.3f} rad')

        if curr_theta >= self.turn_target - 0.1 and curr_theta <= self.turn_target + 0.1:
            self.stop_robot()
            self.get_logger().info('Turn complete.')
            self.turning = False
            self.step += 1
            return
        if abs(self.turn_curr_speed) < abs(self.turn_speed):
            self.turn_curr_speed += .005 * (abs(self.turn_speed) / self.turn_speed)
        
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = self.turn_curr_speed
        self.cmd_vel_pub.publish(twist)
        #self.get_logger().info(f'current speed: {self.turn_curr_speed:.3f} rad/s')

    def stop_robot(self) -> None:
        self.cmd_vel_pub.publish(Twist())

    def odom_callback(self, msg: Odometry) -> None:
        self.last_pose_x = msg.pose.pose.position.x
        self.last_pose_y = msg.pose.pose.position.y
        
        self.vx = msg.twist.twist.linear.x

        self.last_pose_z = msg.pose.pose.orientation.z
        self.last_pose_w = msg.pose.pose.orientation.w
        self.last_pose_theta = 2.0 * math.atan2(self.last_pose_z, self.last_pose_w) #range is -2pi to 2pi, increasing counterclockwise

        self.have_odom = True

    '''def amcl_callback(self, msg: Odometry) -> None:
        if not self.amclReady: #this will only run the first time
            self.turn_start_theta = self.q_to_yaw(msg.pose.pose.orientation.z, msg.pose.pose.orientation.w)
            self.get_logger().info(f'turn start theta from z={msg.pose.pose.orientation.z}, w={msg.pose.pose.orientation.w}')
            self.amclReady = True
        self.have_amcl = True #TODO these two are redundant by this point i think, but used in diff places
        self.amcl_pose_w = msg.pose.pose.orientation.w
        self.amcl_pose_z = msg.pose.pose.orientation.z'''


    def update_callback(self):
        if not self.navReady:
            return

        '''if self.goal_pub.get_subscription_count() <1:
            self.get_logger().info('Waiting for nav2ext subscriber')
            return'''
        
        #if not self.amclReady:
        #    self.get_logger().info('waiting for amcl callback')
        #    return
        
        if self.backing_up:
            self.update_backup()
            return
        
        if self.turning:
            self.update_turn()
            return
        
        # want to make sure arms work before we see if this funny logic if correct/necessary
        # if self.auto_arms:
        #     if self.vx < 0:
        #         send_spi_command(self.arms_out)
        #     elif self.vx > 0:
        #         send_spi_command(self.arms_in)

        if self.step == 0:
            #this does almost nothing rn
            self.get_logger().info(f'step {self.step}')
            self.amSleeping = False
            self.step += 1
        elif self.step == 1:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.15, -0.15) #away from wall
        elif self.step == 2:
            self.get_logger().info(f'step {self.step}')
            arm_out()
            self.start_turn(-1.6, -0.3) #turn away from cave
        elif self.step == 3:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.50, 0.15) #was 0.57 #drive to far end
        elif self.step == 4:
            self.get_logger().info(f'step {self.step}')
            if arm_in():
                self.step += 1
        elif self.step == 5:
            self.get_logger().info(f'step {self.step}')
            #this does nothing rn
            self.step += 1
        elif self.step == 6:
            self.get_logger().info(f'step {self.step}')
            self.amSleeping = False
            arm_out() 
            self.start_turn(2.0, -0.5) #turn toward cave end/center of field
        elif self.step == 7:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.67, 0.15) #drive to middle of field (replacing that old intermediate pose)
        elif self.step == 8:
            self.get_logger().info(f'step {self.step}')
            self.start_turn(0.75, -0.5) #turn to face container
        elif self.step == 9:
            self.get_logger().info(f'step {self.step}')
            self.amSleeping = False
            self.didSleep = False
            self.start_backup(0.34) #this is our old friend to run into the container
            self.step += 1 
        elif self.step == 10:
            self.get_logger().info(f'step {self.step}')
            if arm_in():
                self.step += 1
        elif self.step == 11:
            self.get_logger().info(f'step {self.step}')
            if arm_out():
                self.step += 1
        elif self.step == 12:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.2) #second half of backup, after arms in and out
        elif self.step == 13:
            #this does almost nothing rn
            self.get_logger().info(f'step {self.step}')
            self.didSleep = False
            self.amSleeping = False
            self.step += 1
        elif self.step == 14:
            self.get_logger().info(f'step {self.step}')
            #self.mySleep(1)
            #this does nothing rn
            self.step += 1
        elif self.step == 15:
            self.get_logger().info(f'step {self.step}')
            self.amSleeping = False
            #if shovel_up():
            self.step += 1
        elif self.step == 16:
            self.get_logger().info(f'step {self.step}')
            #if acc_out():
            self.step += 1
        elif self.step == 17:
            self.get_logger().info(f'step {self.step}')
            self.amSleeping = False
            #this does almost nothing rn, should we sleep?
            self.step += 1
        elif self.step == 18:
            self.get_logger().info(f'step {self.step}')
            #if acc_in():
            self.step += 1
        elif self.step == 19:
            self.get_logger().info(f'step {self.step}')
            self.amSleeping = False
            #this does almost nothing rn
            self.step += 1
        elif self.step == 20:
            self.get_logger().info(f'step {self.step}')
            #this does nothing rn
            self.step += 1
        elif self.step == 21:
            self.get_logger().info(f'step {self.step}')
            self.amSleeping = False
            #if shovel_down():
            self.step += 1
            #self.send_new_pos(0.0146, -0.1217, self.last_pose_z, self.last_pose_w) #TODO: better with or without?
        elif self.step == 22:
            self.get_logger().info(f'step {self.step}')
            #this does nothing rn
            self.step += 1
        elif self.step == 23:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.34, -0.08) #TODO i wish this could use amcl, or at least based on the initial_x and initial_y so it forgets all of the slips its done since then?
        elif self.step == 24:
            self.get_logger().info(f'step {self.step}')
            self.amSleeping = False
            self.start_turn(1.75) #turn to face cave
            #if not self.amNavigating:
                #self.controller_server.set_parameters(Parameter('general_goal_checker.xy_goal_tolerance', Parameter.Type.DOUBLE, 0.1)) #TODO maybe should store the prev ones somewhere
                #self.controller_server.set_parameters(Parameter('general_goal_checker.yaw_goal_tolerance', Parameter.Type.DOUBLE, 0.05))
                #self.send_nav_goal(-0.05, 0.1, -3.0) #TODO: better with nav or manual?
        elif self.step == 25:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.75, 0.15) #robot becomes in the cave!
        elif self.step == 26:
            self.get_logger().info(f'step {self.step}')
            if arm_in():
                self.step += 1
        elif self.step == 27:
            self.start_backup(0.75)#run into the wall
        
        elif self.step == 28:
            self.get_logger().info(f'step {self.step}')
            #self.send_new_pos() #TODO: if we want to reset anything
            self.step += 1
        elif self.step == 29:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.35, -0.08)
        elif self.step == 30:
            self.get_logger().info(f'step {self.step}')
            if arm_out():
                self.step += 1
        elif self.step == 31:
            self.get_logger().info(f'step {self.step}')
            self.start_turn(0.45, -0.5)
        elif self.step == 32:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.35)
            #TODO:do i need to close the arms here anywhere?
        elif self.step == 33:
            self.get_logger().info(f'step {self.step}')
            self.start_turn(3.14)
        elif self.step == 34:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.5)
        elif self.step == 35:
            self.get_logger().info(f'step {self.step}')
            self.start_turn(-0.5)
        elif self.step == 36:
            self.get_logger().info(f'step {self.step}')
            self.start_backup(0.25)
        elif self.step == 37:
            self.get_logger().info(f'step {self.step}')
            self.start_turn(-1.7, -0.5)
        

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

    def yaw_to_q(self, yaw: float) -> tuple[float, float]:
        z = math.sin(yaw / 2.0)
        w = math.cos(yaw / 2.0)
        return z, w
    def q_to_yaw(self, z: float, w: float) -> float:
        return 2.0 * math.atan2(z, w)
    
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

        z, w = self.yaw_to_q(yaw)
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

        z, w = self.yaw_to_q(yaw)
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
    
    if node.step > 32:
        finish_callback()

    with SigintSkipper(finish_callback):
        rclpy.spin(node)

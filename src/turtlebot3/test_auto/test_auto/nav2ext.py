import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose

from std_msgs.msg import Bool

from collections import deque

class Nav2Ext(Node):
    def __init__(self):
        super().__init__('nav2_ext')

        self.initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            '/initialpose',
            10
        )

        self.goal_sub = self.create_subscription(
            PoseStamped,
            '/nav2ext/goal_pose',
            self.goal_callback,
            10
        )


        self.goal_done_pub = self.create_publisher(
            Bool,
            '/nav2ext/goal_done',
            10
        )


        self.nav_to_pose_client = ActionClient (
            self,
            NavigateToPose,
            'navigate_to_pose'
        )

        self.goal_queue = deque()
        self.current_goal_handle = None
        self.goal_in_progress = False

        self.get_logger().info('Waiting for navigate_to_pose action server...')
        self.nav_to_pose_client.wait_for_server()
        self.get_logger().info('Connected to navigate_to_pose action server.')

        initial_x = -0.1085
        initial_y = -0.3963
        initial_yaw = 0.2020

        self.publish_initial_pose(initial_x, initial_y, initial_yaw)
        time.sleep(1)
        self.publish_initial_pose(initial_x, initial_y, initial_yaw)
        time.sleep(3)


    def yaw_to_quaternation(self, yaw: float) -> tuple[float, float]:
        z = math.sin(yaw / 2.0)
        w = math.cos(yaw / 2.0)
        return z, w
    
    def publish_initial_pose(self, x: float, y: float, yaw: float) -> None:
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()

        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.position.z = 0.0

        z, w = self.yaw_to_quaternation(yaw)
        msg.pose.pose.orientation.x = 0.0
        msg.pose.pose.orientation.y = 0.0
        msg.pose.pose.orientation.z = z
        msg.pose.pose.orientation.w = w

        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.0685

        self.initial_pose_pub.publish(msg)
        self.get_logger().info(
            f'Published initial pose: x={x}, y={y}, yaw={yaw}'
        )
    
    def goal_callback(self, msg: PoseStamped) -> None:
        self.get_logger().info(
            f'Received goal: x={msg.pose.position.x}, y={msg.pose.position.y}'
        )
        self.goal_queue.append(msg)
        self.try_send_next_goal()

    def try_send_next_goal(self) -> None:
        if self.goal_in_progress:
            self.get_logger().info('Goal already in progress, queued new goal.')
            return
        
        if not self.goal_queue:
            return
        
        pose_msg = self.goal_queue.popleft()
        self.send_goal_pose(pose_msg)

    def send_goal_pose(self, pose_msg: PoseStamped) -> None:
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = pose_msg.header.frame_id or 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose = pose_msg.pose

        self.goal_in_progress = True
        self.get_logger().info(
            f'Sending goal: x={goal.pose.pose.position.x}, '
            f'y={goal.pose.pose.position.y}'
        )

        send_goal_future = self.nav_to_pose_client.send_goal_async(goal)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def send_goal(self, x: float, y: float, yaw: float) -> None:
        pose_msg = PoseStamped()
        pose_msg.header.frame_id = 'map'
        pose_msg.header.stamp = self.get_clock().now().to_msg()

        pose_msg.pose.position.x = x
        pose_msg.pose.position.y = y
        pose_msg.pose.position.z = 0.0

        z, w = self.yaw_to_quaternation(yaw)
        pose_msg.pose.orientation.x = 0.0
        pose_msg.pose.orientation.y = 0.0
        pose_msg.pose.orientation.z = z
        pose_msg.pose.orientation.w = w

        self.goal_queue.append(pose_msg)
        self.try_send_next_goal()

    def goal_response_callback(self, future) -> None:
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().warn('Goal was rejected.')
            self.goal_in_progress = False
            self.try_send_next_goal()
            return

        self.get_logger().info('Goal accepted.')
        self.current_goal_handle = goal_handle

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.goal_result_callback)

    def goal_result_callback(self, future) -> None:
        result = future.result().result
        status = future.result().status

        self.get_logger().info(
            f'Goal finished with status code: {status}'
        )

        done_msg = Bool()
        done_msg.data = True
        self.goal_done_pub.publish(done_msg)

        self.current_goal_handle = None
        self.goal_in_progress = False

        self.try_send_next_goal()

def main(args=None):
    rclpy.init(args=args)
    node = Nav2Ext()

    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ =='__main__':
    main()

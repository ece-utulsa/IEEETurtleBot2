import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose

class Nav2Ext(Node):
    def __init__(self):
        super().__init__('nav2_ext')

        self.initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            '/initialpose',
            10
        )

        self.nav_to_pose_client = ActionClient (
            self,
            NavigateToPose,
            'navigate_to_pose'
        )

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

    def send_goal(self, x: float, y: float, yaw: float) -> None:
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()

        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.position.z = 0.0

        z, w = self.yaw_to_quaternation(yaw)
        goal.pose.pose.orientation.x = 0.0
        goal.pose.pose.orientation.y = 0.0
        goal.pose.pose.orientation.z = z
        goal.pose.pose.orientation.w = w

        self.get_logger().info('Waiting for navigate_to_pose action server...')
        self.nav_to_pose_client.send_goal_async(goal)

def main(args=None):
    rclpy.init(args=args)
    node = Nav2Ext()

    initial_x = 0.0005
    initial_y = -0.0443
    initial_yaw = -0.088

    goal_x = 0.2422
    goal_y = -0.8844
    goal_yaw = -0.935

    node.get_logger().info('Waiting for Nav2/AMC startup...')
    time.sleep(5)

    node.publish_initial_pose(initial_x, initial_y, initial_yaw)
    time.sleep(1)
    node.publish_initial_pose(initial_x, initial_y, initial_yaw)
    time.sleep(3)

    node.send_goal(goal_x, goal_y, goal_yaw)

    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ =='__main__':
    main()

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan

from std_msgs.msg import String


class ScanFilter(Node):

    def __init__(self):
        super().__init__('scan_filter')       

        qos = QoSProfile(depth=10)
        qos.reliability = ReliabilityPolicy.BEST_EFFORT

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos
        )

        self.scan_pub = self.create_publisher(
            LaserScan,
            '/scan_filtered',
            qos
        )

        self.get_logger().info('Scan filter node started')
        

    def scan_callback(self, msg):
        filtered_msg = LaserScan()

        filtered_msg.header = msg.header
        filtered_msg.angle_min = msg.angle_min
        filtered_msg.angle_max = msg.angle_max
        filtered_msg.angle_increment = msg.time_increment
        filtered_msg.scan_time = msg.scan_time
        filtered_msg.range_min = msg.range_min
        filtered_msg.range_max = msg.range_max

        ranges = list(filtered_msg.ranges)
        intensities = list(msg.intensities)

        for i in range (len(ranges)):
            angle = msg.angle_min + i * msg.angle_increment

            if angle > 1.57 or angle < -1.57:
                ranges[i] = float('inf')
                if i < len(intensities):
                    intensities[i] = 0.0
        filtered_msg.ranges = ranges
        filtered_msg.intensities = intensities
        self.scan_pub.publish(filtered_msg)


def main(args=None):
    rclpy.init(args=args)

    scan_filter = ScanFilter()

    rclpy.spin(scan_filter)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    scan_filter.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
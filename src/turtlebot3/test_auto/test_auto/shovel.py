import rclpy
import numpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy

from std_msgs.msg import Bool

class Shovel(Node):
    def __init__(self):
        super().__init__('shovel')
        self.sub = self.create_subscription(
            Bool,
            'shovel_down',
            self.callback,
            10
        )
        self.current_state = None

    def callback(self, msg):
        message = msg.data
        if (self.current_state != message):
            moved = self.move_shovel(message)
            if(moved):
                self.current_state = message
        

    def move_shovel(self, move):
        if (move):
            self.shovel_down()
        else:
            self.shovel_up()

    def shovel_down(self):
        self.shovel.on()
        #time.sleep(shovel_time)
        return True

    def shovel_up(self):
        self.shovel.off()
        #time.sleep(shovel_time)
        return True


def main(args=None):
    rclpy.init(args=args)
    node = Shovel()

    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ =='__main__':
    main()

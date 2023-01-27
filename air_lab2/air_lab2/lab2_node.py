import rclpy
from rclpy.node import Node
import geometry_msgs.msg
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math
import sys

from std_msgs.msg import String


class MinimalPublisher(Node):

    def __init__(self):
        self.start_pos = None
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.declare_parameter('linear', 0.0)
        self.declare_parameter('angular', 0.0)
        self.declare_parameter('distance', 0.0)
        self.linear = float(self.get_parameter('linear').value)
        self.angular = float(self.get_parameter('angular').value)
        self.distance = float(self.get_parameter('distance').value)
        breakpoint()

    def listener_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        z = msg.pose.pose.position.z
        
        if self.start_pos == None:
            self.start_pos = (x,y,z)

        distance = math.sqrt(math.pow(self.start_pos[0]-x, 2) + math.pow(self.start_pos[1]-y, 2) + math.pow(self.start_pos[2]-z, 2))
        print("Distance is",distance)

        if distance >= self.distance:
            rclpy.shutdown()


    def timer_callback(self):
        msg = geometry_msgs.msg.Twist()
        msg.linear.x = self.linear
        msg.angular.z = self.angular
        self.publisher_.publish(msg)
        self.i += 1



def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = MinimalPublisher()

    rclpy.spin(minimal_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    
    main()
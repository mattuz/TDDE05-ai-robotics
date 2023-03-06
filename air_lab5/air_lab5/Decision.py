import sys

import rclpy
from rclpy.node import Node
from air_lab_interfaces.msg import GoalsRequest

# Ugly hack to get a new name for each node
ros_name_counter = 0
def gen_name(name):
    global ros_name_counter
    ros_name_counter += 1
    return name + str(ros_name_counter)


class MinimalClientAsync(Node):

    def __init__(self):
        super().__init__('minimal_client_async')

        self.drive_to_node = Node(gen_name("drive_to_node"))

        self.subscription = self.create_subscription(
            GoalsRequest,
            'goals_request',
            self.listener_callback,
            10)

    def listener_callback(self, msg):
        self.get_logger().info('I heard: "%s"' % msg.data)


def main():
    rclpy.init()

    minimal_client = MinimalClientAsync()

    rclpy.spin(minimal_client)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_client.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

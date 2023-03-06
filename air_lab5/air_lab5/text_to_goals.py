import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from air_lab_interfaces.msg import Goal, GoalsRequest


# Example call is 
# ros2 topic pub --once /text_command std_msgs/msg/String  '{"data":"hallå hallå"}'

class MinimalSubscriber(Node):

    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            String,
            'text_command',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.publisher = self.create_publisher(GoalsRequest, 
                                            'goals_request',
                                            10)

    def listener_callback(self, msg):
        self.get_logger().info('I heard: "%s"' % msg.data)
        words = msg.data.split(" ")
        
        type = words[0]
        object = ""
        destination = ""


        # fixa in en bryt för "and" eller ", " för att hantera flera goals
        if type == "Goto":
            object = words[1]
            destination = words[2]
        elif type == "Bring":
            object = words[1]
        elif type == "Explore!":
            pass

        msg = Goal()
        msg.type = type
        msg.object = object
        msg.destination = destination
        req = GoalsRequest()
        req.goals.append(msg)
        self.publisher.publish(req)
        

def main(args=None):
    rclpy.init(args=args)

    minimal_subscriber = MinimalSubscriber()

    rclpy.spin(minimal_subscriber)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
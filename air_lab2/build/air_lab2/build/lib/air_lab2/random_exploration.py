import rclpy
import math
from rclpy.action import ActionClient
from rclpy.node import Node
import random

from nav2_msgs.action import NavigateToPose

class RandomExploration(Node):

    def __init__(self):
        super().__init__('random_exploration')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
 
    def send_goal(self, x, y, angle):
        self.old_pos = (0,0)
        self.pos_time = 0
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.w = math.cos(angle/2)
        goal_msg.pose.pose.orientation.z = math.sin(angle/2)

        self._action_client.wait_for_server()

        self._send_goal_future = self._action_client.send_goal_async(goal_msg, self.feedback_callback)

        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self._goal_handle = future.result()
        if not self._goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return

        self.get_logger().info('Goal accepted :)')

        self._get_result_future = self._goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        #rclpy.shutdown(context = self.context)
        self.destroy_node()
        print("Shutdown, done")

    def feedback_callback(self, feedback_msg):
        #self.get_logger().info('Received feedback: {0}'.format(feedback_msg.feedback.navigation_time))
        time = feedback_msg.feedback.navigation_time.sec
        x = round(feedback_msg.feedback.current_pose.pose.position.x, 2)
        y = round(feedback_msg.feedback.current_pose.pose.position.y, 2)
        print(time - self.pos_time)
        if (x,y) != self.old_pos:
            self.pos_time = time

        if time - self.pos_time >= 4:
            self._goal_handle.cancel_goal_async()
            self.destroy_node()
            print("Shutdown timeout")

        self.old_pos = (x,y)
        

def main(args=None):
    rclpy.init(args=args)

    while(True):
        print("Starting over")
        x = random.uniform(-5, 5)
        y = random.uniform(-5, 5)
        action_client = RandomExploration()

        action_client.send_goal(x, y, 1.0)

        rclpy.spin(action_client)
        print("Done with rclpy spin")


if __name__ == '__main__':
    main()

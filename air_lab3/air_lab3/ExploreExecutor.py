import threading
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
import rclpy.executors
import math

import TstML
import TstML.Executor

from nav2_msgs.action import NavigateToPose
from nav2_msgs.msg import SpeedLimit

import ament_index_python

# Ugly hack to get a new name for each node
ros_name_counter = 0
def gen_name(name):
    global ros_name_counter
    ros_name_counter += 1
    return name + str(ros_name_counter)

class DriveToExecutor(TstML.Executor.AbstractNodeExecutor):
  def __init__(self, node, context):
    super(TstML.Executor.AbstractNodeExecutor, self).__init__(node,
          context)
    self.finished = True
    self.ros_node = Node(gen_name("driveto_node"))
    self.subscriber_ = self.ros_node.create_subscription(Odometry, '/odom', 10)
    self._action_client = ActionClient(self.ros_node, NavigateToPose, 'navigate_to_pose')
    self.executor = rclpy.executors.MultiThreadedExecutor()
    self.executor.add_node(self.ros_node)
    self.thread = threading.Thread(target=self.executor.spin)
    self.thread.start()

  def finalise(self):
    self.executor.shutdown()

  def start(self):
    radius = 0
    theta = 0
    a = 0
    b = 1

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "radius"):
      radius = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "radius")
      print("radius given", radius)

    self.finished = True
    
    while((a+b*theta) < radius and self.finished):
      x = (a + b * theta) * math.cos(theta)
      y = (a + b * theta) * math.sin(theta)

      theta += math.pi / 4

      goal_msg = NavigateToPose.Goal()
      goal_msg.pose.header.frame_id = "map"
      goal_msg.pose.pose.position.x = float(x)
      goal_msg.pose.pose.position.y = float(y)
      self.finished = False
      print("goal_set")
      #self._action_client.wait_for_server()
      print("past wait")
      self._send_goal_future = self._action_client.send_goal_async(goal_msg, self.feedback_callback)
      print("past send goal_async")
      self._send_goal_future.add_done_callback(self.goal_response_callback)
      print("past send goal_callback")

    return TstML.Executor.ExecutionStatus.Started()

  def feedback_callback(self, feedback_msg):
    print(feedback_msg.feedback)

  def goal_response_callback(self, future):
    self._goal_handle = future.result()
    if not self._goal_handle.accepted:
      self.executionFinished(TstML.Executor.ExecutionStatus.Aborted())
      self.ros_node.get_logger().error('Goal rejected :(')
    else:
      self.ros_node.get_logger().error('Goal accepted :)')

      self._get_result_future = self._goal_handle.get_result_async()
      self._get_result_future.add_done_callback(self.handle_result_callback)

  def handle_result_callback(self, future):
    self.finished = True
    self.executionFinished(TstML.Executor.ExecutionStatus.Finished())

  def pause(self):
    self.ros_node.get_logger().info('Pause is not possible.')
    return TstML.Executor.ExecutionStatus.Running()
  def resume(self):
    return TstML.Executor.ExecutionStatus.Running()
  def stop(self):
    self._goal_handle.cancel_goal()
    return TstML.Executor.ExecutionStatus.Finished()
  def abort(self):
    self._goal_handle.cancel_goal()
    return TstML.Executor.ExecutionStatus.Aborted()

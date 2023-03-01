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
  
    self.ros_node = Node(gen_name("driveto_node"))
    self.publisher_ = self.ros_node.create_publisher(SpeedLimit, '/speed_limit', 10)
    self._action_client = ActionClient(self.ros_node, NavigateToPose, 'navigate_to_pose')
    self.executor = rclpy.executors.MultiThreadedExecutor()
    self.executor.add_node(self.ros_node)
    self.thread = threading.Thread(target=self.executor.spin)
    self.thread.start()

  def finalise(self):
    self.executor.shutdown()

  def start(self):
    x = float(0)
    y = float(0)
    yaw = float(0)

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "p"):
      p = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "p")
      x = p['x']
      y = p['y']
      print("Set some values ", p)

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "heading"):
      yaw = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "heading")

      
    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "maximum-speed"):
      sped = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "maximum-speed")
      msg = SpeedLimit()

      msg.percentage = False
      msg.speed_limit = sped

      self.publisher_.publish(msg)

    goal_msg = NavigateToPose.Goal()
    goal_msg.pose.header.frame_id = "map"
    goal_msg.pose.pose.position.x = float(x)
    goal_msg.pose.pose.position.y = float(y)
    goal_msg.pose.pose.orientation.w = math.cos(yaw/2)
    goal_msg.pose.pose.orientation.z = math.sin(yaw/2)
    print("goal_set")
    #self._action_client.wait_for_server()
    print("past wait")
    self._send_goal_future = self._action_client.send_goal_async(goal_msg, self.feedback_callback)
    print("past send goal_async")
    self._send_goal_future.add_done_callback(self.goal_response_callback)

    print("past send goal_callback")

    return TstML.Executor.ExecutionStatus.Started()

  def feedback_callback(self, feedback_msg):
    pass
    #print(feedback_msg.feedback)

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
    print("Finished!")
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

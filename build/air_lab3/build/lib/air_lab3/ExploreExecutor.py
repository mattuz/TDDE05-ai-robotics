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
from nav_msgs.msg import Odometry

import ament_index_python

# Ugly hack to get a new name for each node
ros_name_counter = 0
def gen_name(name):
    global ros_name_counter
    ros_name_counter += 1
    return name + str(ros_name_counter)

class ExploreExecutor(TstML.Executor.AbstractNodeExecutor):
  def __init__(self, node, context):
    super(TstML.Executor.AbstractNodeExecutor, self).__init__(node,
          context)
    self.running_mission = False
    self.ros_node = Node(gen_name("explore_node"))
    self._action_client = ActionClient(self.ros_node, NavigateToPose, 'navigate_to_pose')
    self.executor = rclpy.executors.MultiThreadedExecutor()
    self.executor.add_node(self.ros_node)
    self.thread = threading.Thread(target=self.executor.spin)
    self.thread.start()
    self.subscriber_ = None
    self.pos_time = 0
    self.old_pos = (0,0)

    self.ax = 0
    self.ay = 0
    self.start_x = 0
    self.start_y = 0
    self.radius = 0
    self.theta = 0
    self.b = 1


  def odom_callback(self, msg):
    self.ax = msg.pose.pose.position.x
    self.ay = msg.pose.pose.position.y
    #math.sqrt(self.start_x**2 + self.start_y**2) + 
    if self.theta*self.b < self.radius + (self.b*math.pi/4) and not self.running_mission:
      if self.theta == 0:
        self.start_x = self.ax
        self.start_y = self.ay
      self.running_mission = True
      print(self.theta*self.b, "<", self.radius)
      x = self.start_x + (self.b * self.theta * math.cos(self.theta))
      y = self.start_y + (self.b * self.theta * math.sin(self.theta))

      self.theta += math.pi / 4

      goal_msg = NavigateToPose.Goal()
      goal_msg.pose.header.frame_id = "map"
      goal_msg.pose.pose.position.x = float(x)
      goal_msg.pose.pose.position.y = float(y)

      self._send_goal_future = self._action_client.send_goal_async(goal_msg, self.feedback_callback)
      self._send_goal_future.add_done_callback(self.goal_response_callback)

    if self.theta*self.b >= self.radius + (self.b*math.pi/4) and not self.running_mission:
      self.executionFinished(TstML.Executor.ExecutionStatus.Finished())

  def finalise(self):
    self.executor.shutdown()

  def start(self):
    self.start_x = 0
    self.start_y = 0
    self.radius = 0
    self.theta = 0
    self.b = 1

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "radius"):
      self.radius = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "radius")
      print("radius given", self.radius)

    self.subscriber_ = self.ros_node.create_subscription(Odometry, '/odom', self.odom_callback, 10)
    return TstML.Executor.ExecutionStatus.Started()

  def feedback_callback(self, feedback_msg):
    time = feedback_msg.feedback.navigation_time.sec
    x = feedback_msg.feedback.current_pose.pose.position.x #round(feedback_msg.feedback.current_pose.pose.position.x, 2)
    y = feedback_msg.feedback.current_pose.pose.position.y #round(feedback_msg.feedback.current_pose.pose.position.y, 1)
    if not self.running_mission or abs(x - self.old_pos[0]) + abs(y - self.old_pos[1]) > 0.005:
        self.pos_time = time

    if self.running_mission and time - self.pos_time >= 4:
        self._goal_handle.cancel_goal_async()
        print("Shutdown timeout")
        self.running_mission = False
        self.pos_time = time
    self.old_pos = (x,y)

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
    self.running_mission = False
    #self.executionFinished(TstML.Executor.ExecutionStatus.Finished())

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

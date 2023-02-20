import threading
import rclpy
from rclpy.node import Node
import rclpy.executors

from air_simple_sim_msgs.msg import SemanticObservation

import TstML
import TstML.Executor

import ament_index_python

class RecordSemantic(TstML.Executor.AbstractNodeExecutor):
  def __init__(self, node, context):
    super(TstML.Executor.AbstractNodeExecutor, self).__init__(node,
          context)

    self.graphname = None
    self.topic = None
    self.ros_node = Node(gen_name("record_semantic_node"))
    self.executor = rclpy.executors.MultiThreadedExecutor()
    self.executor.add_node(self.ros_node)
    self.thread = threading.Thread(target=self.executor.spin)
    self.thread.start()

  def finalise(self):
    self.executor.shutdown()

  def start(self):

    self.subscriber_ = self.ros_node.create_subscription(SemanticObservation, '/semantic_sensor', self.semantic_callback, 10)

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "topic"):
        self.topic = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "topic") #used to create the subscriber

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "graphname"):
        self.graphname = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "graphname") #used for the query, look at example in lab-pm

    self._send_goal_future.add_done_callback(self.goal_response_callback)
    return TstML.Executor.ExecutionStatus.Started()

  def semantic_callback(self, msg):
    someid = "" # is in the msg
    someklass = "" # is in the msg

    x = 0 # msg.pose.pose.position.x
    y = 0 # msg.pose.pose.position.y

    sql_msg = str("PREFIX gis: <http://www.ida.liu.se/~TDDE05/gis>\n PREFIX properties: <http://www.ida.liu.se/~TDDE05/properties>\n SELECT ?x ?y WHERE" +
            "{"+ f"<{someid}> a <{someklass}> ; properties:location [ gis:x ?x; gis:y ?y ] . "+"}")
    
    # TODO call sql here 

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

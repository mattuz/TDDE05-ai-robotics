import threading
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
import rclpy.executors
import json
import TstML
import TstML.Executor
from ros2_kdb_msgs.srv import QueryDatabase

from irobot_create_msgs.action import Undock

import ament_index_python

# Ugly hack to get a new name for each node
ros_name_counter = 0
def gen_name(name):
    global ros_name_counter
    ros_name_counter += 1
    return name + str(ros_name_counter)

class Decision(TstML.Executor.AbstractNodeExecutor):
  def __init__(self, node, context):
    super(TstML.Executor.AbstractNodeExecutor, self).__init__(node,
          context)

    self.ros_node = Node(gen_name("decision_node"))
    self.executor = rclpy.executors.MultiThreadedExecutor()
    self.executor.add_node(self.ros_node)
    self.thread = threading.Thread(target=self.executor.spin)
    self.thread.start()

    self.query_node = Node(gen_name('query_node'))
    self.query_client = self.query_node.create_client(QueryDatabase, '/kdb_server/sparql_query')
    self.executor.add_node(self.query_node)

  def finalise(self):
    self.executor.shutdown()

  def start(self):

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "type"):
            type = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "type")
            
    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "object"):
            object = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "object")

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "destination"):
            destination = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "destination")

    query_req = QueryDatabase.Request()
    query_req.graphname = 'semanticobject'
    query_req.format = 'json'
    sql_msg = "PREFIX gis: <http://www.ida.liu.se/~TDDE05/gis> PREFIX properties: <http://www.ida.liu.se/~TDDE05/properties> SELECT ?obj_id ?class ?x ?y WHERE { ?obj_id a ?class ; properties:location [ gis:x ?x; gis:y ?y ] .}"
    query_req.query = sql_msg
    future = self.query_client.call_async(query_req)
    self.executor.spin_until_future_complete(future)

    data = json.loads(future.result().result)
    breakpoint()
    for row in data['results']['bindings']:
        if row['class']['value'] == 'human':
          pass

    return TstML.Executor.ExecutionStatus.Started()

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

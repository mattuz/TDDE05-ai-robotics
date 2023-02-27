import threading
import rclpy
from rclpy.node import Node
import rclpy.executors

import json

from air_simple_sim_msgs.msg import SemanticObservation

from ros2_kdb_msgs.srv import QueryDatabase, InsertTriples

from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
import tf2_geometry_msgs


import TstML
import TstML.Executor

import ament_index_python
from nav_msgs.msg import Odometry

# Ugly hack to get a new name for each node
ros_name_counter = 0
def gen_name(name):
    global ros_name_counter
    ros_name_counter += 1
    return name + str(ros_name_counter)

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

    self.tf_buffer = Buffer()
    self.tf_listener = TransformListener(self.tf_buffer, self.ros_node)

    self.query_node = Node(gen_name('query_node'))
    self.request_node = Node(gen_name('request_node'))

    self.query_client = self.query_node.create_client(QueryDatabase, '/kdb_server/sparql_query')
    self.request_client = self.request_node.create_client(InsertTriples, '/kdb_server/insert_triples')
    self.executor.add_node(self.query_node)
    self.executor.add_node(self.request_node)



  def finalise(self):
    self.executor.shutdown()

  def start(self):

    self.subscriber_sem = self.ros_node.create_subscription(SemanticObservation, '/semantic_sensor', self.semantic_callback, 10)

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "topic"):
        self.topic = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "topic") #used to create the subscriber

    if self.node().hasParameter(TstML.TSTNode.ParameterType.Specific, "graphname"):
        self.graphname = self.node().getParameter(TstML.TSTNode.ParameterType.Specific, "graphname") #used for the query, look at example in lab-pm
        print("graphname is",self.graphname)

    return TstML.Executor.ExecutionStatus.Started()


  def semantic_callback(self, msg):
    someid = msg.uuid # is in the msg
    someklass = msg.klass # is in the msg

    # The tf_buffer and tf_listener needs to be kept alive and should be created in a constructor

    # To use them for point transformation
    point_transformed = self.tf_buffer.transform(msg.point, "map", timeout=rclpy.duration.Duration(seconds=1.0))

    x = point_transformed.point.x
    y = point_transformed.point.y

    sql_msg = str("PREFIX gis: <http://www.ida.liu.se/~TDDE05/gis>\n PREFIX properties: <http://www.ida.liu.se/~TDDE05/properties>\n SELECT ?x ?y WHERE" +
            "{"+ f"<{someid}> a <{someklass}> ; properties:location [ gis:x ?x; gis:y ?y ] . "+"}")
    
    query_req = QueryDatabase.Request()
    query_req.graphname = self.graphname
    query_req.format = 'json'
    query_req.query = sql_msg
    self.future = self.query_client.call_async(query_req)
    self.executor.spin_until_future_complete(self.future)

    data = json.loads(self.future.result().result)

    for row in data["results"]["bindings"]:
      print(someid, someklass, row['x']['value'], row['y']['value'])

    if not len(data["results"]["bindings"]):
      insert_req = InsertTriples.Request()
      insert_req.graphname = self.graphname
      insert_req.format = 'ttl'
      insert_req.content = str("@prefix gis: <http://www.ida.liu.se/~TDDE05/gis>\n @prefix properties: <http://www.ida.liu.se/~TDDE05/properties>\n" +
      "<"+f"{someid}"+"> a <"+f"{someklass}"+">;" +
            f"properties:location [ gis:x {x}; gis:y {y} ] .")

      self.future = self.request_client.call_async(insert_req)
      self.executor.spin_until_future_complete(self.future)
      print("Data added")

    else:
      print("Data retrieved")

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

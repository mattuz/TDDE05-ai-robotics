import threading
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
import rclpy.executors
import math
import json

import TstML
import TstML.Executor

from ros2_kdb_msgs.srv import QueryDatabase
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

class GenerateHumans(TstML.Executor.AbstractNodeExecutor):
  def __init__(self, node, context):
    super(TstML.Executor.AbstractNodeExecutor, self).__init__(node,
          context)

    self.query_node = Node(gen_name('query_node'))
    self.query_client = self.query_node.create_client(QueryDatabase, '/kdb_server/sparql_query')
    
    self.ros_node = Node(gen_name("human_node"))
    self._action_client = ActionClient(self.ros_node, NavigateToPose, 'navigate_to_pose')
    self.executor = rclpy.executors.MultiThreadedExecutor()
    self.executor.add_node(self.ros_node)
    self.executor.add_node(self.query_node)
    self.thread = threading.Thread(target=self.executor.spin)
    self.thread.start()


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

  def finalise(self):
    self.executor.shutdown()

  def start(self):

    sql_msg = "PREFIX gis: <http://www.ida.liu.se/~TDDE05/gis> PREFIX properties: <http://www.ida.liu.se/~TDDE05/properties> SELECT ?obj_id ?class ?x ?y WHERE { ?obj_id a ?class ; properties:location [ gis:x ?x; gis:y ?y ] .}"
    query_req = QueryDatabase.Request()
    query_req.graphname = 'semanticobject'
    query_req.format = 'json'
    query_req.query = sql_msg
    future = self.query_client.call_async(query_req)
    self.executor.spin_until_future_complete(future)

    data = json.loads(future.result().result)
    unvisited_humans = []
    for row in data['results']['bindings']:
        if row['class']['value'] == 'human':
            unvisited_humans.append((float(row['x']['value']), float(row['y']['value'])))

    
    data_ = {"children": [],"common_params": {},"name": "seq","params": {}}
    for human in unvisited_humans:
      x = human[0]
      y = human[1]
      child = {"children": [],"common_params": {},"name": "drive-to","params": {"p": {"rostype": "Point","x": x,"y": y,"z": 0}}}
      data_['children'].append(child)
    json_data = json.dumps(data_)
    with open("air_lab3/drive-to-humans.json", "w") as outfile:
      outfile.write(json_data)

    self.executionFinished(TstML.Executor.ExecutionStatus.Finished())
    self.finalise()
    return TstML.Executor.ExecutionStatus.Started()

  def feedback_callback(self, feedback_msg):
    pass


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

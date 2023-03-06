import sys
import rclpy.executors
import threading
import json

import rclpy
from rclpy.node import Node
from air_lab_interfaces.msg import GoalsRequest
from ros2_kdb_msgs.srv import QueryDatabase

# Ugly hack to get a new name for each node
ros_name_counter = 0
def gen_name(name):
    global ros_name_counter
    ros_name_counter += 1
    return name + str(ros_name_counter)


class MinimalClientAsync(Node):

    def __init__(self):
        super().__init__('minimal_client_async')

        self.subscription = self.create_subscription(
            GoalsRequest,
            'goals_request',
            self.listener_callback,
            10)
        
        self.executor = rclpy.executors.MultiThreadedExecutor()

        
        self.query_node = Node(gen_name('query_node'))
        self.query_client = self.query_node.create_client(QueryDatabase, '/kdb_server/sparql_query')
        self.executor.add_node(self.query_node)

        self.thread = threading.Thread(target=self.executor.spin)
        self.thread.start()

    def listener_callback(self, msg):
        self.get_logger().info('I heard: "%s"' % msg)

        find_this = ""
        single_command = msg[0]
        if single_command.type == "Goto":
            find_this = single_command.destination
        elif single_command.type == "Bring":
            find_this = single_command.object
        elif single_command.type == "Explore!":
            pass

        sql_msg = "PREFIX gis: <http://www.ida.liu.se/~TDDE05/gis> PREFIX properties: <http://www.ida.liu.se/~TDDE05/properties> SELECT ?obj_id ?class ?x ?y WHERE { ?obj_id a ?class ; properties:location [ gis:x ?x; gis:y ?y ] .}"
        query_req = QueryDatabase.Request()
        query_req.graphname = 'semanticobject'
        query_req.format = 'json'
        query_req.query = sql_msg
        future = self.query_client.call_async(query_req)
        self.executor.spin_until_future_complete(future)

        data = json.loads(future.result().result)

        for row in data['results']['bindings']:
            breakpoint()



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

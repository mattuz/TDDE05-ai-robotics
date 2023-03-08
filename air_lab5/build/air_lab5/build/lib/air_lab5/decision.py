import os
import rclpy.executors
import threading
import json

import rclpy
from rclpy.node import Node
from air_lab_interfaces.msg import GoalsRequest
from air_lab_interfaces.srv import ExecuteTst
from ros2_kdb_msgs.srv import QueryDatabase

# Ugly hack to get a new name for each node
ros_name_counter = 0
def gen_name(name):
    global ros_name_counter
    ros_name_counter += 1
    return name + str(ros_name_counter)

file_counter = 0

class MinimalClientAsync(Node):

    def __init__(self):
        super().__init__('minimal_client_async')

        self.subscription = self.create_subscription(
            GoalsRequest,
            'goals_request',
            self.listener_callback,
            10)
        
        self.executor_ = rclpy.executors.MultiThreadedExecutor()
        self.query_node = Node(gen_name('query_node'))
        self.query_client = self.query_node.create_client(QueryDatabase, '/kdb_server/sparql_query')
        self.executor_.add_node(self.query_node)

        self.drive_node = Node(gen_name('tst_node'))
        self.drive_client = self.drive_node.create_client(ExecuteTst, '/execute_tst')
        self.executor_.add_node(self.drive_node)

        self.thread = threading.Thread(target=self.executor_.spin)
        self.thread.start()
        print("Finish init")

    def listener_callback(self, msg):
        self.get_logger().info('I heard: "%s"' % msg)

        find_this = ""
        single_command = msg.goals[0]
        if single_command.type == "Goto":
            find_this = single_command.destination
        elif single_command.type == "Bring":
            find_this = single_command.object
        elif single_command.type == "Explore!":
            pass

        sql_msg = "PREFIX gis: <http://www.ida.liu.se/~TDDE05/gis> PREFIX properties: <http://www.ida.liu.se/~TDDE05/properties> SELECT ?obj_id ?class ?x ?y ?tags WHERE { ?obj_id a ?class ; properties:location [ gis:x ?x; gis:y ?y ] ; properties:tags ?tags . }" 
        query_req = QueryDatabase.Request()
        query_req.graphname = 'semanticobject'
        query_req.format = 'json'
        query_req.query = sql_msg
        future = self.query_client.call_async(query_req)
        self.executor_.spin_until_future_complete(future)

        data = json.loads(future.result().result)

        x = False
        y = False

        for row in data['results']['bindings']:
            if row['tags']['value'] == find_this:
                x = row['x']['value']
                y = row['y']['value']
                break
        
        if x and y:
            data_ = {"children": [],"common_params": {},"name": "seq","params": {}}
            child = {"children": [],"common_params": {},"name": "drive-to","params": {"p": {"rostype": "Point","x": x,"y": y,"z": 0}}}
            data_['children'].append(child)
            json_data = json.dumps(data_)
            global file_counter
            path = os.path.join(os.getcwd(), f"goals/drive-to-{file_counter}.json")
            with open(f"goals/drive-to-{file_counter}.json", "w") as outfile:
                outfile.write(json_data)
            file_counter += 1

            tst_req = ExecuteTst.Request()
            print("req created")
            breakpoint()
            tst_req.tst_file = path
            print("req tst_file")
            breakpoint()
            future = self.drive_client.call_async(tst_req)
            print("future assigned")
            breakpoint()
            self.executor_.spin_until_future_complete(future)
            print("spin finish")
            breakpoint()
            data = json.loads(future.result().result)
            print("data loaded")
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

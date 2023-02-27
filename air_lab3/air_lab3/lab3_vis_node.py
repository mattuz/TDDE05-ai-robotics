import rclpy
import rclpy.node
import visualization_msgs.msg
import geometry_msgs.msg
import std_msgs.msg
from ros2_kdb_msgs.srv import QueryDatabase
from rclpy.node import Node
import rclpy.executors
import threading
import json

# Ugly hack to get a new name for each node
ros_name_counter = 0
def gen_name(name):
    global ros_name_counter
    ros_name_counter += 1
    return name + str(ros_name_counter)

def create_point(x, y, z):
    msg = geometry_msgs.msg.Point()
    msg.x = x
    msg.y = y
    msg.z = z
    return msg

def create_color(r, g, b, a):
    msg = std_msgs.msg.ColorRGBA()
    msg.r = r
    msg.g = g
    msg.b = b
    msg.a = a
    return msg

def timer_callback():

    query_node = Node(gen_name('query_node'))
    query_client = query_node.create_client(QueryDatabase, '/kdb_server/sparql_query')
    executor = rclpy.executors.MultiThreadedExecutor()

    executor.add_node(query_node)
    thread = threading.Thread(target=executor.spin)
    thread.start()

    marker = visualization_msgs.msg.Marker()
    marker.id     = 1242 # identifier the marker, should be unique
    marker.header.frame_id = "odom"
    marker.type   = visualization_msgs.msg.Marker.CUBE_LIST
    marker.action = 0
    marker.scale.x = 0.5
    marker.scale.y = 0.5
    marker.scale.z = 0.5
    marker.pose.orientation.w = 1.0
    marker.color.a = 1.0

    #marker.points.append(create_point(2.0, 3.0, 0.0))
    #marker.points.append(create_point(5.0, 2.0, 0.0))

    #marker.colors.append(create_color(1.0, 0.5, 0.5, 1.0))
    #marker.colors.append(create_color(0.5, 1.0, 0.5, 1.0))

    sql_msg = "PREFIX gis: <http://www.ida.liu.se/~TDDE05/gis> PREFIX properties: <http://www.ida.liu.se/~TDDE05/properties> SELECT ?obj_id ?class ?x ?y WHERE { ?obj_id a ?class ; properties:location [ gis:x ?x; gis:y ?y ] .}"

    query_req = QueryDatabase.Request()
    query_req.graphname = 'semanticobject'
    query_req.format = 'json'
    query_req.query = sql_msg
    future = query_client.call_async(query_req)
    executor.spin_until_future_complete(future)

    data = json.loads(future.result().result)

    for row in data['results']['bindings']:
        if row['class']['value'] == 'human':
            marker.points.append(create_point(float(row['x']['value']), float(row['y']['value']), 0.0))
            marker.colors.append(create_color(1.0, 0.5, 0.5, 1.0))
        elif row['class']['value'] == 'table':
            marker.points.append(create_point(float(row['x']['value']), float(row['y']['value']), 0.0))
            marker.colors.append(create_color(0.5, 1.0, 0.5, 1.0))
    
    marker_array = visualization_msgs.msg.MarkerArray()
    marker_array.markers = [marker]

    display_marker_pub.publish(marker_array)

    """
    marker.points.append(create_point(2.0, 3.0, 0.0))
    marker.points.append(create_point(5.0, 2.0, 0.0))

    marker.colors.append(create_color(1.0, 0.5, 0.5, 1.0))
    marker.colors.append(create_color(0.5, 1.0, 0.5, 1.0))

    marker_array = visualization_msgs.msg.MarkerArray()
    marker_array.markers = [marker]

    display_marker_pub.publish(marker_array)
    """

def main():
    global display_marker_pub
    rclpy.init()
    node = rclpy.node.Node('visualise_semantic_objects')

    display_marker_pub = node.create_publisher(visualization_msgs.msg.MarkerArray, 'semantic_sensor_visualisation', 10)
    timer = node.create_timer(0.5, timer_callback)

    rclpy.spin(node)

if __name__ == '__main__':
    main()

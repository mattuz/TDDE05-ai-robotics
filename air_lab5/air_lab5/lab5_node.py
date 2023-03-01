from air_lab_interfaces.msg import Goal
import std_srvs.srv

import rclpy
from rclpy.node import Node
import TstML
import ament_index_python
import TstML.Executor
from rclpy.callback_groups import ReentrantCallbackGroup
from ros2_kdb_msgs.srv import QueryDatabase

import json

std_srvs.srv.Empty

class MinimalService(Node):

    def __init__(self):
        super().__init__('minimal_service')
        self.srv = self.create_service(ExecuteTst, 'execute_tst', self.execute_tst_callback)

        self.group = ReentrantCallbackGroup()
        self.tst_registry = TstML.TSTNodeModelsRegistry()
        self.tst_registry.loadDirectory(ament_index_python.get_package_prefix("air_tst") +  "/share/air_tst/configs")

        # Create a registry with node executors
        self.tst_executor_registry = TstML.Executor.NodeExecutorRegistry()

        self.query_node = Node(gen_name('query_node'))
        self.query_client = self.query_node.create_client(QueryDatabase, '/kdb_server/sparql_query')
        self.executor.add_node(self.query_node)

    

    def execute_tst_callback(self, request, response):
        filename = request.tst_file
        tst_node = TstML.TSTNode.load(filename, self.tst_registry)

        # Create an executor using the executors defined
        # in tst_executor_registry
        self.tst_executor = TstML.Executor.Executor(tst_node,
            self.tst_executor_registry)

        # Start execution
        self.tst_executor.start()

        # Block until the execution has finished
        status = self.tst_executor.waitForFinished()

        # Display the result of execution
        if status.type() == TstML.Executor.ExecutionStatus.Type.Finished:
            response.success = True
        elif status.type() == TstML.Executor.ExecutionStatus.Type.Failed:
            response.success = False
            response.error_message = "Execution failed: {}".format(status.message())
        else:
            response.success = False

        return response


def main():
    rclpy.init()

    minimal_service = MinimalService()

    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(minimal_service)
    executor.spin()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
from air_lab_interfaces.msg import Goal
from air_lab_interfaces.srv import ExecuteTst
import std_srvs.srv

import rclpy
from rclpy.node import Node
import TstML
import ament_index_python
import TstML.Executor

from .Decision import Decision
import json

std_srvs.srv.Empty

# Ugly hack to get a new name for each node
ros_name_counter = 0
def gen_name(name):
    global ros_name_counter
    ros_name_counter += 1
    return name + str(ros_name_counter)

class MinimalService(Node):

    def __init__(self):
        super().__init__('minimal_service')
        self.srv = self.create_service(ExecuteTst, 'execute_tst', self.execute_tst_callback)

        self.tst_registry = TstML.TSTNodeModelsRegistry()
        self.tst_registry.loadDirectory(ament_index_python.get_package_prefix("air_tst") +  "/share/air_tst/configs")

        # Create a registry with node executors
        self.tst_executor_registry = TstML.Executor.NodeExecutorRegistry()

        self.tst_executor_registry.registerNodeExecutor(
            self.tst_registry.model("decision"),
            Decision)

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
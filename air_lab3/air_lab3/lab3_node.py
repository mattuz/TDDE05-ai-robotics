from air_lab_interfaces.srv import ExecuteTst

import rclpy
from rclpy.node import Node
import TstML
import ament_index_python
import TstML.Executor


class MinimalService(Node):

    def __init__(self):
        super().__init__('minimal_service')
        print("Hi Heloo")
        self.srv = self.create_service(ExecuteTst, 'execute_tst', self.execute_tst_callback)
        tst_registry = TstML.TSTNodeModelsRegistry()
        tst_registry.loadDirectory(ament_index_python.get_package_prefix("air_tst") +  "/share/air_tst/configs")
        


    def execute_tst_callback(self, request, response):
        filename = request.tst_file
        tst_node = TstML.TSTNode.load(filename, tst_registry)
        # Create a registry with node executors
        tst_executor_registry = TstML.Executor.NodeExecutorRegistry()

        # Setup the executors for sequence and concurrent
        tst_executor_registry.registerNodeExecutor(
            tst_registry.model("seq"),
            TstML.Executor.DefaultNodeExecutor.Sequence)
        tst_executor_registry.registerNodeExecutor(
            tst_registry.model("conc"),
            TstML.Executor.DefaultNodeExecutor.Concurrent)

            # Create an executor using the executors defined
        # in tst_executor_registry
        tst_executor = TstML.Executor.Executor(tst_node,
            tst_executor_registry)

        # Start execution
        tst_executor.start()

        # Block until the execution has finished
        status = tst_executor.waitForFinished()

        # Display the result of execution
        if status.type() == TstML.Executor.ExecutionStatus.Type.Finished:
            response.success = True
        elif status.type() == TstML.Executor.ExecutionStatus.Type.Failed:
            response.success = False
            response.error_message = "Execution failed: {}".format(status.message())
        else:
            response.success = False


        print("Hello Hi")
        return response


def main():
    print("Hi from mainfrmae")
    rclpy.init()

    minimal_service = MinimalService()

    rclpy.spin(minimal_service)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
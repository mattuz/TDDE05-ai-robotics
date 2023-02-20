from air_lab_interfaces.srv import ExecuteTst
import std_srvs.srv

from .UndockExecutor import UndockExecutor
from .DockExecutor import DockExecutor
from .DriveToExecutor import DriveToExecutor
from .ExploreExecutor import ExploreExecutor
from .RecordSemantic import RecordSemantic
import rclpy
from rclpy.node import Node
import TstML
import ament_index_python
import TstML.Executor
from rclpy.callback_groups import ReentrantCallbackGroup

std_srvs.srv.Empty

class MinimalService(Node):

    def __init__(self):
        super().__init__('minimal_service')
        self.srv = self.create_service(ExecuteTst, 'execute_tst', self.execute_tst_callback)

        self.group = ReentrantCallbackGroup()
        service = self.create_service(std_srvs.srv.Empty, 'abort', self.callback_abort, callback_group=self.group)
        service = self.create_service(std_srvs.srv.Empty, 'stop', self.callback_stop, callback_group=self.group)
        service = self.create_service(std_srvs.srv.Empty, 'pause', self.callback_pause, callback_group=self.group)
        service = self.create_service(std_srvs.srv.Empty, 'resume', self.callback_resume, callback_group=self.group)
        self.tst_registry = TstML.TSTNodeModelsRegistry()
        self.tst_registry.loadDirectory(ament_index_python.get_package_prefix("air_tst") +  "/share/air_tst/configs")

        # Create a registry with node executors
        self.tst_executor_registry = TstML.Executor.NodeExecutorRegistry()

        # Setup the executors for sequence and concurrent
        self.tst_executor_registry.registerNodeExecutor(
            self.tst_registry.model("seq"),
            TstML.Executor.DefaultNodeExecutor.Sequence)
        self.tst_executor_registry.registerNodeExecutor(
            self.tst_registry.model("conc"),
            TstML.Executor.DefaultNodeExecutor.Concurrent)
        self.tst_executor_registry.registerNodeExecutor(
            self.tst_registry.model("undock"),
            UndockExecutor)
        self.tst_executor_registry.registerNodeExecutor(
            self.tst_registry.model("dock"),
            DockExecutor)
        self.tst_executor_registry.registerNodeExecutor(
            self.tst_registry.model("drive-to"),
            DriveToExecutor)
        self.tst_executor_registry.registerNodeExecutor(
            self.tst_registry.model("explore"),
            ExploreExecutor)
        self.tst_executor_registry.registerNodeExecutor(
            self.tst_registry.model("record-semantic"),
            RecordSemantic)
    

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

    def callback_abort(self, request, response):
        print(self.tst_executor.abort())
        return response

    def callback_stop(self, request, response):
        print(self.tst_executor.stop())
        return response

    def callback_pause(self, request, response):
        print(self.tst_executor.pause())
        return response

    def callback_resume(self, request, response):
        print(self.tst_executor.resume())
        return response


def main():
    rclpy.init()

    minimal_service = MinimalService()

    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(minimal_service)
    executor.spin()




    #rclpy.spin(minimal_service)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
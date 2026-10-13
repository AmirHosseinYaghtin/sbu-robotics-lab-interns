import sys

import rclpy
from rclpy.node import Node
from robot_task_interfaces.srv import GetRobotStatus


class TaskMonitor(Node):
    def __init__(self):
        super().__init__('task_monitor')

        self.client = self.create_client(
            GetRobotStatus,
            '/get_robot_status'
        )

        self.manipulator_client = self.create_client(
            GetRobotStatus,
            '/get_manipulator_status'
        )

        self.get_logger().info(
            'Task Monitor node has started.'
        )

    def wait_for_service(self, timeout_sec=5.0):
        self.get_logger().info(
            'Waiting for /get_robot_status service...'
        )

        return self.client.wait_for_service(
            timeout_sec=timeout_sec
        )

    def request_status(self):
        request = GetRobotStatus.Request()

        future = self.client.call_async(request)

        rclpy.spin_until_future_complete(self, future)

        return future.result()

    def request_manipulator_status(self, timeout_sec=3.0):
        if not self.manipulator_client.wait_for_service(
            timeout_sec=timeout_sec
        ):
            return None

        future = self.manipulator_client.call_async(
            GetRobotStatus.Request()
        )

        rclpy.spin_until_future_complete(
            self,
            future,
            timeout_sec=timeout_sec
        )

        return future.result()


def format_status(response, title='Robot Status'):
    lines = [
        title,
        '-' * len(title),
        f'Status: {response.status}',
        f'Current Action: {response.current_action}',
    ]

    if response.status == 'EXECUTING':
        lines.append(
            f'Elapsed Time: {response.elapsed_time:.1f} seconds'
        )

    return '\n'.join(lines)


def main(args=None):
    rclpy.init(args=args)

    node = TaskMonitor()

    if not node.wait_for_service():
        node.get_logger().error(
            'Service /get_robot_status is not available. '
            'Is the Robot Simulator running?'
        )

        node.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    response = node.request_status()

    if response is not None:
        print()
        print(format_status(response))
        print()
    else:
        node.get_logger().error(
            'Failed to receive a response from the service.'
        )

    manipulator_response = node.request_manipulator_status()

    if manipulator_response is not None:
        print(format_status(manipulator_response, 'Manipulator Status'))
        print()
    else:
        node.get_logger().warning(
            'Service /get_manipulator_status is not available. '
            'Is the Manipulator Controller running?'
        )

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

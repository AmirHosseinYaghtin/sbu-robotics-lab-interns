import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from std_msgs.msg import String
from robot_task_interfaces.srv import GetRobotStatus


class RobotSimulator(Node):

    IDLE = 'IDLE'
    EXECUTING = 'EXECUTING'
    ERROR = 'ERROR'

    def __init__(self):
        super().__init__('robot_simulator')

        self.status = self.IDLE
        self.current_action = None
        self.action_started_at = None
        self.operation_timer = None

        self.action_handlers = {
            'MOVE_TO_WORKSTATION': self.move_to_workstation,
            'PICK_OBJECT': self.pick_object,
            'MOVE_TO_SHELF': self.move_to_shelf,
            'PLACE_OBJECT': self.place_object,
        }

        self.action_subscription = self.create_subscription(
            String,
            '/task/action',
            self.action_callback,
            10
        )

        self.action_done_publisher = self.create_publisher(
            Bool,
            '/action_done',
            10
        )

        self.status_service = self.create_service(
            GetRobotStatus,
            '/get_robot_status',
            self.get_robot_status_callback
        )

        self.get_logger().info(
            'Robot Simulator node has started.'
        )

    def action_callback(self, message):
        action = message.data.strip()

        self.get_logger().info(
            f'Received action: {action}'
        )

        if self.status == self.ERROR:
            self.get_logger().warning(
                'Robot is in ERROR state. Action ignored.'
            )
            return

        if self.status == self.EXECUTING:
            self.get_logger().warning(
                f'Robot is already executing '
                f'{self.current_action}. Action ignored.'
            )
            return

        handler = self.action_handlers.get(action)

        if handler is None:
            self.status = self.ERROR
            self.current_action = action

            self.get_logger().error(
                f'Unknown action: {action}. '
                f'Robot entered ERROR state.'
            )

            self.publish_action_result(False)
            return

        handler()

    def move_to_workstation(self):
        self.start_action(
            action='MOVE_TO_WORKSTATION',
            duration=5.0
        )

    def pick_object(self):
        self.start_action(
            action='PICK_OBJECT',
            duration=3.0
        )

    def move_to_shelf(self):
        self.start_action(
            action='MOVE_TO_SHELF',
            duration=5.0
        )

    def place_object(self):
        self.start_action(
            action='PLACE_OBJECT',
            duration=2.0
        )

    def start_action(self, action, duration):
        self.status = self.EXECUTING
        self.current_action = action
        self.action_started_at = self.get_clock().now()

        self.operation_timer = self.create_timer(
            duration,
            self.complete_current_action
        )

        self.get_logger().info(
            f'Starting action: {action} '
            f'({duration:.1f} seconds)'
        )

    def complete_current_action(self):
        if self.operation_timer is not None:
            self.operation_timer.cancel()
            self.destroy_timer(self.operation_timer)
            self.operation_timer = None

        finished_at = self.get_clock().now()

        elapsed_seconds = (
            finished_at - self.action_started_at
        ).nanoseconds / 1_000_000_000

        completed_action = self.current_action

        self.status = self.IDLE
        self.current_action = None
        self.action_started_at = None

        self.get_logger().info(
            f'Completed action: {completed_action} '
            f'in {elapsed_seconds:.2f} seconds. '
            f'Robot is now IDLE.'
        )

        self.publish_action_result(True)

    def publish_action_result(self, success):
        result_message = Bool()
        result_message.data = success

        self.action_done_publisher.publish(
            result_message
        )

        self.get_logger().info(
            f'Published action result: {success}'
        )

    def current_elapsed_seconds(self):
        if self.action_started_at is None:
            return 0.0

        now = self.get_clock().now()

        return (
            now - self.action_started_at
        ).nanoseconds / 1_000_000_000

    def get_robot_status_callback(self, request, response):
        response.status = self.status
        response.current_action = (
            self.current_action
            if self.current_action is not None
            else 'NONE'
        )
        response.elapsed_time = self.current_elapsed_seconds()

        self.get_logger().info(
            'Robot status requested by a client.'
        )

        return response


def main(args=None):
    rclpy.init(args=args)

    node = RobotSimulator()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

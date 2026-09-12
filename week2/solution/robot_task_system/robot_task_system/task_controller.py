from collections import deque

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from std_msgs.msg import String


class TaskController(Node):

    def __init__(self):
        super().__init__('task_controller')

        self.action_queue = deque([
            'MOVE_TO_WORKSTATION',
            'PICK_OBJECT',
            'MOVE_TO_SHELF',
            'PLACE_OBJECT',
        ])

        self.current_action = None
        self.waiting_for_result = False
        self.queue_stopped = False
        self.waiting_message_logged = False

        self.action_publisher = self.create_publisher(
            String,
            '/task/action',
            10
        )

        self.action_done_subscription = (
            self.create_subscription(
                Bool,
                '/action_done',
                self.action_done_callback,
                10
            )
        )

        self.dispatch_timer = self.create_timer(
            0.5,
            self.try_dispatch_next_action
        )

        self.get_logger().info(
            'Task Controller node has started.'
        )

        self.get_logger().info(
            f'Queue contains '
            f'{len(self.action_queue)} actions.'
        )

    def try_dispatch_next_action(self):
        if self.queue_stopped:
            return

        if self.waiting_for_result:
            return

        if not self.action_queue:
            self.dispatch_timer.cancel()

            self.get_logger().info(
                'All actions completed successfully.'
            )
            return

        if self.action_publisher.get_subscription_count() == 0:
            if not self.waiting_message_logged:
                self.get_logger().info(
                    'Waiting for Robot Simulator...'
                )
                self.waiting_message_logged = True

            return

        self.waiting_message_logged = False

        self.current_action = self.action_queue[0]

        message = String()
        message.data = self.current_action

        self.action_publisher.publish(message)

        self.waiting_for_result = True

        self.get_logger().info(
            f'Dispatched action: {self.current_action}'
        )

        self.get_logger().info(
            'Waiting for action result...'
        )

    def action_done_callback(self, message):
        if not self.waiting_for_result:
            self.get_logger().warning(
                'Unexpected action result received.'
            )
            return

        if message.data:
            completed_action = self.action_queue.popleft()

            self.get_logger().info(
                f'Action succeeded: {completed_action}'
            )

            self.current_action = None
            self.waiting_for_result = False

            self.get_logger().info(
                f'{len(self.action_queue)} actions remaining.'
            )

        else:
            failed_action = self.current_action

            self.queue_stopped = True
            self.waiting_for_result = False

            self.get_logger().error(
                f'Action failed: {failed_action}. '
                f'Task queue stopped.'
            )


def main(args=None):
    rclpy.init(args=args)

    node = TaskController()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

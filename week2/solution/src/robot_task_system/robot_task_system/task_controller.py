import math
import os
from collections import deque

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from std_msgs.msg import String

from robot_task_interfaces.msg import MoveCommand
from robot_task_interfaces.msg import Waypoint
from robot_task_system import plan_parser


class TaskController(Node):

    def __init__(self):
        super().__init__('task_controller')

        self.startup_ok = False

        self.declare_parameter('plan_file', '')
        self.declare_parameter('anchor_to_origin', True)
        plan_file = self.get_parameter('plan_file').value
        anchor = self.get_parameter('anchor_to_origin').value

        if not plan_file:
            self.get_logger().fatal(
                'No plan_file parameter was provided. The Task Controller '
                'requires a PDDLStream plan produced by export_plan.py. '
                'Launch with plan_file:=/abs/path/plan.json. Aborting.'
            )
            return

        if not os.path.exists(plan_file):
            self.get_logger().fatal(
                'plan_file "{}" was not found. Aborting instead of silently '
                'running a fallback scenario.'.format(plan_file)
            )
            return

        plan = plan_parser.load_plan(plan_file)
        actions = plan_parser.parse_actions(plan)

        if not actions:
            self.get_logger().fatal(
                'plan_file "{}" contains no executable actions. '
                'Aborting.'.format(plan_file)
            )
            return

        if anchor:
            self._anchor_to_origin(actions)

        self.action_queue = deque(actions)
        self.plan_mode = True

        self.get_logger().info(
            'Loaded plan "{}" (problem={}, cost={}, {} actions).'.format(
                os.path.basename(plan_file),
                plan.get('problem', '?'),
                plan.get('cost', '?'),
                len(actions),
            )
        )
        self.get_logger().info(
            'Planned actions:\n' + plan_parser.summarize(actions)
        )

        self.current_action = None
        self.waiting_for_result = False
        self.queue_stopped = False
        self.waiting_message_logged = False

        self.action_publisher = self.create_publisher(
            String,
            '/task/action',
            10
        )

        self.move_publisher = self.create_publisher(
            MoveCommand,
            '/move_command',
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

        self.startup_ok = True

    def _anchor_to_origin(self, actions):
        start = None
        for action in actions:
            if action['type'] == 'move_base' and action['waypoints']:
                start = action['waypoints'][0]
                break

        if start is None:
            return

        start_x, start_y, start_theta = start
        cos_t = math.cos(-start_theta)
        sin_t = math.sin(-start_theta)

        def transform(x, y, theta):
            rel_x = x - start_x
            rel_y = y - start_y
            new_x = rel_x * cos_t - rel_y * sin_t
            new_y = rel_x * sin_t + rel_y * cos_t
            return (new_x, new_y, self._normalize_angle(theta - start_theta))

        for action in actions:
            if action['type'] != 'move_base':
                continue
            action['waypoints'] = [
                transform(x, y, theta)
                for (x, y, theta) in action['waypoints']
            ]
            action['goal'] = transform(*action['goal'])

        self.get_logger().info(
            'Anchored plan to odom origin (start pose was '
            'x={:.2f}, y={:.2f}, theta={:.2f}).'.format(
                start_x, start_y, start_theta
            )
        )

    @staticmethod
    def _normalize_angle(angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    def _action_label(self, action):
        if isinstance(action, dict):
            return action['label']
        return action

    def _is_move(self, action):
        return isinstance(action, dict) and action['type'] == 'move_base'

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

        next_action = self.action_queue[0]

        if self._is_move(next_action):
            if self.move_publisher.get_subscription_count() == 0:
                if not self.waiting_message_logged:
                    self.get_logger().info(
                        'Waiting for Robot Controller...'
                    )
                    self.waiting_message_logged = True
                return

            self.waiting_message_logged = False
            self.current_action = next_action

            waypoints = list(next_action['waypoints'])
            goal = next_action.get('goal')
            if goal is not None and (not waypoints or waypoints[-1] != goal):
                waypoints.append(goal)

            message = MoveCommand()
            message.action_label = next_action['label']
            message.waypoints = [
                Waypoint(x=x, y=y, theta=theta)
                for (x, y, theta) in waypoints
            ]
            self.move_publisher.publish(message)

            self.waiting_for_result = True

            self.get_logger().info(
                'Dispatched MOVE_BASE ({} waypoints, goal theta={:.2f}).'.format(
                    len(waypoints),
                    goal[2] if goal is not None else 0.0,
                )
            )
            self.get_logger().info(
                'Waiting for action result...'
            )
            return

        if self.action_publisher.get_subscription_count() == 0:
            if not self.waiting_message_logged:
                self.get_logger().info(
                    'Waiting for Robot Controller...'
                )
                self.waiting_message_logged = True

            return

        self.waiting_message_logged = False

        self.current_action = next_action

        message = String()
        message.data = self._action_label(next_action)

        self.action_publisher.publish(message)

        self.waiting_for_result = True

        self.get_logger().info(
            f'Dispatched action: {self._action_label(next_action)}'
        )

        self.get_logger().info(
            'Waiting for action result...'
        )



def main(args=None):
    rclpy.init(args=args)

    node = TaskController()

    if not node.startup_ok:
        node.get_logger().fatal(
            'Task Controller failed to start (no valid plan). Shutting down.'
        )
        node.destroy_node()
        rclpy.shutdown()
        return

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

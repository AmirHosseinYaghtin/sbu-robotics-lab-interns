import math
import os
from collections import deque

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

from robot_task_interfaces.msg import ArmWaypoint
from robot_task_interfaces.msg import ManipulatorCommand
from robot_task_interfaces.msg import MoveCommand
from robot_task_interfaces.msg import Waypoint
from robot_task_system import plan_geometry
from robot_task_system import plan_parser


class TaskController(Node):

    def __init__(self):
        super().__init__('task_controller')

        self.startup_ok = False

        self.declare_parameter('plan_file', '')
        self.declare_parameter('anchor_to_origin', True)
        self.declare_parameter('apply_approach_adjustment', True)
        self.declare_parameter('grasp_reach', 0.20)
        self.declare_parameter('arm_mount_x', -0.092)
        self.declare_parameter('target_frame', 'odom')
        self.declare_parameter('consistency_tolerance', 0.05)
        self.declare_parameter('action_timeout', 300.0)

        plan_file = self.get_parameter('plan_file').value
        anchor = self.get_parameter('anchor_to_origin').value
        self.target_frame = self.get_parameter('target_frame').value
        self.action_timeout = self.get_parameter('action_timeout').value

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

        try:
            plan, actions = plan_parser.load_and_validate(plan_file)
        except plan_parser.PlanError as error:
            self.get_logger().fatal(
                'plan_file "{}" is invalid: {}. Aborting.'.format(
                    plan_file,
                    error,
                )
            )
            return

        if anchor:
            self._anchor_to_origin(actions)

        actions = plan_geometry.prepare_actions(
            actions,
            approach=self.get_parameter('apply_approach_adjustment').value,
            grasp_reach=self.get_parameter('grasp_reach').value,
            arm_mount_x=self.get_parameter('arm_mount_x').value,
        )

        self._log_manipulation_geometry(
            actions,
            self.get_parameter('consistency_tolerance').value,
        )

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
        self.dispatched_at = None

        self.manipulator_publisher = self.create_publisher(
            ManipulatorCommand,
            '/manipulator_command',
            10
        )

        self.move_publisher = self.create_publisher(
            MoveCommand,
            '/move_command',
            10
        )

        self.action_done_subscription = self.create_subscription(
            Bool,
            '/action_done',
            self.action_done_callback,
            10
        )

        self.dispatch_timer = self.create_timer(
            0.5,
            self.try_dispatch_next_action
        )

        self.get_logger().info(
            'Task Controller node has started.'
        )

        self.get_logger().info(
            f'Queue contains {len(self.action_queue)} actions.'
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

            return (
                new_x,
                new_y,
                self._normalize_angle(theta - start_theta),
            )

        for action in actions:
            if action['type'] != 'move_base':
                if action.get('base_conf') is not None:
                    action['base_conf'] = transform(*action['base_conf'])

                if action.get('object_pose') is not None:
                    action['object_pose'] = transform(
                        action['object_pose'][0],
                        action['object_pose'][1],
                        0.0,
                    )[:2]
                continue

            action['waypoints'] = [
                transform(x, y, theta)
                for (x, y, theta) in action['waypoints']
            ]

            if action.get('goal') is not None:
                action['goal'] = transform(*action['goal'])

        self.get_logger().info(
            'Anchored plan to odom origin (start pose was '
            'x={:.2f}, y={:.2f}, theta={:.2f}).'.format(
                start_x,
                start_y,
                start_theta,
            )
        )

    def _log_manipulation_geometry(self, actions, tolerance):
        for action in actions:
            if action['type'] == 'move_base':
                continue

            if action['consistency_error'] > tolerance:
                self.get_logger().warning(
                    '{}: planner arm goal and object pose disagree by '
                    '{:.3f} m.'.format(
                        action['label'],
                        action['consistency_error'],
                    )
                )

            if action['approach_shift']:
                self.get_logger().info(
                    '{}: base stops {:.3f} m closer so the object is within '
                    'arm reach.'.format(
                        action['label'],
                        action['approach_shift'],
                    )
                )

    @staticmethod
    def _normalize_angle(angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi

        while angle < -math.pi:
            angle += 2.0 * math.pi

        return angle

    @staticmethod
    def _build_manipulator_command(action, frame_id='odom'):
        message = ManipulatorCommand()

        message.action_type = action['type']
        message.action_label = action['label']
        message.object_name = action['obj']
        message.frame_id = frame_id

        target = (
            action.get('target_world')
            or action.get('object_pose')
            or (0.0, 0.0)
        )

        message.target_x = float(target[0])
        message.target_y = float(target[1])

        grasp = action.get('grasp') or {}

        message.grasp_dx = float(grasp.get('dx', 0.0))
        message.grasp_dy = float(grasp.get('dy', 0.0))
        message.grasp_dtheta = float(grasp.get('dtheta', 0.0))

        message.arm_start = [
            float(value)
            for value in (action.get('arm_start') or [])
        ]

        message.arm_goal = [
            float(value)
            for value in (action.get('arm_goal') or [])
        ]

        message.trajectory = []

        for joints in action.get('arm_trajectory', []):
            waypoint = ArmWaypoint()

            waypoint.joints = [
                float(value)
                for value in joints
            ]

            message.trajectory.append(waypoint)

        return message

    def _action_label(self, action):
        if isinstance(action, dict):
            return action['label']

        return action

    def _is_move(self, action):
        return (
            isinstance(action, dict)
            and action['type'] == 'move_base'
        )

    def _is_manipulation(self, action):
        return (
            isinstance(action, dict)
            and action['type'] in ('pick', 'place')
        )

    def try_dispatch_next_action(self):
        if self.queue_stopped:
            return

        if self.waiting_for_result:
            elapsed = (
                self.get_clock().now() - self.dispatched_at
            ).nanoseconds / 1e9

            if elapsed > self.action_timeout:
                self.get_logger().error(
                    'No result for {} within {:.0f} seconds. '
                    'Stopping task execution.'.format(
                        self._action_label(self.current_action),
                        self.action_timeout,
                    )
                )

                self.queue_stopped = True
                self.current_action = None
                self.waiting_for_result = False
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

            if (
                goal is not None
                and (not waypoints or waypoints[-1] != goal)
            ):
                waypoints.append(goal)

            message = MoveCommand()
            message.action_label = next_action['label']
            message.reverse = bool(next_action.get('reverse', False))
            message.waypoints = [
                Waypoint(x=x, y=y, theta=theta)
                for (x, y, theta) in waypoints
            ]

            self.move_publisher.publish(message)
            self.waiting_for_result = True
            self.dispatched_at = self.get_clock().now()

            self.get_logger().info(
                'Dispatched {} '
                '({} waypoints, goal theta={:.2f}).'.format(
                    next_action['label'],
                    len(waypoints),
                    goal[2] if goal is not None else 0.0,
                )
            )

            self.get_logger().info(
                'Waiting for action result...'
            )
            return

        if self._is_manipulation(next_action):
            if self.manipulator_publisher.get_subscription_count() == 0:
                if not self.waiting_message_logged:
                    self.get_logger().info(
                        'Waiting for Manipulator Controller...'
                    )
                    self.waiting_message_logged = True

                return

            self.waiting_message_logged = False
            self.current_action = next_action

            message = self._build_manipulator_command(
                next_action,
                self.target_frame,
            )
            self.manipulator_publisher.publish(message)

            self.waiting_for_result = True
            self.dispatched_at = self.get_clock().now()

            self.get_logger().info(
                'Dispatched {} for {} '
                '(target x={:.3f}, y={:.3f} in {}).'.format(
                    next_action['type'].upper(),
                    next_action['obj'],
                    message.target_x,
                    message.target_y,
                    self.target_frame,
                )
            )

            self.get_logger().info(
                'Waiting for action result...'
            )
            return

        self.get_logger().error(
            'Unsupported action type: {}. '
            'Stopping task execution.'.format(
                next_action.get('type', 'unknown')
            )
        )

        self.queue_stopped = True
        self.current_action = None
        self.waiting_for_result = False
        self.waiting_message_logged = False

    def action_done_callback(self, message):
        if not self.waiting_for_result or self.current_action is None:
            self.get_logger().warning(
                'Received an action result while no action is pending. '
                'Ignoring.'
            )
            return

        action_label = self._action_label(self.current_action)

        if message.data:
            if self.action_queue:
                self.action_queue.popleft()

            self.get_logger().info(
                f'Action completed successfully: {action_label}'
            )

            self.current_action = None
            self.waiting_for_result = False
            self.waiting_message_logged = False
            return

        self.get_logger().error(
            f'Action failed: {action_label}. '
            'Stopping task execution.'
        )

        self.queue_stopped = True
        self.current_action = None
        self.waiting_for_result = False
        self.waiting_message_logged = False


def main(args=None):
    rclpy.init(args=args)

    node = TaskController()

    if not node.startup_ok:
        node.get_logger().fatal(
            'Task Controller failed to start '
            '(no valid plan). Shutting down.'
        )

        node.destroy_node()
        rclpy.shutdown()
        return

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

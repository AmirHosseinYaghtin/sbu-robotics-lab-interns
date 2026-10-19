import math
import os
from collections import deque

import rclpy
from rclpy.node import Node
import time
from action_msgs.msg import GoalStatus
from rclpy.action import ActionClient
from std_srvs.srv import Trigger
from robot_task_interfaces.action import MoveTo, Manipulate
from robot_task_system.execution_state import TaskState
from robot_task_system.parameter_validation import validate_startup, freeze_parameters, positive

from robot_task_interfaces.msg import ArmWaypoint
from robot_task_interfaces.msg import ManipulatorCommand
from robot_task_interfaces.msg import MoveCommand
from robot_task_interfaces.msg import Waypoint
from robot_task_system import plan_geometry
from robot_task_system import plan_order
from robot_task_system import plan_parser
from robot_task_system import scene


class TaskController(Node):

    # TODO-W5-02: expose execution limits as validated ROS parameters.
    # Match the completed project's shipped pick_place.yaml values for now.
    ACTION_TIMEOUT = 900.0
    SERVER_TIMEOUT = 120.0
    CANCEL_TIMEOUT = 20.0

    def __init__(self, **node_options):
        super().__init__('task_controller', **node_options)

        self.startup_ok = False

        self.declare_parameter('plan_file', '')
        self.declare_parameter('anchor_to_origin', True)
        self.declare_parameter('apply_approach_adjustment', True)
        self.declare_parameter('grasp_reach', 0.20)
        self.declare_parameter('arm_mount_x', -0.092)
        self.declare_parameter('target_frame', 'odom')
        self.declare_parameter('consistency_tolerance', 0.05)
        validate_startup(self, {'grasp_reach': positive, 'consistency_tolerance': positive})
        # The gripper holds one object: plans that pick several objects
        # before placing them are reordered into pick -> place pairs.
        self.declare_parameter('one_object_at_a_time', True)
        # m the base keeps from tables/obstacles on the new (reordered) paths.
        self.declare_parameter('route_clearance', plan_order.DEFAULT_CLEARANCE)

        validate_startup(self, {'route_clearance': positive})
        freeze_parameters(self, (
            'plan_file', 'anchor_to_origin', 'apply_approach_adjustment', 'grasp_reach',
            'arm_mount_x', 'target_frame', 'consistency_tolerance',
            'one_object_at_a_time', 'route_clearance',
            'action_timeout', 'server_timeout', 'cancel_timeout'))
        plan_file = self.get_parameter('plan_file').value
        anchor = self.get_parameter('anchor_to_origin').value
        self.target_frame = self.get_parameter('target_frame').value

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
            raw_actions = plan_parser.parse_actions(plan_parser.load_plan(plan_file))
        except (OSError, ValueError, plan_parser.PlanError):
            raw_actions = []

        try:
            plan, actions = plan_parser.load_and_validate(
                plan_file,
                one_at_a_time=self.get_parameter('one_object_at_a_time').value,
                clearance=float(self.get_parameter('route_clearance').value),
            )
        except plan_parser.PlanError as error:
            self.get_logger().fatal(
                'plan_file "{}" is invalid: {}. Aborting.'.format(
                    plan_file,
                    error,
                )
            )
            return

        if plan_order.held_peak(raw_actions) > 1:
            self.get_logger().info(
                'The plan holds up to {} objects at once; reordered it to carry '
                'one object at a time ({:.1f} m of base paths, planner plan: '
                '{:.1f} m).'.format(
                    plan_order.held_peak(raw_actions),
                    plan_order.total_drive(actions),
                    plan_order.total_drive(raw_actions),
                )
            )

        if anchor:
            self._anchor_to_origin(plan, actions)

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
        self.state = TaskState(os.path.abspath(plan_file), len(actions))
        self.goal_handle = None
        self.goal_future = None
        self.result_future = None
        self.cancel_future = None
        self.active_client = None
        self.dispatched_at = None
        self.cancel_started = None
        self.wait_started = time.monotonic()
        self.last_feedback = None
        self.move_client = ActionClient(self, MoveTo, '/move_to')
        self.manipulator_client = ActionClient(self, Manipulate, '/manipulate')
        # TODO-W5-01: wire /task/status and /get_task_status from self.state.
        # GetTaskStatus.srv remains the agreed interface, with no server yet.
        self.cancel_service = self.create_service(Trigger, '/task/cancel', self.cancel_task)
        self.emergency_service = self.create_service(Trigger, '/task/emergency_stop', self.emergency_stop)
        self.stop_clients = [self.create_client(Trigger, name) for name in (
            '/robot_controller/emergency_stop', '/manipulator_controller/emergency_stop')]
        self.stop_requests = {}
        self.controller_stop_required = False
        self.dispatch_timer = self.create_timer(0.1, self.try_dispatch_next_action)
        self.startup_ok = True
        self.publish_status()

    def _anchor_to_origin(self, plan, actions):
        # Same transform the launch file uses to place the Gazebo scene.
        start = scene.plan_anchor(plan, actions)

        if start is None:
            return

        scene.anchor_actions(actions, start)

        self.get_logger().info(
            'Anchored plan to odom origin (start pose was '
            'x={:.2f}, y={:.2f}, theta={:.2f}).'.format(*start)
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

    def publish_status(self):
        """TODO-W5-01: publish changes without changing execution state."""
        # Intentional scaffold. Internal state and terminal logs still work.
        return None

    def stop_task(self, reason, emergency=False, failure=False):
        self.state.stop(reason, emergency=emergency, failure=failure)
        self.cancel_started = self.cancel_started or time.monotonic()
        self.request_cancel()
        self.publish_status()
        self.get_logger().error('TASK {}: {}'.format(self.state.task_state, reason))

    def cancel_task(self, request, response):
        if self.state.task_state in TaskState.TERMINAL:
            response.success = False
            response.message = 'Task is already ' + self.state.task_state
            return response
        self.stop_task('task cancellation requested')
        response.success = True
        response.message = 'Cancellation requested; inspect terminal logs for outcome'
        return response

    def emergency_stop(self, request, response):
        self.stop_task('software emergency stop requested', emergency=True)
        self.send_emergency_stops()
        response.success = True
        response.message = 'Software stop latched, NOT safety-rated; inspect controller acknowledgements'
        return response

    def send_emergency_stops(self):
        self.controller_stop_required = True
        # Retry DDS discovery; a task may be stopped before servers start.
        for index, client in enumerate(self.stop_clients):
            if index not in self.stop_requests and client.service_is_ready():
                future = client.call_async(Trigger.Request())
                self.stop_requests[index] = future
                future.add_done_callback(self.stop_acknowledged)

    def stop_acknowledged(self, future):
        try:
            result = future.result()
            if result is None or not result.success:
                raise RuntimeError('controller rejected software stop')
            self.get_logger().warning(result.message)
        except Exception as error:
            self.get_logger().error('Emergency-stop acknowledgement failed: ' + str(error))

    def request_cancel(self):
        if self.goal_handle is not None and self.cancel_future is None:
            try:
                self.cancel_future = self.goal_handle.cancel_goal_async()
                self.cancel_future.add_done_callback(self.cancel_response)
            except Exception as error:
                message = 'Cancel transport error: ' + str(error)
                if message not in self.state.message:
                    self.state.message = (self.state.message + '; ' + message
                                          if self.state.message else message)
                    self.get_logger().error(message)
                    self.publish_status()
                # Keep the task stopped; let the timer reach its timeout fallback.

    def cancel_response(self, future):
        try:
            response = future.result()
            if not response.goals_canceling:
                self.get_logger().warning('Cancel not accepted (goal may already be terminal); waiting for result')
        except Exception as error:
            self.state.message = 'Cancel transport error: ' + str(error)
            self.publish_status()

    def try_dispatch_next_action(self):
        if self.state.task_state == 'EMERGENCY_STOP' or self.controller_stop_required:
            self.send_emergency_stops()
        if self.state.task_state in TaskState.TERMINAL or self.state.task_state == 'CANCELING':
            self.request_cancel()
            pending = self.goal_future is not None or self.goal_handle is not None
            if pending and self.cancel_started is not None and time.monotonic() - self.cancel_started > self.CANCEL_TIMEOUT:
                if self.state.action_state != 'STOP_UNCONFIRMED':
                    self.state.action_state = 'STOP_UNCONFIRMED'
                    self.state.message = 'Cancellation/result acknowledgement timeout; physical stop unconfirmed'
                    if self.state.task_state != 'EMERGENCY_STOP':
                        self.state.task_state = 'FAILED'
                    self.get_logger().error(self.state.message)
                    # Independent stop request also covers a lost action connection.
                    self.send_emergency_stops()
                    self.publish_status()
            return
        if self.goal_future is not None or self.goal_handle is not None:
            if time.monotonic() - self.dispatched_at > self.ACTION_TIMEOUT:
                self.stop_task('action/goal response timeout', failure=True)
            return
        if not self.action_queue:
            return
        action = self.action_queue[0]
        client = self.move_client if self._is_move(action) else self.manipulator_client
        if not client.server_is_ready():
            if time.monotonic() - self.wait_started > self.SERVER_TIMEOUT:
                self.stop_task('action server unavailable', failure=True)
            return
        self.current_action = action
        if self.state.task_state == 'IDLE':
            self.get_logger().info('TASK STARTED')
        self.state.begin(action['label'])
        self.state.action_state = 'SENDING'
        self.active_client = client
        self.dispatched_at = time.monotonic()
        self.cancel_future = None
        self.cancel_started = None
        if self._is_move(action):
            waypoints = list(action['waypoints'])
            goal = action.get('goal')
            if goal is not None and (not waypoints or waypoints[-1] != goal):
                waypoints.append(goal)
            command = MoveCommand(action_label=action['label'],
                                  reverse=bool(action.get('reverse', False)),
                                  waypoints=[Waypoint(x=x, y=y, theta=t) for x, y, t in waypoints])
            request = MoveTo.Goal(command=command)
        else:
            request = Manipulate.Goal(command=self._build_manipulator_command(action, self.target_frame))
        self.get_logger().info('[{}/{}] Dispatched {}'.format(
            self.state.completed_actions + 1, self.state.total_actions, action['label']))
        try:
            self.goal_future = client.send_goal_async(request, feedback_callback=self.feedback_callback)
            self.goal_future.add_done_callback(self.goal_response)
        except Exception as error:
            self.goal_future = None
            self.state.result(False, message='send goal failed: ' + str(error))
        self.publish_status()

    def goal_response(self, future):
        self.goal_future = None
        try:
            handle = future.result()
            if not handle.accepted:
                if self.state.task_state == 'CANCELING':
                    self.state.task_state = 'CANCELED'
                    self.state.action_state = 'REJECTED'
                else:
                    self.state.result(False, message='controller rejected goal')
                self.publish_status()
                return
            self.goal_handle = handle
            self.result_future = handle.get_result_async()
            self.result_future.add_done_callback(self.action_result)
            if self.goal_handle is not handle:
                return  # a terminal result may already have been delivered
            if self.state.task_state in TaskState.TERMINAL or self.state.task_state == 'CANCELING':
                self.request_cancel()  # includes cancel-before-acceptance race
            else:
                self.state.action_state = 'EXECUTING'
        except Exception as error:
            self.stop_task('goal/result transport error: ' + str(error), failure=True)
        self.publish_status()

    def feedback_callback(self, message):
        if self.state.task_state != 'EXECUTING':
            return
        feedback = message.feedback
        if hasattr(feedback, 'current_step'):
            text = '{} ({}/{})'.format(feedback.current_step, feedback.completed_steps, feedback.total_steps)
        else:
            text = 'Waypoint: {}/{}; Distance remaining: {:.2f} m'.format(
                feedback.current_waypoint, feedback.total_waypoints, feedback.distance_remaining)
        # Servers throttle feedback; log only meaningful rounded changes.
        if text != self.last_feedback:
            self.get_logger().info('  ' + text)
            self.last_feedback = text

    def action_result(self, future):
        try:
            response = future.result()
            succeeded = response.status == GoalStatus.STATUS_SUCCEEDED and response.result.success
            canceled = response.status == GoalStatus.STATUS_CANCELED
            advance = self.state.result(succeeded, canceled, response.result.message)
        except Exception as error:
            advance = self.state.result(False, message='result transport error: ' + str(error))
            self.send_emergency_stops()
        self.goal_handle = None
        self.result_future = None
        self.current_action = None
        if advance:
            self.action_queue.popleft()
            self.wait_started = time.monotonic()
            if self.state.task_state == 'COMPLETED':
                self.get_logger().info('All actions completed successfully. TASK COMPLETED')
            else:
                self.get_logger().info('  SUCCESS')
        else:
            self.get_logger().error('TASK {}: {}'.format(self.state.task_state, self.state.message))
        self.publish_status()


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

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

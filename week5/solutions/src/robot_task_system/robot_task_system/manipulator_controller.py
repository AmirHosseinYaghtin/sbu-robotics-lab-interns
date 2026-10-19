import math
import time

from action_msgs.msg import GoalStatus
from builtin_interfaces.msg import Duration
from control_msgs.action import GripperCommand
from geometry_msgs.msg import PointStamped
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.time import Time
from robot_task_interfaces.action import Manipulate
from robot_task_system.controller_action import ControllerAction
from robot_task_system.parameter_validation import validate_startup, freeze_parameters, positive
from robot_task_interfaces.srv import GetRobotStatus
from robot_task_system import manipulation_sequence as sequence
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger
from tf2_geometry_msgs import do_transform_point
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint


class StepFailure(Exception):
    pass


class ManipulatorController(Node):

    IDLE = 'IDLE'
    EXECUTING = 'EXECUTING'
    ERROR = 'ERROR'
    STARTING = 'STARTING'
    # TODO-W5-02: make execution deadlines configurable with validation.
    ARM_TIMEOUT_MARGIN = 10.0
    GRIPPER_TIMEOUT = 10.0
    STARTUP_TIMEOUT = 120.0

    def __init__(self):
        super().__init__('manipulator_controller')

        self.declare_parameter('arm_topic', '/arm_controller/joint_trajectory')
        self.declare_parameter('gripper_action', '/gripper_controller/gripper_cmd')
        self.declare_parameter('joint_states_topic', '/joint_states')
        self.declare_parameter('joint_names', ['joint1', 'joint2', 'joint3', 'joint4'])
        self.declare_parameter('arm_base_frame', 'link1')
        self.declare_parameter('home_joints', [0.0, -1.0, 0.3, 0.7])
        self.declare_parameter('fixed_joint1', 0.0)
        # About 8 cm above the calibrated grasp/place, with the fingers down.
        # continuous2d angles describe a different robot and are not ROS joints.
        self.declare_parameter('clearance_joints', [0.44, -0.38, 1.51])
        self.declare_parameter('grasp_joints', [0.688, -0.058, 0.94])
        self.declare_parameter('place_joints', [0.643, -0.068, 0.995])
        self.declare_parameter('gripper_open_position', 0.019)
        self.declare_parameter('gripper_closed_position', -0.0085)
        self.declare_parameter('gripper_max_effort', 10.0)
        self.declare_parameter('verify_grasp', True)
        self.declare_parameter('use_sim_attachment', False)
        self.declare_parameter('attachment_timeout', 5.0)
        self.declare_parameter('grasp_detect_margin', 0.001)
        self.declare_parameter('grasp_reach', 0.20)
        self.declare_parameter('reach_tolerance', 0.04)
        self.declare_parameter('max_joint_speed', 0.3)
        self.declare_parameter('min_segment_time', 1.0)
        self.declare_parameter('joint_tolerance', 0.05)
        # OpenMANIPULATOR-X joint limits (turtlebot3_manipulation URDF).
        # Invalid calibrated poses are rejected; clamping changes grasp geometry.
        self.declare_parameter('joint_lower_limits', [-2.827, -1.791, -0.942, -1.791])
        self.declare_parameter('joint_upper_limits', [2.827, 1.571, 1.382, 2.042])
        self.declare_parameter('joint_limit_margin', 0.02)

        self.joint_names = list(self.get_parameter('joint_names').value)
        self.home = list(self.get_parameter('home_joints').value)
        if len(self.joint_names) != 4 or len(set(self.joint_names)) != 4:
            raise ValueError('joint_names must contain four distinct names')
        poses = [self.home] + [sequence.arm_configuration(
            self.get_parameter('fixed_joint1').value, self.get_parameter(name).value)
            for name in ('clearance_joints', 'grasp_joints', 'place_joints')]
        self.validate_points(poses)

        self.status = self.STARTING
        self.current_action = None
        self.current_command = None
        self.action_started_at = None
        self.held_object = None
        self.joint_positions = {}

        self.steps = []
        self.step_index = 0
        self.step_started = False
        self.step_deadline = None
        self.arm_goal = None
        self.arm_motion_ends_at = None
        self.gripper_result = None
        self.gripper_handle = None
        self.gripper_goal_future = None
        self.gripper_cancel_future = None
        self.cancel_hold_sent = False
        self.attachment_future = None
        self.attachment_clients = {}
        self.attachment_client = None
        self.attachment_operation = None
        self.attachment_object = None

        self.started_at = self.now_seconds()

        self.arm_publisher = self.create_publisher(
            JointTrajectory,
            self.get_parameter('arm_topic').value,
            10,
        )
        self.gripper_client = ActionClient(
            self,
            GripperCommand,
            self.get_parameter('gripper_action').value,
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.joint_state_subscription = self.create_subscription(
            JointState,
            self.get_parameter('joint_states_topic').value,
            self.joint_state_callback,
            20,
        )
        self.status_service = self.create_service(
            GetRobotStatus,
            '/get_manipulator_status',
            self.get_status_callback,
        )
        self.reset_service = self.create_service(
            Trigger,
            '/reset_manipulator_controller',
            self.reset_callback,
        )
        self.command_subscription = None
        self.execution = ControllerAction(
            self, Manipulate, '/manipulate', self.command_callback,
            self.validate_action_goal, self.manipulation_feedback, self.stop_for_cancel, defer=True)
        numeric = ['max_joint_speed', 'min_segment_time', 'joint_tolerance',
                   'attachment_timeout', 'grasp_reach', 'reach_tolerance']
        validate_startup(self, {name: positive for name in numeric})
        freeze_parameters(self, numeric + [
            'arm_timeout_margin', 'gripper_timeout', 'startup_timeout',
            'joint_names', 'home_joints', 'fixed_joint1', 'clearance_joints',
            'grasp_joints', 'place_joints', 'joint_lower_limits', 'joint_upper_limits',
            'joint_limit_margin', 'use_sim_attachment', 'arm_topic', 'gripper_action',
            'joint_states_topic', 'arm_base_frame', 'gripper_open_position',
            'gripper_closed_position', 'gripper_max_effort', 'verify_grasp',
            'grasp_detect_margin'])

        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info(
            'Manipulator Controller started. Waiting for {}, {} and /joint_states.'.format(
                self.get_parameter('arm_topic').value,
                self.get_parameter('gripper_action').value,
            )
        )

    def now_seconds(self):
        return self.get_clock().now().nanoseconds / 1e9

    def joint_state_callback(self, message):
        for name, position in zip(message.name, message.position):
            self.joint_positions[name] = position

    def current_arm_joints(self):
        joints = []
        for name in self.joint_names:
            if name not in self.joint_positions:
                return None
            joints.append(self.joint_positions[name])
        return joints

    def control_loop(self):
        if self.execution.tick():
            return
        if self.status == self.STARTING:
            self.check_startup()
        elif self.status == self.EXECUTING:
            try:
                self.run_current_step()
            except StepFailure as error:
                self.finish(False, str(error))

    def check_startup(self):
        arm_ready = self.arm_publisher.get_subscription_count() > 0
        gripper_ready = self.gripper_client.server_is_ready()
        joints_ready = self.current_arm_joints() is not None

        if arm_ready and gripper_ready and joints_ready:
            self.current_action = 'STARTUP_HOME'
            self.current_command = None
            self.start_steps([
                sequence.step('OPEN_GRIPPER', sequence.GRIPPER, sequence.OPEN),
                sequence.step('MOVE_HOME', sequence.ARM, [self.home]),
            ])
            return

        if self.now_seconds() - self.started_at > self.STARTUP_TIMEOUT:
            self.get_logger().error(
                'Startup failed (arm controller ready: {}, gripper controller ready: {}, '
                'joint states received: {}). Manipulator Controller is in ERROR state.'.format(
                    arm_ready, gripper_ready, joints_ready
                )
            )
            self.status = self.ERROR
            self.listen_for_commands()

    def listen_for_commands(self):
        # Mirror original readiness: expose the server only after startup ends.
        self.execution.activate()
        self.get_logger().info('Manipulator is {} on /manipulate.'.format(self.status))

    def validate_action_goal(self, message):
        try:
            self.validate_command(message)
        except StepFailure as error:
            raise ValueError(str(error))
        if not all(math.isfinite(v) for v in (message.target_x, message.target_y)):
            raise ValueError('nonfinite target')

    def manipulation_feedback(self):
        name = self.steps[self.step_index]['name'] if self.step_index < len(self.steps) else 'FINISHING'
        return Manipulate.Feedback(current_step=name, completed_steps=self.step_index,
                                   total_steps=len(self.steps))

    def stop_for_cancel(self):
        # Hold the measured joints, never open the fingers or release an object.
        if not self.cancel_hold_sent:
            joints = self.current_arm_joints()
            if joints is None or not all(math.isfinite(v) for v in joints):
                self.status = self.ERROR
                return False
            hold = JointTrajectory()
            hold.joint_names = self.joint_names
            hold.points = [JointTrajectoryPoint(positions=list(joints),
                                                time_from_start=Duration(sec=0, nanosec=100000000))]
            self.arm_publisher.publish(hold)
            self.cancel_hold_sent = True
            self.cancel_hold_until = time.monotonic() + 0.2
        if time.monotonic() < self.cancel_hold_until:
            return False
        # A nested goal may be awaiting acceptance when task cancellation arrives.
        if self.gripper_goal_future is not None:
            if not self.gripper_goal_future.done():
                return False
            if self.gripper_handle is None and self.gripper_result is None:
                # The response can be ready before its executor callback runs.
                self.gripper_goal_response(self.gripper_goal_future)
        if self.gripper_handle is not None and self.gripper_result is None:
            if self.gripper_cancel_future is None:
                self.gripper_cancel_future = self.gripper_handle.cancel_goal_async()
            return False  # wait for terminal gripper result, not just cancel ACK
        if self.attachment_future is not None and not self.attachment_future.done():
            return False  # callback preserves confirmed physical possession
        self.steps = []
        self.step_index = 0
        self.step_started = False
        self.arm_goal = None
        self.arm_motion_ends_at = None
        self.current_command = None
        self.current_action = None
        self.action_started_at = None
        # Physical grasp evidence is ambiguous if interrupted without attachment.
        self.status = self.ERROR
        return True

    def command_callback(self, message):
        label = message.action_label or message.action_type.upper()

        if self.status == self.ERROR:
            self.get_logger().error('Manipulator is in ERROR state. {} rejected.'.format(label))
            self.publish_result(False)
            return

        if self.status == self.EXECUTING:
            self.get_logger().warning(
                'Already executing {}. {} ignored.'.format(self.current_action, label)
            )
            return

        self.get_logger().info('Received {} for object "{}".'.format(label, message.object_name))
        self.current_action = label
        self.current_command = message

        try:
            self.validate_command(message)
            target = self.target_in_arm_frame(message)
            self.check_reach(target)
            fixed_joint1 = self.get_parameter('fixed_joint1').value
            clearance = sequence.arm_configuration(
                fixed_joint1, self.get_parameter('clearance_joints').value
            )
            use_attachment = self.get_parameter('use_sim_attachment').value
            if message.action_type == 'pick':
                grasp = sequence.arm_configuration(
                    fixed_joint1, self.get_parameter('grasp_joints').value
                )
                steps = sequence.pick_steps(clearance, grasp, self.home, use_attachment)
            else:
                release = sequence.arm_configuration(
                    fixed_joint1, self.get_parameter('place_joints').value
                )
                steps = sequence.place_steps(clearance, release, self.home, use_attachment)
            # Validate the complete motion before opening or attaching anything.
            for current in steps:
                if current['kind'] == sequence.ARM:
                    self.validate_points(current['value'])
        except (StepFailure, sequence.ManipulationError) as error:
            self.status = self.EXECUTING
            self.finish(False, str(error))
            return

        self.get_logger().info(
            '{}: object at x={:.3f} y={:.3f} in {}; using calibrated clearance path '
            '({} continuous2d waypoints retained as plan metadata).'.format(
                label,
                target[0],
                target[1],
                self.get_parameter('arm_base_frame').value,
                len(message.trajectory),
            )
        )
        self.start_steps(steps)

    def validate_command(self, message):
        if message.action_type not in ('pick', 'place'):
            raise StepFailure('unknown manipulation type "{}"'.format(message.action_type))
        if not message.object_name:
            raise StepFailure('command has no object name')
        if not message.frame_id:
            raise StepFailure('command has no target frame')
        if len(message.arm_goal) != 3 or len(message.arm_start) != 3:
            raise StepFailure('planner arm configuration must have 3 joints')
        if not message.trajectory:
            raise StepFailure('planner arm trajectory is empty')
        if message.action_type == 'pick' and self.held_object is not None:
            raise StepFailure('gripper already holds "{}"'.format(self.held_object))
        if message.action_type == 'place' and self.held_object != message.object_name:
            raise StepFailure('cannot place "{}": gripper holds "{}"'.format(
                message.object_name, self.held_object or 'nothing'
            ))

    def target_in_arm_frame(self, message):
        arm_frame = self.get_parameter('arm_base_frame').value
        try:
            transform = self.tf_buffer.lookup_transform(arm_frame, message.frame_id, Time())
        except TransformException as error:
            raise StepFailure('TF {} -> {} unavailable: {}'.format(
                message.frame_id, arm_frame, error
            ))

        point = PointStamped()
        point.header.frame_id = message.frame_id
        point.point.x = message.target_x
        point.point.y = message.target_y
        point.point.z = 0.0

        result = do_transform_point(point, transform)
        return result.point.x, result.point.y

    def check_reach(self, target):
        x, y = target
        reach = math.sqrt(x * x + y * y)
        expected = self.get_parameter('grasp_reach').value
        tolerance = self.get_parameter('reach_tolerance').value

        if abs(reach - expected) > tolerance:
            raise StepFailure(
                'object is {:.3f} m from the arm, expected {:.3f} +/- {:.3f} m'.format(
                    reach, expected, tolerance
                )
            )

    def start_steps(self, steps):
        self.cancel_hold_sent = False
        self.steps = steps
        self.step_index = 0
        self.step_started = False
        self.status = self.EXECUTING
        self.action_started_at = self.get_clock().now()

    def run_current_step(self):
        if self.step_index >= len(self.steps):
            self.finish(True, '')
            return

        current = self.steps[self.step_index]

        if not self.step_started:
            self.get_logger().info('[{}] {}'.format(self.current_action, current['name']))
            if current['kind'] == sequence.ARM:
                self.send_arm(current['value'])
            elif current['kind'] == sequence.ATTACHMENT:
                self.send_attachment(current['value'])
            else:
                self.send_gripper(current['value'])
            self.step_started = True
            return

        if current['kind'] == sequence.ARM:
            done = self.arm_reached()
        elif current['kind'] == sequence.ATTACHMENT:
            done = self.attachment_finished()
        else:
            done = self.gripper_finished(current['value'])

        if done:
            self.step_index += 1
            self.step_started = False
            if self.step_index >= len(self.steps):
                self.finish(True, '')
        elif self.now_seconds() > self.step_deadline:
            raise StepFailure('{} timed out'.format(current['name']))

    def send_attachment(self, operation):
        obj = self.current_command.object_name
        service = '/{}/{}'.format(obj, operation)
        if service not in self.attachment_clients:
            self.attachment_clients[service] = self.create_client(Trigger, service)
        self.attachment_client = self.attachment_clients[service]
        self.attachment_operation = operation
        self.attachment_object = obj
        self.attachment_future = None
        self.step_deadline = self.now_seconds() + self.get_parameter('attachment_timeout').value

    def attachment_response(self, future, operation, obj):
        # Keep physical possession accurate even if a later arm step fails or
        # an acknowledgement arrives after the controller's timeout.
        try:
            response = future.result()
        except Exception:
            return
        if response is not None and response.success:
            self.held_object = obj if operation == sequence.ATTACH else None

    def attachment_finished(self):
        if self.attachment_future is None:
            # DDS discovery is asynchronous for a newly created client. Wait
            # without blocking the node or treating discovery latency as failure.
            if self.attachment_client.service_is_ready():
                obj = self.attachment_object
                operation = self.attachment_operation
                self.attachment_future = self.attachment_client.call_async(Trigger.Request())
                self.attachment_future.add_done_callback(
                    lambda future: self.attachment_response(future, operation, obj)
                )
            elif self.now_seconds() > self.step_deadline:
                raise StepFailure(
                    'attachment service unavailable; build robot_object_attachment, '
                    'source the workspace and respawn the cube'
                )
            return False
        if not self.attachment_future.done():
            return False
        try:
            response = self.attachment_future.result()
        except Exception as error:
            raise StepFailure('attachment service failed: {}'.format(error))
        if response is None or not response.success:
            reason = response.message if response is not None else 'empty response'
            raise StepFailure('attachment failed: {}'.format(reason))
        # The executor may schedule a future's done callback after this timer.
        # Apply the acknowledgement here too before advancing to close/lift.
        if self.attachment_operation is not None:
            self.held_object = (
                self.attachment_object if self.attachment_operation == sequence.ATTACH else None
            )
        self.get_logger().info(response.message)
        return True

    def validate_points(self, points):
        lower = list(self.get_parameter('joint_lower_limits').value)
        upper = list(self.get_parameter('joint_upper_limits').value)
        margin = float(self.get_parameter('joint_limit_margin').value)
        try:
            sequence.validate_arm_points(points, lower, upper, margin)
        except sequence.ManipulationError as error:
            raise StepFailure(str(error))

    def send_arm(self, points):
        self.validate_points(points)
        trajectory = JointTrajectory()
        trajectory.joint_names = self.joint_names

        previous = self.current_arm_joints()
        if previous is None or not all(math.isfinite(v) for v in previous):
            raise StepFailure('finite arm joint feedback is required before moving')
        min_time = self.get_parameter('min_segment_time').value / len(points)
        elapsed = 0.0

        for joints in points:
            try:
                elapsed += sequence.segment_duration(
                    previous,
                    joints,
                    self.get_parameter('max_joint_speed').value,
                    min_time,
                )
            except sequence.ManipulationError as error:
                raise StepFailure(str(error))
            previous = joints

            point = JointTrajectoryPoint()
            point.positions = [float(value) for value in joints]
            point.time_from_start = Duration(
                sec=int(elapsed),
                nanosec=int((elapsed % 1.0) * 1e9),
            )
            trajectory.points.append(point)

        self.arm_publisher.publish(trajectory)
        self.arm_goal = points[-1]
        self.arm_motion_ends_at = self.now_seconds() + elapsed
        self.step_deadline = (
            self.arm_motion_ends_at + self.ARM_TIMEOUT_MARGIN
        )

    def arm_reached(self):
        # The endpoint can already be near the arm while an earlier part of the
        # trajectory is still running. Do not replace that trajectory early.
        if self.arm_motion_ends_at is None or self.now_seconds() < self.arm_motion_ends_at:
            return False
        joints = self.current_arm_joints()
        if joints is None or not all(math.isfinite(v) for v in joints):
            return False
        tolerance = self.get_parameter('joint_tolerance').value
        for current, goal in zip(joints, self.arm_goal):
            if abs(current - goal) > tolerance:
                return False
        return True

    def send_gripper(self, command):
        if not self.gripper_client.server_is_ready():
            raise StepFailure('gripper action server is not available')

        goal = GripperCommand.Goal()
        if command == sequence.OPEN:
            goal.command.position = self.get_parameter('gripper_open_position').value
        else:
            goal.command.position = self.get_parameter('gripper_closed_position').value
        goal.command.max_effort = self.get_parameter('gripper_max_effort').value

        self.gripper_result = None
        self.step_deadline = self.now_seconds() + self.GRIPPER_TIMEOUT

        self.gripper_handle = None
        self.gripper_cancel_future = None
        future = self.gripper_client.send_goal_async(goal)
        self.gripper_goal_future = future
        future.add_done_callback(self.gripper_goal_response)

    def gripper_goal_response(self, future):
        if self.gripper_handle is not None or self.gripper_result is not None:
            return  # response already consumed by the cancellation path
        try:
            handle = future.result()
        except Exception:
            self.gripper_result = 'rejected'
            return
        self.gripper_handle = handle
        if not handle.accepted:
            self.gripper_result = 'rejected'
            return
        result_future = handle.get_result_async()
        result_future.add_done_callback(self.gripper_result_callback)

    def gripper_result_callback(self, future):
        try:
            self.gripper_result = future.result()
        except Exception:
            self.gripper_result = 'rejected'

    def gripper_finished(self, command):
        if self.gripper_result is None:
            return False
        if self.gripper_result == 'rejected':
            raise StepFailure('gripper goal was rejected')

        status = self.gripper_result.status
        if status not in (GoalStatus.STATUS_SUCCEEDED, GoalStatus.STATUS_ABORTED):
            raise StepFailure('gripper goal finished with status {}'.format(status))
        if self.get_parameter('use_sim_attachment').value and status != GoalStatus.STATUS_SUCCEEDED:
            raise StepFailure('simulated gripper goal did not succeed')

        position = self.gripper_result.result.position
        self.get_logger().info('Gripper {} -> position {:.4f}'.format(command, position))

        closed = self.get_parameter('gripper_closed_position').value
        margin = self.get_parameter('grasp_detect_margin').value
        if (
            command == sequence.CLOSE
            and self.get_parameter('verify_grasp').value
            and not (
                self.get_parameter('use_sim_attachment').value
                and self.held_object is not None
            )
            and position <= closed + margin
        ):
            raise StepFailure('gripper closed completely; no object was grasped')
        return True

    def finish(self, success, reason):
        label = self.current_action
        message = self.current_command
        step_name = 'VALIDATION'
        if self.step_index < len(self.steps):
            step_name = self.steps[self.step_index]['name']

        self.steps = []
        self.step_index = 0
        self.step_started = False
        self.arm_goal = None
        self.arm_motion_ends_at = None

        if success:
            self.status = self.IDLE
            self.current_action = None
            self.action_started_at = None
            self.get_logger().info('Completed {}.'.format(label))
        else:
            self.status = self.ERROR
            self.get_logger().error('{} failed at {}: {}'.format(label, step_name, reason))

        if message is None:
            if not success:
                self.execution.request_stop(reason)
            self.listen_for_commands()
            return

        if success and not self.get_parameter('use_sim_attachment').value:
            if message.action_type == 'pick':
                self.held_object = message.object_name
            else:
                self.held_object = None

        self.current_command = None
        self.last_failure_reason = reason
        self.publish_result(success)

    def publish_result(self, success, message=''):
        reason = message or (getattr(self, 'last_failure_reason', '') if not success else '')
        self.execution.complete(success, reason or ('completed' if success else 'manipulation failed'))

    def elapsed_seconds(self):
        if self.action_started_at is None:
            return 0.0
        return (self.get_clock().now() - self.action_started_at).nanoseconds / 1e9

    def get_status_callback(self, request, response):
        response.status = self.status
        if self.status == self.EXECUTING and self.step_index < len(self.steps):
            response.current_action = '{} [{}]'.format(
                self.current_action, self.steps[self.step_index]['name']
            )
        else:
            response.current_action = self.current_action or 'NONE'
        response.elapsed_time = self.elapsed_seconds()
        return response

    def reset_callback(self, request, response):
        if ((self.gripper_goal_future is not None and not self.gripper_goal_future.done())
                or (self.gripper_handle is not None and self.gripper_result is None)):
            response.success = False
            response.message = 'Gripper goal/result pending; wait before resetting.'
            return response
        if self.status == self.EXECUTING:
            response.success = False
            response.message = 'Cannot reset while executing.'
            return response

        if self.attachment_future is not None and not self.attachment_future.done():
            response.success = False
            response.message = 'Attachment response pending; wait before resetting.'
            return response

        if not self.execution.reset():
            response.success = False
            response.message = 'An action result is still pending'
            return response
        previous = self.status
        self.cancel_hold_sent = False
        self.status = self.IDLE
        self.current_action = None
        self.current_command = None
        self.action_started_at = None
        if not self.get_parameter('use_sim_attachment').value:
            self.held_object = None
        self.listen_for_commands()

        response.success = True
        response.message = 'Manipulator Controller reset from {} to IDLE.'.format(previous)
        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ManipulatorController()
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

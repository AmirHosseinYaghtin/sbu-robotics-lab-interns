import rclpy
import math
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import Bool
from std_msgs.msg import String
from std_srvs.srv import Trigger
from robot_task_interfaces.srv import GetRobotStatus
from robot_task_interfaces.msg import MoveCommand
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


class RobotController(Node):

    IDLE = 'IDLE'
    EXECUTING = 'EXECUTING'
    ERROR = 'ERROR'

    WAYPOINT_TOL = 0.1
    GOAL_THETA_TOL = 0.1
    MAX_MOVE_TIME = 180.0
    ODOM_TIMEOUT = 5.0
    INITIAL_ODOM_TIMEOUT = 120.0
    ODOM_WARN_INTERVAL = 10.0
    STUCK_TIME = 20.0
    STUCK_DIST = 0.05

    def __init__(self):
        super().__init__('robot_controller')

        self.status = self.IDLE
        self.current_action = None
        self.action_started_at = None
        self.operation_timer = None

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

        self.reset_service = self.create_service(
            Trigger,
            '/reset_robot_controller',
            self.reset_callback
        )

        self.get_logger().info(
            'Robot Controller node has started.'
        )

        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.odom_subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.current_x = None
        self.current_y = None
        self.current_yaw = None

        self.target_x = None
        self.target_y = None
        self.moving = False

        self.control_timer = self.create_timer(
            0.1,
            self.control_loop
        )

        self.trajectory = []
        self.waypoint_index = 0

        self.move_command_subscription = self.create_subscription(
            MoveCommand,
            '/move_command',
            self.move_command_callback,
            10
        )

        self.final_theta = None
        self.rotating_final = False
        self.last_odom_time = None
        self.move_deadline = None
        self.odom_deadline = None
        self.odom_warn_deadline = None
        self.progress_ref_x = None
        self.progress_ref_y = None
        self.progress_deadline = None

    def move_command_callback(self, message):
        label = message.action_label

        if self.status == self.ERROR:
            self.get_logger().warning(
                'Robot is in ERROR state. Move ignored.'
            )
            return

        if self.status == self.EXECUTING:
            self.get_logger().warning(
                f'Robot is already executing '
                f'{self.current_action}. Move ignored.'
            )
            return

        trajectory = [
            (waypoint.x, waypoint.y, waypoint.theta)
            for waypoint in message.waypoints
        ]

        self.get_logger().info(
            f'Received MOVE_BASE "{label}" with '
            f'{len(trajectory)} waypoints.'
        )

        if not trajectory:
            self.current_action = label
            self.action_started_at = self.get_clock().now()
            self.status = self.ERROR
            self.get_logger().error(
                f'MOVE_BASE "{label}" has no waypoints. '
                f'Robot entered ERROR state.'
            )
            self.publish_action_result(False)
            return

        self.start_trajectory(label, trajectory)

    def start_trajectory(self, action, trajectory):
        if not trajectory:
            return

        self.status = self.EXECUTING
        self.current_action = action
        self.action_started_at = self.get_clock().now()

        self.trajectory = trajectory
        self.waypoint_index = 0

        self.final_theta = trajectory[-1][2]
        self.rotating_final = False

        self.target_x = trajectory[0][0]
        self.target_y = trajectory[0][1]

        self.moving = True

        now = self.get_clock().now()
        self.move_deadline = now + Duration(seconds=self.MAX_MOVE_TIME)
        self.odom_deadline = now + Duration(seconds=self.INITIAL_ODOM_TIMEOUT)
        self.odom_warn_deadline = now + Duration(
            seconds=self.ODOM_WARN_INTERVAL
        )
        self.progress_ref_x = None
        self.progress_ref_y = None
        self.progress_deadline = now + Duration(seconds=self.STUCK_TIME)

    def normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi

        while angle < -math.pi:
            angle += 2.0 * math.pi

        return angle

    def fail_move(self, reason):
        self.moving = False
        self.rotating_final = False
        self.cmd_vel_publisher.publish(Twist())

        failed_action = self.current_action
        self.status = self.ERROR

        self.get_logger().error(
            f'Move "{failed_action}" failed: {reason}. Robot stopped.'
        )

        self.publish_action_result(False)

    def control_loop(self):
        if not self.moving:
            return

        now = self.get_clock().now()

        if self.move_deadline is not None and now > self.move_deadline:
            self.fail_move('movement timeout')
            return

        if self.last_odom_time is None:
            if self.odom_deadline is not None and now > self.odom_deadline:
                self.fail_move('no /odom received')
            elif (self.odom_warn_deadline is None
                    or now > self.odom_warn_deadline):
                self.get_logger().warning(
                    'Still waiting for the first /odom message '
                    '(is Gazebo finished starting?).'
                )
                self.odom_warn_deadline = now + Duration(
                    seconds=self.ODOM_WARN_INTERVAL
                )
            return
        if (now - self.last_odom_time) > Duration(seconds=self.ODOM_TIMEOUT):
            self.fail_move('/odom feed lost')
            return

        if self.current_x is None or self.current_yaw is None:
            return

        command = Twist()

        if self.rotating_final:
            yaw_error = self.normalize_angle(
                self.final_theta - self.current_yaw
            )

            if abs(yaw_error) < self.GOAL_THETA_TOL:
                self.moving = False
                self.rotating_final = False
                self.cmd_vel_publisher.publish(command)
                self.complete_current_action()
                return

            turn = 0.6 * yaw_error
            if 0.0 <= turn < 0.15:
                turn = 0.15
            elif -0.15 < turn < 0.0:
                turn = -0.15
            command.angular.z = max(-0.8, min(0.8, turn))

            self.cmd_vel_publisher.publish(command)
            return

        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y

        distance = math.sqrt(dx * dx + dy * dy)

        target_yaw = math.atan2(dy, dx)
        angle_error = self.normalize_angle(
            target_yaw - self.current_yaw
        )

        if self.progress_ref_x is None:
            self.progress_ref_x = self.current_x
            self.progress_ref_y = self.current_y
            self.progress_deadline = now + Duration(seconds=self.STUCK_TIME)
        else:
            moved = math.hypot(
                self.current_x - self.progress_ref_x,
                self.current_y - self.progress_ref_y,
            )
            if moved > self.STUCK_DIST:
                self.progress_ref_x = self.current_x
                self.progress_ref_y = self.current_y
                self.progress_deadline = (
                    now + Duration(seconds=self.STUCK_TIME)
                )
            elif (
                self.progress_deadline is not None
                and now > self.progress_deadline
            ):
                self.fail_move('robot is stuck (no progress)')
                return

        if distance < self.WAYPOINT_TOL:
            self.waypoint_index += 1

            if self.waypoint_index < len(self.trajectory):
                self.target_x = self.trajectory[self.waypoint_index][0]
                self.target_y = self.trajectory[self.waypoint_index][1]
                return

            self.cmd_vel_publisher.publish(command)
            if self.final_theta is None:
                self.moving = False
                self.complete_current_action()
            else:
                self.rotating_final = True
            return

        if abs(angle_error) > 0.15:
            command.angular.z = 0.5 * angle_error
        else:
            command.linear.x = 0.15
            command.angular.z = 0.3 * angle_error

        self.cmd_vel_publisher.publish(command)

    def odom_callback(self, message):
        self.current_x = message.pose.pose.position.x
        self.current_y = message.pose.pose.position.y

        q = message.pose.pose.orientation

        self.current_yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )

        self.last_odom_time = self.get_clock().now()

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

        if action.startswith('PICK'):
            self.start_action(action=action, duration=3.0)
            return

        if action.startswith('PLACE'):
            self.start_action(action=action, duration=2.0)
            return

        self.status = self.ERROR
        self.current_action = action

        self.get_logger().error(
            f'Unknown action: {action}. '
            f'Robot entered ERROR state.'
        )

        self.publish_action_result(False)

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

    def reset_callback(self, request, response):
        self.moving = False
        self.rotating_final = False
        self.cmd_vel_publisher.publish(Twist())

        if self.operation_timer is not None:
            self.operation_timer.cancel()
            self.destroy_timer(self.operation_timer)
            self.operation_timer = None

        previous = self.status

        self.status = self.IDLE
        self.current_action = None
        self.action_started_at = None
        self.trajectory = []
        self.waypoint_index = 0
        self.final_theta = None
        self.move_deadline = None
        self.odom_deadline = None
        self.odom_warn_deadline = None
        self.progress_ref_x = None
        self.progress_ref_y = None
        self.progress_deadline = None

        response.success = True
        response.message = (
            'Robot Controller reset from {} to IDLE.'.format(previous)
        )

        self.get_logger().info(
            'Robot Controller was reset from {} to IDLE.'.format(previous)
        )

        return response


def main(args=None):
    rclpy.init(args=args)

    node = RobotController()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

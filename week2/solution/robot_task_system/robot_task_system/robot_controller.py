import rclpy
import math
from rclpy.node import Node
from std_msgs.msg import Bool
from std_msgs.msg import String
from robot_task_interfaces.srv import GetRobotStatus
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

class RobotController(Node):

    IDLE = 'IDLE'
    EXECUTING = 'EXECUTING'
    ERROR = 'ERROR'

    def __init__(self):
        super().__init__('robot_controller')

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

    def start_trajectory(self, action, trajectory):
        if not trajectory:
            return

        self.status = self.EXECUTING
        self.current_action = action
        self.action_started_at = self.get_clock().now()

        self.trajectory = trajectory
        self.waypoint_index = 0

        self.target_x = trajectory[0][0]
        self.target_y = trajectory[0][1]

        self.moving = True

    def normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi

        while angle < -math.pi:
            angle += 2.0 * math.pi

        return angle
    
    def control_loop(self):
        if not self.moving:
            return

        if self.current_x is None or self.current_yaw is None:
            return

        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y

        distance = math.sqrt(dx * dx + dy * dy)

        target_yaw = math.atan2(dy, dx)
        angle_error = self.normalize_angle(
            target_yaw - self.current_yaw
        )

        command = Twist()

        if distance < 0.1:
            self.waypoint_index += 1

            if self.waypoint_index < len(self.trajectory):
                self.target_x = self.trajectory[self.waypoint_index][0]
                self.target_y = self.trajectory[self.waypoint_index][1]
                return

            self.moving = False
            self.cmd_vel_publisher.publish(command)
            self.complete_current_action()
            return

        if abs(angle_error) > 0.15:
            command.angular.z = 0.5 * angle_error
        else:
            command.linear.x = 0.15
            command.angular.z = 0.3 * angle_error

        self.cmd_vel_publisher.publish(command)
    
    def start_move(self, action, target_x, target_y):
        self.status = self.EXECUTING
        self.current_action = action
        self.action_started_at = self.get_clock().now()

        self.target_x = target_x
        self.target_y = target_y
        self.moving = True

        self.get_logger().info(
            f'Starting move: {action} '
            f'to ({target_x:.2f}, {target_y:.2f})'
        )
    
    def odom_callback(self, message):
        self.current_x = message.pose.pose.position.x
        self.current_y = message.pose.pose.position.y

        q = message.pose.pose.orientation

        self.current_yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z)
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

    node = RobotController()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

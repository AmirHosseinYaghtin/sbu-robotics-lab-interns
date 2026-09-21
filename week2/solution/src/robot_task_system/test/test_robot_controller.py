import math

import pytest
import rclpy
from std_msgs.msg import String

from robot_task_interfaces.srv import GetRobotStatus
from robot_task_interfaces.msg import MoveCommand, Waypoint
from robot_task_system.robot_controller import RobotController


@pytest.fixture
def ros():
    rclpy.init()
    yield
    rclpy.shutdown()


def test_initial_status_is_idle(ros):
    node = RobotController()
    try:
        request = GetRobotStatus.Request()
        response = GetRobotStatus.Response()

        result = node.get_robot_status_callback(request, response)

        assert result.status == 'IDLE'
        assert result.current_action == 'NONE'
        assert result.elapsed_time == 0.0
    finally:
        node.destroy_node()


def test_pick_action_sets_executing(ros):
    node = RobotController()
    try:
        message = String()
        message.data = 'PICK_box'

        node.action_callback(message)

        assert node.status == 'EXECUTING'
        assert node.current_action == 'PICK_box'
    finally:
        node.destroy_node()


def test_planner_pick_label_is_simulated(ros):
    node = RobotController()
    try:
        message = String()
        message.data = 'PICK_cube1'

        node.action_callback(message)

        assert node.status == 'EXECUTING'
        assert node.current_action == 'PICK_cube1'
    finally:
        node.destroy_node()


def test_invalid_action_sets_error(ros):
    node = RobotController()
    try:
        message = String()
        message.data = 'FLY_TO_MARS'

        node.action_callback(message)

        assert node.status == 'ERROR'
    finally:
        node.destroy_node()


def test_normalize_angle_wraps_into_pi_range(ros):
    node = RobotController()
    try:
        assert node.normalize_angle(0.0) == pytest.approx(0.0)
        assert node.normalize_angle(3.0 * math.pi) == pytest.approx(math.pi)
        assert node.normalize_angle(-3.0 * math.pi) == pytest.approx(-math.pi)
        wrapped = node.normalize_angle(1.5 * math.pi)
        assert -math.pi <= wrapped <= math.pi
    finally:
        node.destroy_node()


def test_trajectory_keeps_theta(ros):
    node = RobotController()
    try:
        command = MoveCommand()
        command.action_label = 'MOVE_BASE'
        command.waypoints = [
            Waypoint(x=0.0, y=0.0, theta=0.0),
            Waypoint(x=1.0, y=0.0, theta=0.5),
            Waypoint(x=1.0, y=1.0, theta=1.25),
        ]

        node.move_command_callback(command)

        assert node.status == 'EXECUTING'
        assert node.moving is True
        assert len(node.trajectory) == 3
        assert node.trajectory[1] == pytest.approx((1.0, 0.0, 0.5))
        assert node.final_theta == pytest.approx(1.25)
    finally:
        node.destroy_node()


def test_empty_trajectory_is_a_failure(ros):
    node = RobotController()
    try:
        command = MoveCommand()
        command.action_label = 'MOVE_BASE'
        command.waypoints = []

        node.move_command_callback(command)

        assert node.status == 'ERROR'
        assert node.moving is False
    finally:
        node.destroy_node()

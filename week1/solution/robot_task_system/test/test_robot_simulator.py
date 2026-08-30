import pytest
import rclpy
from std_msgs.msg import String

from robot_task_interfaces.srv import GetRobotStatus
from robot_task_system.robot_simulator import RobotSimulator


@pytest.fixture
def ros():
    rclpy.init()
    yield
    rclpy.shutdown()


def test_initial_status_is_idle(ros):
    node = RobotSimulator()
    try:
        request = GetRobotStatus.Request()
        response = GetRobotStatus.Response()

        result = node.get_robot_status_callback(request, response)

        assert result.status == 'IDLE'
        assert result.current_action == 'NONE'
        assert result.elapsed_time == 0.0
    finally:
        node.destroy_node()


def test_valid_action_sets_executing(ros):
    node = RobotSimulator()
    try:
        message = String()
        message.data = 'PICK_OBJECT'

        node.action_callback(message)

        assert node.status == 'EXECUTING'
        assert node.current_action == 'PICK_OBJECT'

        # The status service should now report EXECUTING as well.
        response = node.get_robot_status_callback(
            GetRobotStatus.Request(),
            GetRobotStatus.Response(),
        )
        assert response.status == 'EXECUTING'
        assert response.current_action == 'PICK_OBJECT'
        assert response.elapsed_time >= 0.0
    finally:
        node.destroy_node()


def test_invalid_action_sets_error(ros):
    node = RobotSimulator()
    try:
        message = String()
        message.data = 'FLY_TO_MARS'

        node.action_callback(message)

        assert node.status == 'ERROR'
    finally:
        node.destroy_node()

import pytest
import rclpy
from std_msgs.msg import Bool

from robot_task_system.task_controller import TaskController


@pytest.fixture
def ros():
    rclpy.init()
    yield
    rclpy.shutdown()


def test_queue_starts_with_four_actions(ros):
    node = TaskController()
    try:
        assert len(node.action_queue) == 4
        assert node.action_queue[0] == 'MOVE_TO_WORKSTATION'
        assert node.queue_stopped is False
    finally:
        node.destroy_node()


def test_successful_result_pops_one_action(ros):
    node = TaskController()
    try:
        node.waiting_for_result = True
        node.current_action = node.action_queue[0]

        result = Bool()
        result.data = True

        node.action_done_callback(result)

        assert len(node.action_queue) == 3
        assert node.waiting_for_result is False
        assert node.queue_stopped is False
    finally:
        node.destroy_node()


def test_failed_result_stops_the_queue(ros):
    node = TaskController()
    try:
        node.waiting_for_result = True
        node.current_action = node.action_queue[0]

        result = Bool()
        result.data = False

        node.action_done_callback(result)

        assert node.queue_stopped is True
        assert len(node.action_queue) == 4
    finally:
        node.destroy_node()

import pytest
from robot_task_system.task_controller import TaskController


def test_manipulator_command_carries_target_and_type():
    action = {
        'type': 'place',
        'label': 'PLACE_cube1',
        'obj': 'cube1',
        'grasp': None,
        'arm_start': [0.0, 0.0, 0.0],
        'arm_goal': [0.1, 0.2, 0.3],
        'arm_trajectory': [[0.0, 0.0, 0.0], [0.1, 0.2, 0.3]],
        'target_world': (-1.27, 1.25),
    }
    message = TaskController._build_manipulator_command(action, 'odom')
    assert message.action_type == 'place'
    assert message.frame_id == 'odom'
    assert message.target_x == pytest.approx(-1.27)
    assert message.target_y == pytest.approx(1.25)

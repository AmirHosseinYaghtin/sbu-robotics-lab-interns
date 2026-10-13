from robot_task_system.task_controller import TaskController


def test_build_manipulator_command():
    action = {
        'type': 'pick',
        'label': 'PICK_cube1',
        'obj': 'cube1',
        'grasp': {
            '__type__': 'Grasp',
            'obj': 'cube1',
            'dx': 0.1,
            'dy': 0.2,
            'dtheta': 0.3,
        },
        'arm_start': [0.0, 0.0, 0.0],
        'arm_goal': [0.4, 0.5, 0.6],
        'arm_trajectory': [
            [0.0, 0.0, 0.0],
            [0.2, 0.25, 0.3],
            [0.4, 0.5, 0.6],
        ],
    }

    message = TaskController._build_manipulator_command(action)

    assert message.action_label == 'PICK_cube1'
    assert message.object_name == 'cube1'

    assert message.grasp_dx == 0.1
    assert message.grasp_dy == 0.2
    assert message.grasp_dtheta == 0.3

    assert list(message.arm_start) == [0.0, 0.0, 0.0]
    assert list(message.arm_goal) == [0.4, 0.5, 0.6]

    assert len(message.trajectory) == 3
    assert list(message.trajectory[0].joints) == [0.0, 0.0, 0.0]
    assert list(message.trajectory[-1].joints) == [0.4, 0.5, 0.6]

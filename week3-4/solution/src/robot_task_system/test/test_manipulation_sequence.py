import pytest
from robot_task_system import manipulation_sequence as sequence

HOME = [0.0, -1.0, 0.3, 0.7]
TRAJECTORY = [[0.0, -1.0, 0.3, 0.7], [0.0, 0.5, -0.2, 1.0]]
GRASP = [0.0, 0.688, -0.058, 0.94]


def names(steps):
    return [s['name'] for s in steps]


def test_planner_joints_go_to_joint2_joint3_joint4():
    assert sequence.planner_to_arm(0.0, [0.5, -0.2, 1.0]) == [0.0, 0.5, -0.2, 1.0]


def test_wrong_planner_joint_count_raises():
    with pytest.raises(sequence.ManipulationError):
        sequence.planner_to_arm(0.0, [0.5, -0.2])


def test_planner_trajectory_keeps_every_waypoint():
    points = sequence.planner_trajectory(0.0, [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    assert points == [[0.0, 0.1, 0.2, 0.3], [0.0, 0.4, 0.5, 0.6]]


def test_empty_planner_trajectory_raises():
    with pytest.raises(sequence.ManipulationError):
        sequence.planner_trajectory(0.0, [])


def test_pick_sequence_order():
    steps = sequence.pick_steps(TRAJECTORY, GRASP, HOME)
    assert names(steps) == [
        'OPEN_GRIPPER', 'FOLLOW_PLANNER_TRAJECTORY', 'MOVE_GRASP',
        'CLOSE_GRIPPER', 'LIFT', 'MOVE_HOME',
    ]
    assert steps[1]['value'] == TRAJECTORY
    assert steps[2]['value'] == [GRASP]
    assert steps[3]['value'] == sequence.CLOSE
    assert steps[4]['value'] == [TRAJECTORY[-1]]


def test_place_sequence_order():
    steps = sequence.place_steps(TRAJECTORY, GRASP, HOME)
    assert names(steps) == [
        'FOLLOW_PLANNER_TRAJECTORY', 'MOVE_PLACE', 'OPEN_GRIPPER', 'RETREAT', 'MOVE_HOME',
    ]
    assert steps[1]['value'] == [GRASP]
    assert steps[2]['value'] == sequence.OPEN


def test_segment_duration_respects_speed_and_minimum():
    assert sequence.segment_duration([0, 0, 0, 0], [1.2, 0, 0, 0], 0.6, 1.0) == pytest.approx(2.0)
    assert sequence.segment_duration([0, 0, 0, 0], [0.1, 0, 0, 0], 0.6, 1.0) == pytest.approx(1.0)
    assert sequence.segment_duration(None, [0.1, 0, 0, 0], 0.6, 1.0) == pytest.approx(3.0)


def test_simulated_pick_attaches_before_closing_or_lifting():
    steps = sequence.pick_steps(TRAJECTORY, GRASP, HOME, use_attachment=True)
    assert names(steps) == [
        'OPEN_GRIPPER', 'FOLLOW_PLANNER_TRAJECTORY', 'MOVE_GRASP',
        'ATTACH_OBJECT', 'CLOSE_GRIPPER', 'LIFT', 'MOVE_HOME',
    ]


def test_simulated_place_opens_before_detaching_and_retreating():
    steps = sequence.place_steps(TRAJECTORY, GRASP, HOME, use_attachment=True)
    assert names(steps) == [
        'FOLLOW_PLANNER_TRAJECTORY', 'MOVE_PLACE', 'OPEN_GRIPPER',
        'DETACH_OBJECT', 'RETREAT', 'MOVE_HOME',
    ]

import math
from pathlib import Path

import pytest
from robot_task_system import manipulation_sequence as sequence
from robot_task_system import plan_parser
import yaml

HOME = [0.0, -1.0, 0.3, 0.7]
CLEARANCE = [0.0, 0.44, -0.38, 1.51]
GRASP = [0.0, 0.688, -0.058, 0.94]


def names(steps):
    return [s['name'] for s in steps]


def test_calibrated_pose_sets_fixed_base_and_pitch_joints():
    assert sequence.arm_configuration(0.0, [0.5, -0.2, 1.0]) == [0.0, 0.5, -0.2, 1.0]


def test_wrong_calibrated_joint_count_raises():
    with pytest.raises(sequence.ManipulationError):
        sequence.arm_configuration(0.0, [0.5, -0.2])


def test_pick_sequence_order():
    steps = sequence.pick_steps(CLEARANCE, GRASP, HOME)
    assert names(steps) == [
        'OPEN_GRIPPER', 'MOVE_CLEARANCE', 'MOVE_GRASP',
        'CLOSE_GRIPPER', 'LIFT', 'MOVE_HOME',
    ]
    assert steps[1]['value'] == [CLEARANCE]
    assert steps[2]['value'] == [GRASP]
    assert steps[3]['value'] == sequence.CLOSE
    assert steps[4]['value'] == [CLEARANCE]


def test_place_sequence_order():
    steps = sequence.place_steps(CLEARANCE, GRASP, HOME)
    assert names(steps) == [
        'MOVE_CLEARANCE', 'MOVE_PLACE', 'OPEN_GRIPPER', 'RETREAT', 'MOVE_HOME',
    ]
    assert steps[1]['value'] == [GRASP]
    assert steps[2]['value'] == sequence.OPEN
    assert steps[3]['value'] == [CLEARANCE]


def test_segment_duration_respects_speed_and_minimum():
    assert sequence.segment_duration([0, 0, 0, 0], [1.2, 0, 0, 0], 0.6, 1.0) == pytest.approx(2.0)
    assert sequence.segment_duration([0, 0, 0, 0], [0.1, 0, 0, 0], 0.6, 1.0) == pytest.approx(1.0)
    assert sequence.segment_duration(None, [0.1, 0, 0, 0], 0.6, 1.0) == pytest.approx(3.0)


def test_simulated_pick_attaches_before_closing_or_lifting():
    steps = sequence.pick_steps(CLEARANCE, GRASP, HOME, use_attachment=True)
    assert names(steps) == [
        'OPEN_GRIPPER', 'MOVE_CLEARANCE', 'MOVE_GRASP',
        'ATTACH_OBJECT', 'CLOSE_GRIPPER', 'LIFT', 'MOVE_HOME',
    ]


def test_simulated_place_opens_before_detaching_and_retreating():
    steps = sequence.place_steps(CLEARANCE, GRASP, HOME, use_attachment=True)
    assert names(steps) == [
        'MOVE_CLEARANCE', 'MOVE_PLACE', 'OPEN_GRIPPER',
        'DETACH_OBJECT', 'RETREAT', 'MOVE_HOME',
    ]


@pytest.mark.parametrize('value', [2.38, float('nan'), float('inf')])
def test_invalid_target_is_rejected_without_clamping(value):
    points = [[0.0, 0.5, 0.0, value]]
    with pytest.raises(sequence.ManipulationError, match='joint4'):
        sequence.validate_arm_points(points, [-2.0] * 4, [2.0] * 4, margin=0.02)
    if math.isfinite(value):
        assert points[0][-1] == value


@pytest.mark.parametrize('points, lower, upper, margin', [
    ([[0.0] * 4], [], [], 0.0),
    ([[0.0] * 3], [-1.0] * 4, [1.0] * 4, 0.0),
    ([], [-1.0] * 4, [1.0] * 4, 0.0),
    ([[0.0] * 4], [-1.0] * 4, [1.0] * 4, 1.0),
    ([[0.0] * 4], [-1.0] * 4, [1.0] * 4, -0.1),
])
def test_invalid_limits_and_waypoints_are_rejected(points, lower, upper, margin):
    with pytest.raises(sequence.ManipulationError):
        sequence.validate_arm_points(points, lower, upper, margin)


@pytest.mark.parametrize('speed', [0.0, -0.2, float('nan')])
def test_invalid_joint_speed_is_rejected(speed):
    with pytest.raises(sequence.ManipulationError):
        sequence.segment_duration(HOME, CLEARANCE, speed, 1.0)


def gripper_position(joints):
    # Joint origins/axes and end_effector offset in ROBOTIS's Humble URDF:
    # turtlebot3_manipulation_description/urdf/open_manipulator_x.urdf.xacro.
    # Independent FK checks the actual physical consequence of the waypoints.
    _, shoulder, elbow, wrist = joints
    pitch = shoulder + elbow + wrist
    x = (0.012 + 0.024 * math.cos(shoulder) + 0.128 * math.sin(shoulder)
         + 0.124 * math.cos(shoulder + elbow) + 0.126 * math.cos(pitch))
    z = (0.0765 - 0.024 * math.sin(shoulder) + 0.128 * math.cos(shoulder)
         - 0.124 * math.sin(shoulder + elbow) - 0.126 * math.sin(pitch))
    return x, z


@pytest.mark.parametrize('plan_name', [
    'plan_pick_place.json', 'plans/simple.json', 'plans/pick_place.json',
    'plans/corridor.json', 'plans/multi_object.json', 'plans/at_work.json',
])
def test_all_maps_use_forward_clearance_paths(plan_name):
    config = Path(__file__).resolve().parents[1] / 'config'
    params = yaml.safe_load((config / 'pick_place.yaml').read_text())
    params = params['manipulator_controller']['ros__parameters']
    clearance = sequence.arm_configuration(params['fixed_joint1'], params['clearance_joints'])
    _, actions = plan_parser.load_and_validate(str(config / plan_name))
    for action in actions:
        if action['type'] == 'move_base':
            continue
        pose_parameter = 'grasp_joints' if action['type'] == 'pick' else 'place_joints'
        pose = sequence.arm_configuration(params['fixed_joint1'], params[pose_parameter])
        build = sequence.pick_steps if action['type'] == 'pick' else sequence.place_steps
        steps = build(clearance, pose, params['home_joints'], use_attachment=True)
        previous = params['home_joints']
        for current in steps:
            if current['kind'] != sequence.ARM:
                continue
            for goal in current['value']:
                sequence.validate_arm_points(
                    [goal], params['joint_lower_limits'], params['joint_upper_limits'],
                    params['joint_limit_margin']
                )
                # Sample the positions-only controller's linear interpolation.
                for index in range(101):
                    t = index / 100.0
                    sample = [a + t * (b - a) for a, b in zip(previous, goal)]
                    x, z = gripper_position(sample)
                    assert x > 0.13, (action['label'], current['name'], sample)
                    assert z >= gripper_position(pose)[1] - 0.001
                previous = goal
        raised_x, raised_z = gripper_position(clearance)
        target_x, target_z = gripper_position(pose)
        assert abs(raised_x - target_x) < 0.005
        assert raised_z - target_z > 0.07

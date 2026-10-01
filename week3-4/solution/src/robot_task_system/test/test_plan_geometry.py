import math
import os

import pytest
from robot_task_system import plan_geometry
from robot_task_system import plan_parser

PLAN = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'config', 'plan_pick_place.json'
))


@pytest.fixture
def actions():
    return plan_parser.load_and_validate(PLAN)[1]


def test_planner_arm_goal_matches_object_pose(actions):
    prepared = plan_geometry.prepare_actions(actions, approach=False)
    for action in prepared:
        if action['type'] != 'move_base':
            assert action['consistency_error'] < 1e-3


def test_target_is_planner_object_position(actions):
    prepared = plan_geometry.prepare_actions(actions, approach=False)
    assert prepared[1]['target_world'] == pytest.approx((0.8, 0.0), abs=1e-3)


def test_approach_brings_object_within_reach(actions):
    reach, mount = 0.20, -0.092
    prepared = plan_geometry.prepare_actions(actions, grasp_reach=reach, arm_mount_x=mount)
    manipulations = [a for a in prepared if a['type'] != 'move_base']
    assert len(manipulations) == 2
    for action in manipulations:
        local = plan_geometry.world_to_local(action['base_conf'], action['target_world'])
        assert math.hypot(local[0] - mount, local[1]) == pytest.approx(reach, abs=1e-6)
        assert action['approach_shift'] > 0.0


def test_retreat_is_inserted_after_shifted_pick(actions):
    prepared = plan_geometry.prepare_actions(actions)
    labels = [a['label'] for a in prepared]
    assert labels == ['MOVE_BASE', 'PICK_cube1', 'RETREAT', 'MOVE_BASE', 'PLACE_cube1']
    retreat = prepared[2]
    assert retreat['reverse'] is True
    assert retreat['goal'] == pytest.approx(prepared[3]['waypoints'][0], abs=1e-9)


def test_local_and_world_are_inverse():
    base = (1.0, -2.0, 0.7)
    world = plan_geometry.local_to_world(base, (0.3, 0.1))
    assert plan_geometry.world_to_local(base, world) == pytest.approx((0.3, 0.1))


def test_desired_center_distance_straight_ahead():
    assert plan_geometry.desired_center_distance(0.0, 0.2, -0.092) == pytest.approx(0.108)

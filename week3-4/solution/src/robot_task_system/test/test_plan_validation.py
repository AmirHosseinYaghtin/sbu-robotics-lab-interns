import os

import pytest
from robot_task_system import plan_parser

CONFIG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))


def test_real_plan_is_valid():
    plan, actions = plan_parser.load_and_validate(
        os.path.join(CONFIG, 'plan_pick_place.json')
    )
    assert plan['problem'] == 'get_pick_and_place_problem'
    assert [a['type'] for a in actions] == ['move_base', 'pick', 'move_base', 'place']


def test_real_plan_keeps_base_and_object_pose():
    _, actions = plan_parser.load_and_validate(os.path.join(CONFIG, 'plan_pick_place.json'))
    pick = actions[1]
    assert len(pick['base_conf']) == 3
    assert pick['object_pose'] == pytest.approx((0.8, 0.0))


@pytest.mark.parametrize('name, message', [
    ('unknown_action.json', 'not supported'),
    ('missing_arm_conf.json', 'missing arm_start'),
    ('wrong_joint_count.json', 'expected 3'),
    ('empty_arm_trajectory.json', 'empty arm trajectory'),
    ('place_without_pick.json', 'holds nothing'),
    ('double_pick.json', 'already held'),
    ('unmerged_actions.json', '-ma'),
    ('empty_plan.json', 'no executable actions'),
])
def test_invalid_plans_are_rejected(name, message):
    with pytest.raises(plan_parser.PlanError) as error:
        plan_parser.load_and_validate(os.path.join(CONFIG, 'error_plans', name))
    assert message in str(error.value)


def test_missing_file_is_a_plan_error():
    with pytest.raises(plan_parser.PlanError):
        plan_parser.load_and_validate(os.path.join(CONFIG, 'does_not_exist.json'))


def test_pick_without_object_argument_is_rejected():
    with pytest.raises(plan_parser.PlanError):
        plan_parser.parse_actions({'actions': [{'name': 'pick_and_stow', 'args': ['robot0']}]})

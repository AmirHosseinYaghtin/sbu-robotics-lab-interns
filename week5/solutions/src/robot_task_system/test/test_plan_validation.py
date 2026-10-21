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


PLANS = os.path.join(CONFIG, 'plans')


def held_counts(actions):
    held = set()
    counts = []
    for action in actions:
        if action['type'] == 'pick':
            assert action['obj'] not in held
            held.add(action['obj'])
        elif action['type'] == 'place':
            held.remove(action['obj'])
        counts.append(len(held))
    return counts


@pytest.mark.parametrize('name', [
    'pick_place', 'corridor', 'multi_object', 'at_work', 'simple',
])
def test_every_map_is_valid_and_holds_one_object(name):
    _, actions = plan_parser.load_and_validate(os.path.join(PLANS, name + '.json'))
    assert max(held_counts(actions)) == 1
    assert held_counts(actions)[-1] == 0


def test_at_work_places_each_object_before_the_next_pick():
    _, actions = plan_parser.load_and_validate(os.path.join(PLANS, 'at_work.json'))
    manipulations = [(a['type'], a['obj']) for a in actions if a['type'] != 'move_base']
    picks = [obj for kind, obj in manipulations if kind == 'pick']
    assert picks == ['f20_20_1', 'f20_20_2', 'bearing1', 's40_40_1', 's40_40_2']
    for index in range(0, len(manipulations), 2):
        assert manipulations[index][0] == 'pick'
        assert manipulations[index + 1] == ('place', manipulations[index][1])


def test_every_manipulation_is_preceded_by_a_move():
    _, actions = plan_parser.load_and_validate(os.path.join(PLANS, 'at_work.json'))
    for index, action in enumerate(actions):
        if action['type'] != 'move_base':
            assert actions[index - 1]['type'] == 'move_base'
            goal = actions[index - 1]['goal']
            assert goal == pytest.approx(action['base_conf'], abs=1e-6)


@pytest.mark.parametrize('name', ['multi_object', 'at_work'])
def test_multi_object_plan_is_rejected_without_reordering(name):
    with pytest.raises(plan_parser.PlanError) as error:
        plan_parser.load_and_validate(
            os.path.join(PLANS, name + '.json'), one_at_a_time=False
        )
    assert 'one_object_at_a_time' in str(error.value)


def test_simple_map_matches_the_default_plan():
    _, simple = plan_parser.load_and_validate(os.path.join(PLANS, 'simple.json'))
    _, default = plan_parser.load_and_validate(os.path.join(CONFIG, 'plan_pick_place.json'))
    assert simple == default

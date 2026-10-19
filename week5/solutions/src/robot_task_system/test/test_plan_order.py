import math
import os

import pytest
from robot_task_system import plan_order
from robot_task_system import plan_parser

PLANS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'plans'))


def raw(name):
    plan = plan_parser.load_plan(os.path.join(PLANS, name + '.json'))
    return plan, plan_parser.parse_actions(plan)


def test_held_peak_counts_objects_held_together():
    _, actions = raw('at_work')
    assert plan_order.held_peak(actions) == 3
    _, actions = raw('pick_place')
    assert plan_order.held_peak(actions) == 1


def test_single_object_plan_is_returned_unchanged():
    plan, actions = raw('corridor')
    assert plan_order.one_object_at_a_time(plan, actions) is actions


@pytest.mark.parametrize('name', ['multi_object', 'at_work'])
def test_reordered_plan_keeps_every_manipulation(name):
    plan, actions = raw(name)
    result = plan_order.one_object_at_a_time(plan, actions)
    assert plan_order.held_peak(result) == 1
    before = sorted(a['label'] for a in actions if a['type'] != 'move_base')
    after = sorted(a['label'] for a in result if a['type'] != 'move_base')
    assert before == after
    for action in result:
        if action['type'] != 'move_base':
            original = [a for a in actions if a['label'] == action['label']][0]
            assert action['base_conf'] == original['base_conf']
            assert action['arm_trajectory'] == original['arm_trajectory']


@pytest.mark.parametrize('name', ['multi_object', 'at_work'])
def test_routes_are_continuous(name):
    plan, actions = raw(name)
    result = plan_order.one_object_at_a_time(plan, actions)
    initial = plan['scene']['initial_base']
    here = (initial['x'], initial['y'], initial['theta'])
    for action in result:
        if action['type'] == 'move_base':
            assert action['waypoints'][0][:2] == pytest.approx(here[:2], abs=1e-6)
            here = action['goal']
        else:
            assert action['base_conf'][:2] == pytest.approx(here[:2], abs=1e-6)


def test_straight_line_through_a_box_is_not_clear():
    box = [(-0.5, -0.5, 0.5, 0.5)]
    assert not plan_order.straight_is_clear((-2.0, 0.0), (2.0, 0.0), box, 0.3)
    assert plan_order.straight_is_clear((-2.0, 1.0), (2.0, 1.0), box, 0.3)


def test_road_map_finds_shortest_chain():
    roads = plan_order.RoadMap()
    a = roads.node((0.0, 0.0, 0.0))
    b = roads.node((1.0, 0.0, 0.0))
    c = roads.node((1.0, 1.0, 0.0))
    roads.connect(a, b, [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)])
    roads.connect(b, c, [(1.0, 0.0, 0.0), (1.0, 1.0, 0.0)])
    route = roads.route(c, a)
    length = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(route, route[1:]))
    assert length == pytest.approx(2.0)


def test_object_never_placed_is_an_order_error():
    plan, actions = raw('at_work')
    last_place = max(i for i, a in enumerate(actions) if a['type'] == 'place')
    with pytest.raises(plan_order.OrderError):
        plan_order.one_object_at_a_time(plan, actions[:last_place])

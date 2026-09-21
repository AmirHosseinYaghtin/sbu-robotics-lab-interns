from robot_task_system import plan_parser


def _base_conf(x, y, theta):
    return {'__type__': 'BaseConf', 'x': x, 'y': y, 'theta': theta}


def _sample_plan():
    traj = {
        '__type__': 'BaseTraj',
        'waypoints': [
            _base_conf(0.0, -1.0, 0.0),
            _base_conf(0.2, -0.5, 0.3),
            _base_conf(0.47, 0.26, -0.65),
        ],
    }
    return {
        'problem': 'get_pick_and_place_problem',
        'cost': 20.4,
        'actions': [
            {
                'name': 'move_base',
                'args': [
                    _base_conf(0.0, -1.0, 0.0),
                    _base_conf(0.47, 0.26, -0.65),
                    traj,
                    _base_conf(0.47, 0.26, -0.65),
                ],
            },
            {
                'name': 'pick_and_stow',
                'args': ['robot', 'cube1', 'slot0'],
            },
        ],
    }


def test_move_base_keeps_full_waypoints_with_theta():
    actions = plan_parser.parse_actions(_sample_plan())

    move = actions[0]
    assert move['type'] == 'move_base'
    assert move['label'] == 'MOVE_BASE'
    assert len(move['waypoints']) == 3
    for wp in move['waypoints']:
        assert len(wp) == 3
    assert move['waypoints'][-1] == (0.47, 0.26, -0.65)
    assert move['goal'] == (0.47, 0.26, -0.65)


def test_pick_action_is_labelled_per_object():
    actions = plan_parser.parse_actions(_sample_plan())

    pick = actions[1]
    assert pick['type'] == 'pick'
    assert pick['label'] == 'PICK_cube1'
    assert pick['obj'] == 'cube1'


def test_summarize_lists_every_action():
    actions = plan_parser.parse_actions(_sample_plan())
    summary = plan_parser.summarize(actions)

    assert 'MOVE_BASE' in summary
    assert 'PICK_cube1' in summary
    assert summary.count('\n') == len(actions) - 1

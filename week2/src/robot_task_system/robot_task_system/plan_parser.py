import json


def load_plan(path):
    with open(path, 'r') as plan_file:
        return json.load(plan_file)


def _conf_to_tuple(conf):
    return (
        float(conf['x']),
        float(conf['y']),
        float(conf['theta']),
    )


def _waypoints_from_traj(traj):
    return [_conf_to_tuple(wp) for wp in traj['waypoints']]


def parse_actions(plan):
    actions = []

    for raw in plan.get('actions', []):
        name = raw['name']
        args = raw['args']

        if name == 'move_base':
            trajectory = args[2]
            goal = args[3]
            actions.append({
                'type': 'move_base',
                'name': name,
                'label': 'MOVE_BASE',
                'waypoints': _waypoints_from_traj(trajectory),
                'goal': _conf_to_tuple(goal),
            })

        elif name in ('pick_and_stow', 'pick'):
            obj = args[1]
            slot = args[-1]
            actions.append({
                'type': 'pick',
                'name': name,
                'label': 'PICK_{}'.format(obj),
                'obj': obj,
                'slot': slot,
                'duration': 3.0,
            })

        elif name in ('unstow_and_place', 'place'):
            obj = args[1]
            slot = args[-1]
            actions.append({
                'type': 'place',
                'name': name,
                'label': 'PLACE_{}'.format(obj),
                'obj': obj,
                'slot': slot,
                'duration': 2.0,
            })

        else:
            actions.append({
                'type': 'other',
                'name': name,
                'label': name.upper(),
                'duration': 1.0,
            })

    return actions


def summarize(actions):
    lines = []
    for index, action in enumerate(actions):
        if action['type'] == 'move_base':
            goal = action['goal']
            lines.append(
                '{:>2}) {} ({} waypoints) -> goal '
                '(x={:.2f}, y={:.2f}, theta={:.2f})'.format(
                    index + 1,
                    action['label'],
                    len(action['waypoints']),
                    goal[0], goal[1], goal[2],
                )
            )
        else:
            lines.append(
                '{:>2}) {}'.format(index + 1, action['label'])
            )
    return '\n'.join(lines)

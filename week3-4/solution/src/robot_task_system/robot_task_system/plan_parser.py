import json


def load_plan(plan_file):
    with open(plan_file, 'r', encoding='utf-8') as file:
        return json.load(file)


def _is_type(value, type_name):
    return (
        isinstance(value, dict)
        and value.get('__type__') == type_name
    )


def _base_conf_to_tuple(conf):
    return (
        float(conf['x']),
        float(conf['y']),
        float(conf['theta']),
    )


def _arm_conf_to_list(conf):
    return [
        float(value)
        for value in conf.get('joints', [])
    ]


def _extract_manipulation_data(args):
    grasp = next(
        (
            arg
            for arg in args
            if _is_type(arg, 'Grasp')
        ),
        None,
    )

    arm_confs = [
        arg
        for arg in args
        if _is_type(arg, 'ArmConf')
    ]

    arm_traj = next(
        (
            arg
            for arg in args
            if _is_type(arg, 'ArmTraj')
        ),
        None,
    )

    arm_start = (
        _arm_conf_to_list(arm_confs[0])
        if len(arm_confs) >= 1
        else None
    )

    arm_goal = (
        _arm_conf_to_list(arm_confs[1])
        if len(arm_confs) >= 2
        else None
    )

    arm_trajectory = []

    if arm_traj is not None:
        arm_trajectory = [
            _arm_conf_to_list(conf)
            for conf in arm_traj.get('waypoints', [])
            if _is_type(conf, 'ArmConf')
        ]

    return {
        'grasp': grasp,
        'arm_start': arm_start,
        'arm_goal': arm_goal,
        'arm_trajectory': arm_trajectory,
    }


def parse_actions(plan):
    parsed_actions = []

    for action in plan.get('actions', []):
        name = action.get('name', '')
        args = action.get('args', [])

        if name == 'move_base':
            trajectory = next(
                (
                    arg
                    for arg in args
                    if _is_type(arg, 'BaseTraj')
                ),
                None,
            )

            waypoints = []

            if trajectory is not None:
                waypoints = [
                    _base_conf_to_tuple(conf)
                    for conf in trajectory.get('waypoints', [])
                    if _is_type(conf, 'BaseConf')
                ]

            base_confs = [
                arg
                for arg in args
                if _is_type(arg, 'BaseConf')
            ]

            if base_confs:
                goal = _base_conf_to_tuple(base_confs[-1])
            elif waypoints:
                goal = waypoints[-1]
            else:
                goal = None

            parsed_actions.append({
                'type': 'move_base',
                'label': 'MOVE_BASE',
                'waypoints': waypoints,
                'goal': goal,
            })

        elif name == 'pick_and_stow':
            if len(args) < 2:
                continue

            obj = str(args[1])
            manipulation = _extract_manipulation_data(args)

            parsed_actions.append({
                'type': 'pick',
                'label': f'PICK_{obj}',
                'obj': obj,
                **manipulation,
            })

        elif name in ('unstow_and_place', 'place_and_unstow'):
            if len(args) < 2:
                continue

            obj = str(args[1])
            manipulation = _extract_manipulation_data(args)

            parsed_actions.append({
                'type': 'place',
                'label': f'PLACE_{obj}',
                'obj': obj,
                **manipulation,
            })

    return parsed_actions


def summarize(actions):
    lines = []

    for index, action in enumerate(actions, start=1):
        if action['type'] == 'move_base':
            lines.append(
                '{}. {} ({} waypoints)'.format(
                    index,
                    action['label'],
                    len(action['waypoints']),
                )
            )
        else:
            lines.append(
                '{}. {}'.format(
                    index,
                    action['label'],
                )
            )

    return '\n'.join(lines)

import json


PLANNER_ARM_JOINTS = 3


class PlanError(Exception):
    pass


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


def _is_point(value):
    return (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(
            isinstance(item, (int, float))
            for item in value
        )
    )


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

    base_conf = next(
        (
            arg
            for arg in args
            if _is_type(arg, 'BaseConf')
        ),
        None,
    )

    object_pose = next(
        (
            arg
            for arg in args
            if _is_point(arg)
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
        'base_conf': (
            _base_conf_to_tuple(base_conf)
            if base_conf is not None
            else None
        ),
        'object_pose': (
            (float(object_pose[0]), float(object_pose[1]))
            if object_pose is not None
            else None
        ),
        'arm_start': arm_start,
        'arm_goal': arm_goal,
        'arm_trajectory': arm_trajectory,
    }


def parse_actions(plan):
    parsed_actions = []

    for index, action in enumerate(plan.get('actions', []), start=1):
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
                raise PlanError(
                    'action #{} ({}) has no object argument'.format(
                        index,
                        name,
                    )
                )

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
                raise PlanError(
                    'action #{} ({}) has no object argument'.format(
                        index,
                        name,
                    )
                )

            obj = str(args[1])
            manipulation = _extract_manipulation_data(args)

            parsed_actions.append({
                'type': 'place',
                'label': f'PLACE_{obj}',
                'obj': obj,
                **manipulation,
            })

        elif name in ('pick', 'stow', 'unstow', 'place'):
            raise PlanError(
                'action #{} "{}" comes from the unmerged domain; '
                'export the plan with merged actions (-ma)'.format(
                    index,
                    name,
                )
            )

        else:
            raise PlanError(
                'action #{} "{}" is not supported'.format(
                    index,
                    name,
                )
            )

    return parsed_actions


def _validate_manipulation(action, index):
    label = action['label']

    for key in ('base_conf', 'object_pose', 'arm_start', 'arm_goal'):
        if action.get(key) is None:
            raise PlanError(
                '{} (#{}) is missing {}'.format(label, index, key)
            )

    for key in ('arm_start', 'arm_goal'):
        if len(action[key]) != PLANNER_ARM_JOINTS:
            raise PlanError(
                '{} (#{}) {} has {} joints, expected {}'.format(
                    label,
                    index,
                    key,
                    len(action[key]),
                    PLANNER_ARM_JOINTS,
                )
            )

    trajectory = action.get('arm_trajectory') or []

    if not trajectory:
        raise PlanError(
            '{} (#{}) has an empty arm trajectory'.format(label, index)
        )

    if any(len(point) != PLANNER_ARM_JOINTS for point in trajectory):
        raise PlanError(
            '{} (#{}) arm trajectory has a waypoint with the wrong '
            'joint count'.format(label, index)
        )


def validate_actions(actions):
    if not actions:
        raise PlanError('plan contains no executable actions')

    held = None

    for index, action in enumerate(actions, start=1):
        if action['type'] == 'move_base':
            if not action['waypoints'] and action.get('goal') is None:
                raise PlanError(
                    'MOVE_BASE (#{}) has no waypoints'.format(index)
                )
            continue

        _validate_manipulation(action, index)

        if action['type'] == 'pick':
            if held is not None:
                raise PlanError(
                    '{} (#{}) requires an empty gripper but {} is already '
                    'held; multi-object plans need stow/unstow '
                    'support'.format(action['label'], index, held)
                )
            held = action['obj']
        else:
            if held != action['obj']:
                raise PlanError(
                    '{} (#{}) places {} but the gripper holds {}'.format(
                        action['label'],
                        index,
                        action['obj'],
                        held or 'nothing',
                    )
                )
            held = None

    return actions


def load_and_validate(plan_file):
    try:
        plan = load_plan(plan_file)
    except (OSError, ValueError) as error:
        raise PlanError(
            'cannot read plan "{}": {}'.format(plan_file, error)
        )

    actions = parse_actions(plan)
    validate_actions(actions)

    return plan, actions


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

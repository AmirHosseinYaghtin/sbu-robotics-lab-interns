GRIPPER = 'gripper'
ARM = 'arm'
ATTACHMENT = 'attachment'
ATTACH = 'attach'
DETACH = 'detach'
OPEN = 'open'
CLOSE = 'close'


class ManipulationError(Exception):
    pass


def step(name, kind, value):
    return {'name': name, 'kind': kind, 'value': value}


def planner_to_arm(fixed_joint1, planner_joints):
    if len(planner_joints) != 3:
        raise ManipulationError('planner arm configuration must have 3 joints')
    return [
        float(fixed_joint1),
        float(planner_joints[0]),
        float(planner_joints[1]),
        float(planner_joints[2]),
    ]


def planner_trajectory(fixed_joint1, waypoints):
    if not waypoints:
        raise ManipulationError('planner arm trajectory is empty')
    points = []
    for joints in waypoints:
        points.append(planner_to_arm(fixed_joint1, joints))
    return points


def pick_steps(trajectory, grasp, home, use_attachment=False):
    steps = [
        step('OPEN_GRIPPER', GRIPPER, OPEN),
        step('FOLLOW_PLANNER_TRAJECTORY', ARM, trajectory),
        step('MOVE_GRASP', ARM, [grasp]),
    ]
    if use_attachment:
        steps.append(step('ATTACH_OBJECT', ATTACHMENT, ATTACH))
    return steps + [
        step('CLOSE_GRIPPER', GRIPPER, CLOSE),
        step('LIFT', ARM, [trajectory[-1]]),
        step('MOVE_HOME', ARM, [list(home)]),
    ]


def place_steps(trajectory, release, home, use_attachment=False):
    steps = [
        step('FOLLOW_PLANNER_TRAJECTORY', ARM, trajectory),
        step('MOVE_PLACE', ARM, [release]),
        step('OPEN_GRIPPER', GRIPPER, OPEN),
    ]
    if use_attachment:
        steps.append(step('DETACH_OBJECT', ATTACHMENT, DETACH))
    return steps + [
        step('RETREAT', ARM, [trajectory[-1]]),
        step('MOVE_HOME', ARM, [list(home)]),
    ]


def segment_duration(start, goal, max_joint_speed, min_duration):
    if start is None:
        return max(min_duration, 3.0)
    largest = 0.0
    for a, b in zip(start, goal):
        largest = max(largest, abs(a - b))
    return max(min_duration, largest / max_joint_speed)

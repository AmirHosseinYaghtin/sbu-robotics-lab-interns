import math


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


def arm_configuration(fixed_joint1, pitch_joints):
    """Build a calibrated OpenMANIPULATOR pose, not a continuous2d pose."""
    if len(pitch_joints) != 3:
        raise ManipulationError('calibrated arm configuration must have 3 pitch joints')
    return [
        float(fixed_joint1),
        float(pitch_joints[0]),
        float(pitch_joints[1]),
        float(pitch_joints[2]),
    ]


def validate_arm_points(points, lower, upper, margin=0.0):
    """Reject invalid targets instead of changing their physical geometry."""
    if len(lower) != 4 or len(upper) != 4:
        raise ManipulationError('arm limits must contain 4 joints')
    if not math.isfinite(margin) or margin < 0.0:
        raise ManipulationError('joint limit margin must be finite and nonnegative')
    for low, high in zip(lower, upper):
        if not all(math.isfinite(v) for v in (low, high)) or low + margin >= high - margin:
            raise ManipulationError('invalid arm joint limits or margin')
    if not points:
        raise ManipulationError('arm trajectory is empty')
    for joints in points:
        if len(joints) != 4:
            raise ManipulationError('arm waypoint must contain 4 joints')
        for index, value in enumerate(joints):
            low = lower[index] + margin
            high = upper[index] - margin
            if not math.isfinite(value) or not low <= value <= high:
                raise ManipulationError(
                    'joint{} target {} outside [{:.3f}, {:.3f}] rad'.format(
                        index + 1, value, low, high
                    )
                )


def pick_steps(clearance, grasp, home, use_attachment=False):
    steps = [
        step('OPEN_GRIPPER', GRIPPER, OPEN),
        step('MOVE_CLEARANCE', ARM, [list(clearance)]),
        step('MOVE_GRASP', ARM, [grasp]),
    ]
    if use_attachment:
        steps.append(step('ATTACH_OBJECT', ATTACHMENT, ATTACH))
    return steps + [
        step('CLOSE_GRIPPER', GRIPPER, CLOSE),
        step('LIFT', ARM, [list(clearance)]),
        step('MOVE_HOME', ARM, [list(home)]),
    ]


def place_steps(clearance, release, home, use_attachment=False):
    steps = [
        step('MOVE_CLEARANCE', ARM, [list(clearance)]),
        step('MOVE_PLACE', ARM, [release]),
        step('OPEN_GRIPPER', GRIPPER, OPEN),
    ]
    if use_attachment:
        steps.append(step('DETACH_OBJECT', ATTACHMENT, DETACH))
    return steps + [
        step('RETREAT', ARM, [list(clearance)]),
        step('MOVE_HOME', ARM, [list(home)]),
    ]


def segment_duration(start, goal, max_joint_speed, min_duration):
    if not math.isfinite(max_joint_speed) or max_joint_speed <= 0.0:
        raise ManipulationError('max_joint_speed must be finite and positive')
    if not math.isfinite(min_duration) or min_duration <= 0.0:
        raise ManipulationError('minimum segment duration must be finite and positive')
    if start is None:
        return max(min_duration, 3.0)
    largest = 0.0
    for a, b in zip(start, goal):
        largest = max(largest, abs(a - b))
    return max(min_duration, largest / max_joint_speed)

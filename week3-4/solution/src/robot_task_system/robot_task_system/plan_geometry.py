import math

from robot_task_system import planner_kinematics


def local_to_world(base, local):
    bx, by, btheta = base
    lx, ly = local
    x = bx + math.cos(btheta) * lx - math.sin(btheta) * ly
    y = by + math.sin(btheta) * lx + math.cos(btheta) * ly
    return x, y


def world_to_local(base, point):
    bx, by, btheta = base
    dx = point[0] - bx
    dy = point[1] - by
    x = math.cos(btheta) * dx + math.sin(btheta) * dy
    y = -math.sin(btheta) * dx + math.cos(btheta) * dy
    return x, y


def desired_center_distance(bearing, grasp_reach, arm_mount_x):
    lateral = arm_mount_x * math.sin(bearing)
    if grasp_reach < abs(lateral):
        return None
    return arm_mount_x * math.cos(bearing) + math.sqrt(grasp_reach ** 2 - lateral ** 2)


def shift_move_goal(move, shift, bearing):
    gx, gy, gtheta = move['goal']
    direction = gtheta + bearing
    new_goal = (
        gx + shift * math.cos(direction),
        gy + shift * math.sin(direction),
        gtheta,
    )
    waypoints = list(move['waypoints'])
    if not waypoints or waypoints[-1] != move['goal']:
        waypoints.append(move['goal'])
    waypoints.append(new_goal)
    move['waypoints'] = waypoints
    move['goal'] = new_goal
    return new_goal


def prepare_actions(actions, approach=True, grasp_reach=0.20, arm_mount_x=-0.092,
                    min_shift=0.005):
    result = []

    for action in actions:
        if action['type'] == 'move_base':
            result.append(action)
            continue

        base = action['base_conf']
        local = planner_kinematics.forward_kinematics(action['arm_goal'])
        bearing = math.atan2(local[1], local[0])
        planner_distance = math.sqrt(local[0] ** 2 + local[1] ** 2)

        object_local = world_to_local(base, action['object_pose'])
        action['consistency_error'] = math.sqrt(
            (object_local[0] - local[0]) ** 2 + (object_local[1] - local[1]) ** 2
        )
        action['target_world'] = local_to_world(base, local)
        action['approach_shift'] = 0.0

        previous = result[-1] if result else None
        desired = desired_center_distance(bearing, grasp_reach, arm_mount_x)

        can_shift = (
            approach
            and previous is not None
            and previous['type'] == 'move_base'
            and previous.get('goal') is not None
            and desired is not None
            and abs(planner_distance - desired) >= min_shift
        )

        if not can_shift:
            result.append(action)
            continue

        shift = planner_distance - desired
        planner_base = previous['goal']
        action['base_conf'] = shift_move_goal(previous, shift, bearing)
        action['approach_shift'] = shift
        result.append(action)
        result.append({
            'type': 'move_base',
            'label': 'RETREAT',
            'reverse': True,
            'waypoints': [planner_base],
            'goal': planner_base,
        })

    if result and result[-1]['label'] == 'RETREAT':
        result.pop()

    return result

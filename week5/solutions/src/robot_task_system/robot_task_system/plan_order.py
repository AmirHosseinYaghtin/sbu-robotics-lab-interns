"""
Carry one object at a time.

The PDDLStream merged domain stows picked objects on a 3-slot tray, so a plan
may pick several objects before it places any of them (at_work picks
f20_20_1, f20_20_2 and bearing1 in a row). The robot carries objects in its
gripper, so such a plan is reordered here into pick -> place pairs:

    MOVE  PICK A  MOVE  PLACE A  MOVE  PICK B  MOVE  PLACE B ...

Picks keep the planner's order. The planner's base poses, grasps and arm
trajectories are reused unchanged; only the base paths between them are new.
A path is a chain of planner trajectories (collision-checked by the planner,
driven forwards or backwards) and straight shortcuts that keep clear of every
table, obstacle and stand in the plan's scene.

Pure Python (no ROS imports). Works in the planner frame, before anchoring.
"""

import heapq
import math

# Waffle footprint (0.281 x 0.306 m) plus the arm at home, with a margin.
DEFAULT_CLEARANCE = 0.30
SAMPLE_STEP = 0.02
SAME_POSE = 1e-3


class OrderError(Exception):
    pass


def held_peak(actions):
    """Return the largest number of objects held at the same time."""
    held = 0
    peak = 0
    for action in actions:
        if action['type'] == 'pick':
            held += 1
        elif action['type'] == 'place':
            held -= 1
        peak = max(peak, held)
    return peak


# --------------------------------------------------------------------------
# Obstacles


def _box(x, y, size_x, size_y):
    return (x - size_x / 2.0, y - size_y / 2.0, x + size_x / 2.0, y + size_y / 2.0)


def scene_obstacles(plan, actions, pick_stand=0.04, place_stand=0.08):
    """Axis-aligned boxes (planner frame) the base must keep clear of."""
    boxes = []
    for item in (plan.get('scene') or {}).get('furniture', []):
        x, y = float(item['pose'][0]), float(item['pose'][1])
        boxes.append(_box(x, y, float(item['size'][0]), float(item['size'][1])))
    for action in actions:
        if action['type'] == 'move_base' or action.get('object_pose') is None:
            continue
        x, y = action['object_pose']
        size = pick_stand if action['type'] == 'pick' else place_stand
        boxes.append(_box(x, y, size, size))
    return boxes


def _box_distance(point, box):
    dx = max(box[0] - point[0], 0.0, point[0] - box[2])
    dy = max(box[1] - point[1], 0.0, point[1] - box[3])
    return math.hypot(dx, dy)


def straight_is_clear(start, end, boxes, clearance=DEFAULT_CLEARANCE):
    """
    True if the base can drive straight from start to end.

    Every point must stay `clearance` from each box, except that the path may
    stay as close as its own end points already are (a base pose next to a
    table is valid; driving closer than that is not).
    """
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    samples = max(1, int(math.ceil(length / SAMPLE_STEP)))
    for box in boxes:
        allowed = min(clearance, _box_distance(start, box), _box_distance(end, box))
        for index in range(samples + 1):
            t = index / samples
            point = (start[0] + t * (end[0] - start[0]), start[1] + t * (end[1] - start[1]))
            if _box_distance(point, box) < allowed - SAME_POSE:
                return False
    return True


# --------------------------------------------------------------------------
# Road map of base poses


def _path_length(points):
    return sum(
        math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])
    )


class RoadMap:

    def __init__(self):
        self.poses = []
        self.edges = {}

    def node(self, pose):
        for index, known in enumerate(self.poses):
            if all(abs(a - b) <= SAME_POSE for a, b in zip(known, pose)):
                return index
        self.poses.append(tuple(pose))
        self.edges[len(self.poses) - 1] = []
        return len(self.poses) - 1

    def connect(self, a, b, points):
        if a == b:
            return
        length = _path_length(points)
        self.edges[a].append((length, b, list(points)))
        self.edges[b].append((length, a, list(reversed(points))))

    def add_shortcuts(self, boxes, clearance):
        for a in range(len(self.poses)):
            for b in range(a + 1, len(self.poses)):
                start, end = self.poses[a], self.poses[b]
                if straight_is_clear(start, end, boxes, clearance):
                    self.connect(a, b, [start, end])

    def route(self, a, b):
        """Shortest list of poses from node a to node b (both included)."""
        if a == b:
            return [self.poses[a]]
        best = {a: 0.0}
        previous = {}
        queue = [(0.0, a)]
        while queue:
            cost, current = heapq.heappop(queue)
            if current == b:
                break
            if cost > best.get(current, math.inf):
                continue
            for length, neighbour, points in self.edges[current]:
                total = cost + length
                if total < best.get(neighbour, math.inf) - 1e-9:
                    best[neighbour] = total
                    previous[neighbour] = (current, points)
                    heapq.heappush(queue, (total, neighbour))
        if b not in previous:
            raise OrderError('no base path between two plan poses')
        pieces = []
        current = b
        while current != a:
            current, points = previous[current]
            pieces.append(points)
        route = [self.poses[a]]
        for points in reversed(pieces):
            for point in points[1:]:
                route.append(tuple(point))
        # The last pose carries the heading the base must end with.
        route[-1] = self.poses[b]
        return route


def _move_points(action, start):
    points = [tuple(start)]
    for waypoint in action['waypoints']:
        if math.hypot(waypoint[0] - points[-1][0], waypoint[1] - points[-1][1]) > SAME_POSE:
            points.append(tuple(waypoint))
    goal = action.get('goal')
    if goal is not None:
        if math.hypot(goal[0] - points[-1][0], goal[1] - points[-1][1]) > SAME_POSE:
            points.append(tuple(goal))
        else:
            points[-1] = tuple(goal)
    return points


def _move(route):
    return {
        'type': 'move_base',
        'label': 'MOVE_BASE',
        'waypoints': [tuple(pose) for pose in route],
        'goal': tuple(route[-1]),
    }


# --------------------------------------------------------------------------
# Reordering


def one_object_at_a_time(plan, actions, clearance=DEFAULT_CLEARANCE):
    """
    Return actions reordered so the robot never holds two objects.

    actions are parsed plan actions in the planner frame. Plans that never
    hold more than one object are returned unchanged.
    """
    if held_peak(actions) <= 1:
        return actions

    start = None
    for action in actions:
        if action['type'] == 'move_base':
            if action['waypoints']:
                start = action['waypoints'][0]
            elif action.get('goal') is not None:
                start = action['goal']
            break
    initial = (plan.get('scene') or {}).get('initial_base')
    if initial is not None:
        start = (float(initial['x']), float(initial['y']), float(initial['theta']))
    if start is None:
        raise OrderError('plan has no start pose')

    roads = RoadMap()
    here = roads.node(start)
    where = []      # (action, node it is executed at)
    for action in actions:
        if action['type'] == 'move_base':
            points = _move_points(action, roads.poses[here])
            target = roads.node(points[-1])
            roads.connect(here, target, points)
            here = target
        else:
            where.append((action, here))
    end_node = here
    roads.add_shortcuts(scene_obstacles(plan, actions), clearance)

    pairs = []
    waiting = {}
    for action, node in where:
        if action['type'] == 'pick':
            pairs.append([(action, node), None])
            waiting[action['obj']] = pairs[-1]
        else:
            pair = waiting.pop(action['obj'], None)
            if pair is None:
                raise OrderError('{} places an object that was not picked'.format(
                    action['label']))
            pair[1] = (action, node)
    if waiting:
        raise OrderError('{} picked but never placed; cannot carry one at a time'.format(
            ', '.join(sorted(waiting))))

    result = []
    here = roads.node(start)
    for pick, place in pairs:
        for action, node in (pick, place):
            result.append(_move(roads.route(here, node)))
            result.append(action)
            here = node
    if end_node != here:
        result.append(_move(roads.route(here, end_node)))
    return result


def total_drive(actions):
    """Length of every base path in the plan (m)."""
    total = 0.0
    for action in actions:
        if action['type'] == 'move_base':
            total += _path_length(action['waypoints'])
    return total

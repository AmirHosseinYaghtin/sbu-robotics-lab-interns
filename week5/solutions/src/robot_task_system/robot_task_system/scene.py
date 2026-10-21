"""
Build the Gazebo scene that matches a PDDLStream plan.

The plan JSON written by planner_reference/export_plan.py carries a "scene"
block (furniture, regions, objects and the initial base pose). This module is
the single place that converts planner coordinates into the odom/world frame
used by the ROS nodes, so the launch file, the Task Controller and the
verification tool cannot drift apart.

Plans without a "scene" block (older exports) still work: objects come from
the pick actions and no furniture is spawned.

Pure Python (no ROS imports), so it is unit-testable and usable from launch.
"""

import math
import os

from robot_task_system import planner_kinematics

DEFAULT_CONFIG = {
    # pedestal: small stands under each object and at each place pose. This is
    #           what the robot can actually reach: the planner's 0.6 m tables
    #           would collide with the real base before the 0.20 m arm reaches.
    # full:     spawn the planner's tables/workstations at full size.
    'surface_mode': 'pedestal',
    'surface_height': 0.05,
    'pick_pedestal_size': 0.04,
    'place_pedestal_size': 0.08,
    # Visual-only floor plates showing the planner regions (pedestal mode).
    'show_regions': True,
    'region_plate_height': 0.002,
    # Non-region furniture (shelves, barriers, walls) always has collisions.
    'obstacle_height': 0.40,
    'obstacle_heights': {},
    # Edge length of the spawned objects. None = use the planner footprint.
    # 0.03 m matches the gripper and the calibrated grasp_joints.
    'object_size': 0.03,
    'object_mass': 0.02,
    'spawn_clearance': 0.001,
    # Attachment plugin settings written into each object model.
    'parent_link': 'link5',
    'grasp_offset': [0.126, 0.0, 0.0],
    'max_grasp_distance': 0.04,
}


class SceneError(Exception):
    pass


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def load_config(path=None):
    """Return DEFAULT_CONFIG updated with a YAML file (if given)."""
    config = dict(DEFAULT_CONFIG)
    if path:
        import yaml
        with open(path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            raise SceneError('scene config "{}" must be a mapping'.format(path))
        unknown = sorted(set(data) - set(DEFAULT_CONFIG))
        if unknown:
            raise SceneError('unknown scene config keys: {}'.format(', '.join(unknown)))
        config.update(data)
    if config['surface_mode'] not in ('pedestal', 'full'):
        raise SceneError('surface_mode must be "pedestal" or "full"')
    return config


# --------------------------------------------------------------------------
# Planner frame -> odom frame


def plan_anchor(plan, actions):
    """Planner pose that becomes the odom origin (the robot's start pose)."""
    scene = plan.get('scene') or {}
    base = scene.get('initial_base')
    if base is not None:
        return (float(base['x']), float(base['y']), float(base['theta']))
    for action in actions:
        if action['type'] == 'move_base' and action['waypoints']:
            return tuple(action['waypoints'][0])
    return None


def make_transform(anchor):
    """Return f(x, y, theta) mapping planner coordinates into odom."""
    if anchor is None:
        return lambda x, y, theta=0.0: (x, y, theta)

    start_x, start_y, start_theta = anchor
    cos_t = math.cos(-start_theta)
    sin_t = math.sin(-start_theta)

    def transform(x, y, theta=0.0):
        rel_x = x - start_x
        rel_y = y - start_y
        return (
            rel_x * cos_t - rel_y * sin_t,
            rel_x * sin_t + rel_y * cos_t,
            normalize_angle(theta - start_theta),
        )

    return transform


def anchor_actions(actions, anchor):
    """Transform parsed plan actions in place from planner to odom frame."""
    if anchor is None:
        return actions
    transform = make_transform(anchor)
    for action in actions:
        if action['type'] != 'move_base':
            if action.get('base_conf') is not None:
                action['base_conf'] = transform(*action['base_conf'])
            if action.get('object_pose') is not None:
                action['object_pose'] = transform(*action['object_pose'])[:2]
            continue
        action['waypoints'] = [transform(*w) for w in action['waypoints']]
        if action.get('goal') is not None:
            action['goal'] = transform(*action['goal'])
    return actions


# --------------------------------------------------------------------------
# Scene description


def _box(name, kind, x, y, yaw, size, height, collision=True, z=0.0):
    return {
        'name': name, 'kind': kind,
        'x': float(x), 'y': float(y), 'z': float(z), 'yaw': float(yaw),
        'size': [float(size[0]), float(size[1]), float(height)],
        'collision': collision,
    }


def _pick_yaw(action):
    """Object yaw facing the arm: base heading plus arm bearing."""
    if action.get('base_conf') is None or not action.get('arm_goal'):
        return 0.0
    local = planner_kinematics.forward_kinematics(action['arm_goal'])
    return normalize_angle(action['base_conf'][2] + math.atan2(local[1], local[0]))


def build_scene(plan, actions, config=None, offset=(0.0, 0.0)):
    """
    Describe every box and object to spawn, in the Gazebo world frame.

    actions must already be anchored (odom frame). offset is the robot spawn
    position in the world, so world = odom + offset.
    """
    config = config or dict(DEFAULT_CONFIG)
    anchor = plan_anchor(plan, actions)
    transform = make_transform(anchor)
    yaw0 = transform(0.0, 0.0, 0.0)[2]
    ox, oy = float(offset[0]), float(offset[1])
    raw = plan.get('scene') or {}
    surface = config['surface_height']

    boxes = []
    for item in raw.get('furniture', []):
        x, y, _ = transform(*item['pose'])
        if item.get('is_region', item['name'] in raw.get('regions', {})):
            if config['surface_mode'] == 'full':
                boxes.append(_box(item['name'], 'surface', x + ox, y + oy, yaw0,
                                  item['size'], surface))
            elif config['show_regions']:
                boxes.append(_box(item['name'], 'region', x + ox, y + oy, yaw0,
                                  item['size'], config['region_plate_height'],
                                  collision=False))
        else:
            height = config['obstacle_heights'].get(item['name'], config['obstacle_height'])
            boxes.append(_box(item['name'], 'obstacle', x + ox, y + oy, yaw0,
                              item['size'], height))

    sizes = {o['name']: o.get('size') for o in raw.get('objects', [])}
    first_pick = {}
    places = []
    for action in actions:
        if action['type'] == 'pick':
            first_pick.setdefault(action['obj'], action)
        elif action['type'] == 'place':
            places.append(action)

    starts = {}
    for item in raw.get('objects', []):
        x, y, _ = transform(*item['pose'])
        starts[item['name']] = (x, y)
    for name, action in first_pick.items():
        if name not in starts and action.get('object_pose') is not None:
            starts[name] = tuple(action['object_pose'])
    if not starts:
        raise SceneError('plan has no objects to spawn')

    objects = []
    for name in sorted(starts):
        x, y = starts[name]
        edge = config['object_size']
        if edge is None:
            footprint = sizes.get(name) or [0.03, 0.03]
            edge = float(min(footprint))
        yaw = _pick_yaw(first_pick[name]) if name in first_pick else yaw0
        objects.append({
            'name': name,
            'x': x + ox, 'y': y + oy,
            'z': surface + config['spawn_clearance'],
            'yaw': yaw,
            'size': float(edge),
        })
        if config['surface_mode'] == 'pedestal':
            p = config['pick_pedestal_size']
            boxes.append(_box('pick_stand_' + name, 'pick_stand', x + ox, y + oy, yaw,
                              (p, p), surface))

    if config['surface_mode'] == 'pedestal':
        p = config['place_pedestal_size']
        for index, action in enumerate(places):
            x, y = action['object_pose']
            boxes.append(_box('place_stand_{}_{}'.format(index, action['obj']),
                              'place_stand', x + ox, y + oy, yaw0, (p, p), surface))

    return {
        'problem': plan.get('problem', '?'),
        'anchor': anchor,
        'boxes': boxes,
        'objects': objects,
        'expected_final': expected_final_poses(actions, offset),
    }


def expected_final_poses(actions, offset=(0.0, 0.0)):
    """World (x, y) where each object should end up: its last place pose."""
    result = {}
    for action in actions:
        if action['type'] == 'place' and action.get('object_pose') is not None:
            x, y = action['object_pose']
            result[action['obj']] = (x + offset[0], y + offset[1])
    return result


# --------------------------------------------------------------------------
# SDF generation

COLORS = {
    'obstacle': '0.45 0.45 0.45 1',
    'surface': '0.6 0.45 0.3 1',
    'region': '0.8 0.8 0.5 0.6',
    'pick_stand': '0.3 0.3 0.8 1',
    'place_stand': '0.2 0.7 0.2 1',
}


def _fmt(values):
    return ' '.join('{:.6g}'.format(float(v)) for v in values)


def scene_model_sdf(boxes, model_name='planner_scene'):
    """One static model holding every furniture box, pedestal and plate."""
    links = []
    for box in boxes:
        sx, sy, sz = box['size']
        geometry = '<geometry><box><size>{}</size></box></geometry>'.format(_fmt((sx, sy, sz)))
        color = COLORS.get(box['kind'], '0.5 0.5 0.5 1')
        collision = ''
        if box['collision']:
            collision = '<collision name="collision">{}</collision>'.format(geometry)
        links.append(
            '    <link name="{name}">\n'
            '      <pose>{pose}</pose>\n'
            '      {collision}\n'
            '      <visual name="visual">{geometry}'
            '<material><ambient>{color}</ambient><diffuse>{color}</diffuse></material>'
            '</visual>\n'
            '    </link>'.format(
                name=box['name'],
                pose=_fmt((box['x'], box['y'], box['z'] + sz / 2.0, 0, 0, box['yaw'])),
                collision=collision, geometry=geometry, color=color,
            )
        )
    return (
        '<?xml version="1.0"?>\n<sdf version="1.6">\n'
        '  <model name="{}">\n    <static>true</static>\n{}\n  </model>\n</sdf>\n'
    ).format(model_name, '\n'.join(links))


def object_model_sdf(obj, config=None):
    """Return the SDF of a graspable cube with the attachment plugin."""
    config = config or dict(DEFAULT_CONFIG)
    edge = obj['size']
    mass = config['object_mass']
    inertia = mass * edge * edge / 6.0
    return """<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{name}">
    <link name="link">
      <pose>0 0 {half} 0 0 0</pose>
      <inertial>
        <mass>{mass}</mass>
        <inertia>
          <ixx>{i}</ixx><iyy>{i}</iyy><izz>{i}</izz>
          <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry><box><size>{size}</size></box></geometry>
        <surface>
          <friction><ode><mu>10.0</mu><mu2>10.0</mu2></ode></friction>
          <contact><ode><kp>50000</kp><kd>100</kd><min_depth>0.001</min_depth>
          <max_vel>0.01</max_vel></ode></contact>
        </surface>
      </collision>
      <visual name="visual">
        <geometry><box><size>{size}</size></box></geometry>
        <material><ambient>0.9 0.2 0.1 1</ambient><diffuse>0.9 0.2 0.1 1</diffuse></material>
      </visual>
    </link>
    <plugin name="{name}_attachment" filename="librobot_object_attachment.so">
      <object_link>link</object_link>
      <parent_link>{parent}</parent_link>
      <grasp_offset>{offset}</grasp_offset>
      <max_grasp_distance>{dist}</max_grasp_distance>
    </plugin>
  </model>
</sdf>
""".format(
        name=obj['name'], half='{:.6g}'.format(edge / 2.0), mass=mass,
        i='{:.6g}'.format(inertia), size=_fmt((edge, edge, edge)),
        parent=config['parent_link'], offset=_fmt(config['grasp_offset']),
        dist=config['max_grasp_distance'],
    )


def write_scene_files(scene, config, directory):
    """Write SDF files; return (scene_sdf_or_None, [(object, sdf_path)])."""
    os.makedirs(directory, exist_ok=True)
    scene_path = None
    if scene['boxes']:
        scene_path = os.path.join(directory, 'planner_scene.sdf')
        with open(scene_path, 'w', encoding='utf-8') as file:
            file.write(scene_model_sdf(scene['boxes']))
    objects = []
    for obj in scene['objects']:
        path = os.path.join(directory, '{}.sdf'.format(obj['name']))
        with open(path, 'w', encoding='utf-8') as file:
            file.write(object_model_sdf(obj, config))
        objects.append((obj, path))
    return scene_path, objects


def prepare_plan(plan_file, config=None, offset=(0.0, 0.0)):
    """Load, validate and anchor a plan, then describe its scene."""
    from robot_task_system import plan_parser

    plan, actions = plan_parser.load_and_validate(plan_file)
    anchor_actions(actions, plan_anchor(plan, actions))
    return plan, actions, build_scene(plan, actions, config, offset)


def describe(scene):
    lines = ['Scene for {}:'.format(scene['problem'])]
    for box in scene['boxes']:
        lines.append('  {:<12} {:<24} x={:+.3f} y={:+.3f} size={}'.format(
            box['kind'], box['name'], box['x'], box['y'], _fmt(box['size'])))
    for obj in scene['objects']:
        lines.append('  {:<12} {:<24} x={:+.3f} y={:+.3f} yaw={:+.3f}'.format(
            'object', obj['name'], obj['x'], obj['y'], obj['yaw']))
    for name, (x, y) in sorted(scene['expected_final'].items()):
        lines.append('  {:<12} {:<24} x={:+.3f} y={:+.3f}'.format('goal', name, x, y))
    return '\n'.join(lines)


def main(argv=None):
    """CLI: preview the scene a plan will produce (no ROS needed)."""
    import argparse

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('plan_file')
    parser.add_argument('--config', default=None, help='scene YAML')
    parser.add_argument('--write', default=None, help='directory for SDF files')
    args = parser.parse_args(argv)

    config = load_config(args.config)
    _, _, scene = prepare_plan(args.plan_file, config)
    print(describe(scene))
    if args.write:
        write_scene_files(scene, config, args.write)
        print('SDF files written to', args.write)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

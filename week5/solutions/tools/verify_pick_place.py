"""Run a complete plan in an isolated, headless Gazebo instance and check it.

Run after building and sourcing the workspace:

    python3 tools/verify_pick_place.py                      # verified default plan
    python3 tools/verify_pick_place.py --map corridor
    python3 tools/verify_pick_place.py --map at_work --timeout 2400
    python3 tools/verify_pick_place.py --plan /abs/path/plan.json

Checks that every object follows the gripper without drifting while held,
and ends up on its place stand.
"""

import argparse
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

ROBOT = 'turtlebot3_manipulation_system'
# The manipulator logs 'Received PICK_x for object "x"' before it calls that
# object's attach/detach service, whose reply is logged as 'Object attached to'
# or 'Object released;'.
EVENT = re.compile(r'Received \S+ for object "([^"]+)"|\]: Object (attached to|released;)')
FRAMES = {
    'attached to': ROBOT + '::link5',
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--map', help='map name in config/plans, e.g. corridor')
    group.add_argument('--plan', help='absolute path to a plan JSON')
    parser.add_argument('--record-bag', help='reserved for TODO-W5-03 recording support')
    parser.add_argument('--timeout', type=float, default=None,
                        help='seconds (default: 480 + 240 per manipulation)')
    args = parser.parse_args()
    if args.record_bag is not None:
        parser.error(
            'TODO-W5-03: implement rosbag2 recording, bag info and isolated playback; '
            'no simulation has been started.')
    return args


def resolve_plan(args, share):
    if args.plan:
        return os.path.abspath(args.plan)
    if args.map:
        return os.path.join(share, 'config', 'plans', args.map + '.json')
    return os.path.join(share, 'config', 'plan_pick_place.json')


def entity_position(node, client, name, frame):
    from gazebo_msgs.srv import GetEntityState
    import rclpy

    request = GetEntityState.Request()
    request.name = name
    request.reference_frame = frame
    future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future, timeout_sec=2)
    if future.done() and future.result() is not None and future.result().success:
        p = future.result().state.pose.position
        return (p.x, p.y, p.z)
    return None


def main():
    args = parse_args()
    from ament_index_python.packages import get_package_share_directory
    from gazebo_msgs.srv import GetEntityState
    import rclpy
    from robot_task_system import scene as scene_builder

    share = get_package_share_directory('robot_task_system')
    plan_file = resolve_plan(args, share)
    config = scene_builder.load_config(os.path.join(share, 'config', 'scene.yaml'))
    _, actions, scene = scene_builder.prepare_plan(plan_file, config)
    expected = scene['expected_final']
    manipulations = sum(1 for a in actions if a['type'] != 'move_base')
    timeout = args.timeout or 480 + 240 * manipulations
    print('Plan {}: {} objects, {} manipulations, timeout {:.0f} s'.format(
        plan_file, len(expected), manipulations, timeout), flush=True)

    workspace = Path(__file__).resolve().parents[1]
    output = workspace / 'log' / 'pick_place_verification'
    output.mkdir(parents=True, exist_ok=True)
    world = ET.parse(str(Path(get_package_share_directory('turtlebot3_gazebo')) /
                         'worlds' / 'empty_world.world'))
    plugin = ET.SubElement(world.getroot().find('world'), 'plugin', {
        'name': 'verification_state', 'filename': 'libgazebo_ros_state.so',
    })
    ET.SubElement(ET.SubElement(plugin, 'ros'), 'namespace').text = '/gazebo'
    ET.SubElement(plugin, 'update_rate').text = '20.0'
    world_path = output / 'verification.world'
    world.write(world_path, encoding='utf-8', xml_declaration=True)

    # Keep this test independent of any simulation the user already has open.
    os.environ['ROS_DOMAIN_ID'] = '76'
    os.environ['ROS_LOCALHOST_ONLY'] = '1'
    os.environ['GAZEBO_MASTER_URI'] = 'http://127.0.0.1:11476'
    os.environ['ROS_LOG_DIR'] = str(output / 'ros')
    os.environ['GAZEBO_MODEL_DATABASE_URI'] = ''
    log_path = output / 'launch.log'
    rclpy.init()
    node = rclpy.create_node('pick_place_verification')
    state = node.create_client(GetEntityState, '/gazebo/get_entity_state')
    process = None
    try:
        with log_path.open('w') as log:
            process = subprocess.Popen([
                'ros2', 'launch', 'robot_task_system', 'pick_place.launch.py',
                'gui:=false', 'world:=' + str(world_path), 'plan_file:=' + plan_file,
            ], cwd=workspace, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + timeout
            seen = set()
            episodes = {}   # (object, event number) -> [positions relative to holder]
            released = set()
            while time.monotonic() < deadline:
                text = log_path.read_text(errors='replace')
                for marker in ('Object attachment ready', 'Dispatched PICK', 'Dispatched PLACE',
                               'All actions completed successfully.'):
                    if marker in text and marker not in seen:
                        print(marker, flush=True)
                        seen.add(marker)
                if ('Action failed:' in text or 'failed at ' in text or
                        'Failed loading controller' in text or 'TASK FAILED' in text or process.poll() is not None):
                    raise RuntimeError('Simulation failed; inspect ' + str(log_path))

                holders = {}
                obj = None
                for number, match in enumerate(EVENT.finditer(text)):
                    if match.group(1) is not None:
                        obj = match.group(1)
                        continue
                    event = match.group(2)
                    if obj is None:
                        continue
                    holders[obj] = (number, event)
                    if event == 'released;':
                        released.add(obj)
                for obj, (number, event) in holders.items():
                    if event in FRAMES:
                        key = (obj, number)
                        if key not in episodes:
                            print('{} {} {}'.format(obj, event, FRAMES[event]), flush=True)
                            episodes[key] = []
                        p = entity_position(node, state, obj, FRAMES[event])
                        if p is not None:
                            episodes[key].append(p)

                if 'All actions completed successfully.' in seen:
                    assert released == set(expected), 'Not released: {}'.format(
                        sorted(set(expected) - released))
                    drift = 0.0
                    for (obj, _), samples in episodes.items():
                        if len(samples) >= 2:
                            drift = max(drift, max(math.dist(samples[0], p) for p in samples))
                    assert drift < 0.01, 'An object drifted while held: {:.4f} m'.format(drift)
                    time.sleep(1)
                    for obj, (x, y) in sorted(expected.items()):
                        p = entity_position(node, state, obj, 'world')
                        assert p is not None, '{} disappeared'.format(obj)
                        error = math.hypot(p[0] - x, p[1] - y)
                        assert error < 0.04, '{} missed its place stand by {:.3f} m'.format(
                            obj, error)
                        assert 0.045 < p[2] < 0.09, (
                            '{} did not settle on the stand: z={:.3f}'.format(obj, p[2]))
                        print('  {} final ({:.4f}, {:.4f}, {:.4f}), error {:.4f} m'.format(
                            obj, p[0], p[1], p[2], error), flush=True)
                    print('PASS: {} objects placed; max held drift {:.6f} m'.format(
                        len(expected), drift), flush=True)
                    return
                time.sleep(0.5)
            raise RuntimeError('Simulation timed out; inspect ' + str(log_path))
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

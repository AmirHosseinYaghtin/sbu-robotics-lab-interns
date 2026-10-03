"""Run the complete pick/place plan in an isolated, headless Gazebo instance.

Run after building and sourcing the workspace: python3 tools/verify_pick_place.py
"""

import math
import os
from pathlib import Path
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
from gazebo_msgs.srv import GetEntityState
import rclpy


def main():
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
                'gui:=false', 'world:=' + str(world_path),
            ], cwd=workspace, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + 480
            seen = set()
            held_samples = []
            while time.monotonic() < deadline:
                text = log_path.read_text(errors='replace')
                for marker in (
                    'Object attachment ready', 'Dispatched PICK', 'ATTACH_OBJECT',
                    'Object attached to', 'Completed PICK', 'Dispatched PLACE',
                    'DETACH_OBJECT', 'Object released', 'All actions completed successfully.',
                ):
                    if marker in text and marker not in seen:
                        print(marker, flush=True)
                        seen.add(marker)
                if ('Action failed:' in text or 'failed at ' in text or
                        'Failed loading controller' in text or process.poll() is not None):
                    raise RuntimeError('Simulation failed; inspect ' + str(log_path))

                if 'Object attached to' in seen and 'Object released' not in seen:
                    request = GetEntityState.Request()
                    request.name = 'cube1'
                    request.reference_frame = 'turtlebot3_manipulation_system::link5'
                    future = state.call_async(request)
                    rclpy.spin_until_future_complete(node, future, timeout_sec=2)
                    if future.done() and future.result().success:
                        p = future.result().state.pose.position
                        held_samples.append((p.x, p.y, p.z))

                if 'All actions completed successfully.' in seen:
                    assert 'Object attached to' in seen and 'Object released' in seen
                    assert len(held_samples) >= 2, 'No measurements of the attached cube'
                    first = held_samples[0]
                    drift = max(math.dist(first, p) for p in held_samples)
                    assert drift < 0.01, 'Cube drifted relative to the gripper: {}'.format(drift)
                    time.sleep(1)
                    request = GetEntityState.Request()
                    request.name = 'cube1'
                    request.reference_frame = 'world'
                    future = state.call_async(request)
                    rclpy.spin_until_future_complete(node, future, timeout_sec=3)
                    assert future.done() and future.result().success, 'Cube disappeared'
                    p = future.result().state.pose.position
                    error = math.hypot(p.x + 1.27, p.y - 1.246)
                    assert error < 0.04, 'Cube missed the place stand: {}'.format(error)
                    assert 0.045 < p.z < 0.09, 'Cube did not settle on the stand: {}'.format(p.z)
                    print('PASS: pick/place completed; held drift {:.6f} m; '
                          'final cube ({:.4f}, {:.4f}, {:.4f})'.format(
                              drift, p.x, p.y, p.z), flush=True)
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

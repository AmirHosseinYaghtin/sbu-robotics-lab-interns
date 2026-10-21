"""Replay an actual bag on isolated ROS domain 77, with no robot controllers.

Checks recorded task completion and odometry/TF/joint-state messages.
Does not execute the robot or prove that replay reproduces physics.
"""
import argparse
import json
import os
import signal
import subprocess
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bag')
    parser.add_argument('--timeout', type=float, default=600.0)
    args = parser.parse_args()
    os.environ['ROS_DOMAIN_ID'] = '77'
    os.environ['ROS_LOCALHOST_ONLY'] = '1'
    import rclpy
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import JointState
    from std_msgs.msg import String
    from tf2_msgs.msg import TFMessage
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
    rclpy.init()
    node = rclpy.create_node('week05_bag_verifier')
    counts = dict(odom=0, tf=0, joints=0)
    states = []
    def status(message):
        states.append(json.loads(message.data))
    def count(key):
        def callback(message):
            counts[key] += 1
        return callback
    status_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE,
                            durability=DurabilityPolicy.TRANSIENT_LOCAL)
    sensor_qos = QoSProfile(depth=100, reliability=ReliabilityPolicy.BEST_EFFORT)
    subscriptions = [
        node.create_subscription(String, '/task/status', status, status_qos),
        node.create_subscription(Odometry, '/odom', count('odom'), sensor_qos),
        node.create_subscription(TFMessage, '/tf', count('tf'), sensor_qos),
        node.create_subscription(JointState, '/joint_states', count('joints'), sensor_qos)]
    process = None
    log_path = Path(args.bag).resolve().parent / 'week05_playback.log'
    try:
        with log_path.open('w') as log:
            process = subprocess.Popen(['ros2', 'bag', 'play', str(Path(args.bag).resolve()),
                                        '--clock', '--rate', '5.0', '--delay', '2.0'],
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + args.timeout
            while process.poll() is None and time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=0.1)
            if process.poll() is None:
                raise RuntimeError('Bag playback timeout; inspect ' + str(log_path))
            for _ in range(20):
                rclpy.spin_once(node, timeout_sec=0.05)
            if process.returncode != 0:
                raise RuntimeError('Bag playback failed; inspect ' + str(log_path))
            if not any(s['task_state'] == 'COMPLETED' and
                       s['completed_actions'] == s['total_actions'] > 0 for s in states):
                raise RuntimeError('Bag did not replay a completed task')
            if not all(counts.values()):
                raise RuntimeError('Missing recorded data: ' + str(counts))
            print('PASS: actual bag replayed COMPLETED task, odometry, TF, joint states:', counts)
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        for subscription in subscriptions:
            node.destroy_subscription(subscription)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

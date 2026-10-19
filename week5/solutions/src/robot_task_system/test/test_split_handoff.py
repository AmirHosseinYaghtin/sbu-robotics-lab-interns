"""Retained behavior at the three unfinished feature boundaries."""
from pathlib import Path

import pytest
import rclpy
from rclpy.parameter import Parameter

from robot_task_system.robot_controller import RobotController
from robot_task_system.task_controller import TaskController


@pytest.mark.parametrize('reverse', [False, True])
def test_fixed_speed_final_approach_keeps_direction_and_limit(reverse):
    rclpy.init()
    base = RobotController()
    try:
        base.current_x = base.current_y = base.current_yaw = 0.0
        base.last_odom_time = base.get_clock().now()
        base.start_trajectory('MOVE', [(-0.1 if reverse else 0.1, 0.0, 0.0)], reverse)
        commands = []
        base.cmd_vel_publisher.publish = commands.append
        base.control_loop()
        assert 0.0 < abs(commands[-1].linear.x) <= 0.15
        assert (commands[-1].linear.x < 0.0) == reverse
    finally:
        base.destroy_node()
        rclpy.shutdown()


def test_existing_arm_settings_remain_frozen_until_parameter_task_is_done():
    from robot_task_system.manipulator_controller import ManipulatorController
    rclpy.init()
    arm = ManipulatorController()
    try:
        arm.status = arm.IDLE
        before = arm.get_parameter('max_joint_speed').value
        result = arm.set_parameters([Parameter('max_joint_speed', value=0.1)])[0]
        assert not result.successful
        assert arm.get_parameter('max_joint_speed').value == before
    finally:
        arm.destroy_node()
        rclpy.shutdown()


def test_full_task_starts_and_dispatches_without_external_status_feature():
    plan = Path(__file__).resolve().parents[1] / 'config/plan_pick_place.json'
    rclpy.init()
    task = TaskController(parameter_overrides=[Parameter('plan_file', value=str(plan))])
    try:
        assert task.startup_ok
        assert task.state.task_state == 'IDLE'
        assert task.state.total_actions == len(task.action_queue) > 0
        task.move_client.server_is_ready = lambda: True
        sent = []
        from rclpy.task import Future
        task.move_client.send_goal_async = lambda goal, **kwargs: sent.append(goal) or Future()
        task.try_dispatch_next_action()
        assert task.state.task_state == 'EXECUTING'
        assert task.state.completed_actions == 0
        assert len(sent) == 1
        assert sent[0].command.waypoints
        assert task.publish_status() is None
    finally:
        task.destroy_node()
        rclpy.shutdown()

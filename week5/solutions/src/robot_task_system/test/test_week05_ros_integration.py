"""Actual ROS/DDS integration tests, no Gazebo required.

Run after colcon build and sourcing install/setup.bash. These are NOT run by
run_offline_tests.py, and do not verify robot physics or the C++ plugin.
"""
from pathlib import Path
import time

import pytest
rclpy = pytest.importorskip('rclpy')
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_srvs.srv import Trigger
from robot_task_interfaces.action import MoveTo, Manipulate
from robot_task_interfaces.msg import MoveCommand, Waypoint, ManipulatorCommand, ArmWaypoint
from robot_task_system.robot_controller import RobotController
from robot_task_system.manipulator_controller import ManipulatorController
from robot_task_system.task_controller import TaskController


def spin_until(executor, predicate, timeout=8.0):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        executor.spin_once(timeout_sec=0.05)
    assert predicate(), 'ROS integration condition timed out'


@pytest.fixture
def graph():
    rclpy.init()
    executor = SingleThreadedExecutor()
    base = RobotController()
    caller = Node('week05_integration_client')
    executor.add_node(base)
    executor.add_node(caller)
    client = ActionClient(caller, MoveTo, '/move_to')
    spin_until(executor, client.server_is_ready)
    yield executor, base, caller, client
    client.destroy()
    executor.shutdown()
    base.destroy_node()
    caller.destroy_node()
    rclpy.shutdown()


def goal(x=1.0):
    return MoveTo.Goal(command=MoveCommand(action_label='MOVE_BASE',
        waypoints=[Waypoint(x=x, y=0.0, theta=0.0)]))


def accept(executor, client, request):
    future = client.send_goal_async(request)
    spin_until(executor, future.done)
    assert future.result().accepted
    return future.result()


def test_ros_no_odom_aborts_with_reason(graph):
    executor, base, _, client = graph
    handle = accept(executor, client, goal())
    base.odom_deadline = base.get_clock().now() - Duration(seconds=1.0)
    future = handle.get_result_async()
    spin_until(executor, future.done)
    assert future.result().status == 6
    assert not future.result().result.success
    assert 'no /odom' in future.result().result.message
    assert not base.moving


def test_ros_cancel_returns_canceled(graph):
    executor, base, _, client = graph
    handle = accept(executor, client, goal())
    cancel = handle.cancel_goal_async()
    result = handle.get_result_async()
    spin_until(executor, lambda: cancel.done() and result.done())
    assert cancel.result().goals_canceling
    assert result.result().status == 5
    assert not base.moving


def test_ros_success_and_feedback(graph):
    executor, base, _, client = graph
    base.current_x = base.current_y = base.current_yaw = 0.0
    base.last_odom_time = base.get_clock().now()
    feedback = []
    future = client.send_goal_async(goal(0.0), feedback_callback=feedback.append)
    spin_until(executor, future.done)
    result = future.result().get_result_async()
    spin_until(executor, result.done)
    assert result.result().status == 4
    assert result.result().result.success
    assert feedback


def test_ros_invalid_path_rejected(graph):
    executor, _, _, client = graph
    future = client.send_goal_async(MoveTo.Goal(command=MoveCommand()))
    spin_until(executor, future.done)
    assert not future.result().accepted


def test_ros_software_stop_aborts_and_latches(graph):
    executor, base, caller, client = graph
    handle = accept(executor, client, goal())
    service = caller.create_client(Trigger, '/robot_controller/emergency_stop')
    spin_until(executor, service.service_is_ready)
    stop = service.call_async(Trigger.Request())
    result = handle.get_result_async()
    spin_until(executor, lambda: stop.done() and result.done())
    assert stop.result().success
    assert result.result().status in (5, 6)
    assert not base.moving
    reject = client.send_goal_async(goal())
    spin_until(executor, reject.done)
    assert not reject.result().accepted


def test_ros_base_failure_stops_task_before_pick(graph):
    executor, base, _, _ = graph
    plan = Path(__file__).resolve().parents[1] / 'config/plan_pick_place.json'
    task = TaskController(parameter_overrides=[Parameter('plan_file', value=str(plan))])
    assert task.startup_ok
    executor.add_node(task)
    try:
        spin_until(executor, lambda: base.moving)
        base.odom_deadline = base.get_clock().now() - Duration(seconds=1.0)
        spin_until(executor, lambda: task.state.task_state == 'FAILED')
        assert task.state.completed_actions == 0
        assert len(task.action_queue) == task.state.total_actions
        assert task.action_queue[1]['type'] == 'pick'
        assert 'no /odom' in task.state.message
    finally:
        executor.remove_node(task)
        task.destroy_node()


def test_ros_task_cancel_never_dispatches_pick(graph):
    executor, _, caller, _ = graph
    plan = Path(__file__).resolve().parents[1] / 'config/plan_pick_place.json'
    task = TaskController(parameter_overrides=[Parameter('plan_file', value=str(plan))])
    executor.add_node(task)
    try:
        spin_until(executor, lambda: task.goal_handle is not None)
        service = caller.create_client(Trigger, '/task/cancel')
        spin_until(executor, service.service_is_ready)
        future = service.call_async(Trigger.Request())
        spin_until(executor, lambda: future.done() and task.state.task_state == 'CANCELED')
        assert task.state.completed_actions == 0
        assert len(task.action_queue) == task.state.total_actions
    finally:
        executor.remove_node(task)
        task.destroy_node()


def test_ros_manipulation_transport_with_mocked_actuators():
    # Real ROS Action protocol; actuator/TF methods deliberately mocked here.
    rclpy.init()
    executor = SingleThreadedExecutor()
    arm = ManipulatorController()
    caller = Node('week05_arm_integration_client')
    arm.status = arm.IDLE
    arm.joint_positions = dict(zip(arm.joint_names, arm.home))
    arm.target_in_arm_frame = lambda command: (0.20, 0.0)
    arm.send_arm = lambda points: setattr(arm, 'step_deadline', arm.now_seconds() + 5.0)
    arm.arm_reached = lambda: True
    arm.send_gripper = lambda command: setattr(arm, 'step_deadline', arm.now_seconds() + 5.0)
    arm.gripper_finished = lambda command: True
    arm.listen_for_commands()
    executor.add_node(arm)
    executor.add_node(caller)
    client = ActionClient(caller, Manipulate, '/manipulate')
    try:
        spin_until(executor, client.server_is_ready)
        command = ManipulatorCommand(action_type='pick', action_label='PICK_cube1',
            object_name='cube1', frame_id='odom', target_x=0.20, target_y=0.0,
            arm_start=[0.0]*3, arm_goal=[0.0]*3,
            trajectory=[ArmWaypoint(joints=[0.0]*3)])
        feedback = []
        sent = client.send_goal_async(Manipulate.Goal(command=command), feedback_callback=feedback.append)
        spin_until(executor, sent.done)
        result = sent.result().get_result_async()
        spin_until(executor, result.done)
        assert result.result().status == 4
        assert arm.held_object == 'cube1'
        assert feedback
    finally:
        client.destroy()
        executor.shutdown()
        arm.destroy_node()
        caller.destroy_node()
        rclpy.shutdown()

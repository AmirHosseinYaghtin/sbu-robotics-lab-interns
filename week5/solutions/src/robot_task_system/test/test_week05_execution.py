"""Unit tests of task lifecycle, cancellation, failure, and limits.

These run with ROS on Ubuntu or explicit doubles via tools/run_offline_tests.py.
"""
import time
from collections import deque
from types import SimpleNamespace as NS

import pytest
import rclpy
from rclpy.parameter import Parameter
from rclpy.task import Future
from rclpy.action import GoalResponse, CancelResponse
from std_srvs.srv import Trigger
from robot_task_interfaces.action import MoveTo
from robot_task_interfaces.msg import MoveCommand, Waypoint
from robot_task_system.execution_state import TaskState
from robot_task_system.robot_controller import RobotController
from robot_task_system.manipulator_controller import ManipulatorController
from robot_task_system.task_controller import TaskController


def completed(value):
    future = Future()
    future.set_result(value)
    return future


@pytest.fixture
def base():
    rclpy.init()
    node = RobotController()
    yield node
    node.destroy_node()
    rclpy.shutdown()


@pytest.fixture
def arm():
    rclpy.init()
    node = ManipulatorController()
    node.joint_positions = dict(zip(node.joint_names, node.home))
    yield node
    node.destroy_node()
    rclpy.shutdown()


def request(x=0.0):
    return MoveTo.Goal(command=MoveCommand(
        action_label='MOVE_BASE', waypoints=[Waypoint(x=x, y=0.0, theta=0.0)]))


class Handle:
    def __init__(self, goal):
        self.request = goal
        self.is_cancel_requested = False
        self.is_active = True
        self.terminal = None
        self.feedback = []

    def succeed(self):
        self.terminal, self.is_active = 'SUCCEEDED', False

    def abort(self):
        self.terminal, self.is_active = 'ABORTED', False

    def canceled(self):
        self.terminal, self.is_active = 'CANCELED', False

    def publish_feedback(self, feedback):
        self.feedback.append(feedback)


def start(endpoint, goal):
    assert endpoint.goal(goal) == GoalResponse.ACCEPT
    handle = Handle(goal)
    coroutine = endpoint.execute(handle)
    coroutine.send(None)
    return handle, coroutine


def finish_coroutine(coroutine):
    with pytest.raises(StopIteration) as result:
        coroutine.send(None)
    return result.value.value


def test_task_success_counts_all_actions():
    state = TaskState('plan.json', 2)
    for label in ['MOVE', 'PICK']:
        state.begin(label)
        assert state.result(True)
    assert state.task_state == 'COMPLETED'
    assert state.completed_actions == 2


@pytest.mark.parametrize('canceled', [False, True])
def test_failure_or_external_cancel_never_advances(canceled):
    state = TaskState('plan', 2)
    state.begin('MOVE')
    assert not state.result(False, canceled, 'no odom')
    assert state.completed_actions == 0
    with pytest.raises(RuntimeError):
        state.begin('PICK')


@pytest.mark.parametrize('emergency,failure', [(False, False), (True, False), (False, True)])
def test_late_success_cannot_resume_stopped_task(emergency, failure):
    state = TaskState('plan', 2)
    state.begin('MOVE')
    state.stop('stop', emergency=emergency, failure=failure)
    assert not state.result(True)
    assert state.completed_actions == 1  # acknowledged success, but never dispatch next
    with pytest.raises(RuntimeError):
        state.begin('PICK')


def test_cancel_while_idle_is_terminal():
    state = TaskState('plan', 2)
    state.stop('cancel')
    assert state.task_state == 'CANCELED'


def test_busy_goal_rejected_until_result_is_consumed(base):
    handle, coroutine = start(base.execution, request(1.0))
    assert base.execution.goal(request()) == GoalResponse.REJECT
    base.complete_current_action()
    assert handle.terminal == 'SUCCEEDED'
    assert base.execution.goal(request()) == GoalResponse.REJECT
    assert finish_coroutine(coroutine).success
    assert not base.execution.reserved


@pytest.mark.parametrize('x', [float('nan'), float('inf')])
def test_nonfinite_goal_is_rejected(base, x):
    assert base.execution.goal(request(x)) == GoalResponse.REJECT


def test_empty_goal_rejected(base):
    assert base.execution.goal(MoveTo.Goal(command=MoveCommand())) == GoalResponse.REJECT


def test_base_cancel_stops_velocity_and_returns_canceled(base):
    handle, coroutine = start(base.execution, request(1.0))
    assert base.execution.cancel(handle) == CancelResponse.ACCEPT
    assert handle.terminal is None
    handle.is_cancel_requested = True
    base.control_loop()
    result = finish_coroutine(coroutine)
    assert handle.terminal == 'CANCELED'
    assert not result.success
    assert not base.moving
    assert base.status == base.IDLE


def test_real_controller_no_odom_failure_reaches_action_result(base):
    handle, coroutine = start(base.execution, request(1.0))
    from rclpy.duration import Duration
    base.odom_deadline = base.get_clock().now() - Duration(seconds=1.0)
    base.control_loop()  # actual no-/odom branch in existing controller
    base.control_loop()  # controlled stop, then result
    result = finish_coroutine(coroutine)
    assert handle.terminal == 'ABORTED'
    assert not result.success
    assert 'no /odom' in result.message
    assert base.status == base.ERROR
    assert not base.moving


def test_software_stop_latches_and_blocks_new_goals(base):
    handle, coroutine = start(base.execution, request(1.0))
    response = base.execution.emergency_stop(Trigger.Request(), Trigger.Response())
    assert response.success
    base.control_loop()
    assert not finish_coroutine(coroutine).success
    assert base.execution.goal(request()) == GoalResponse.REJECT
    assert base.reset_callback(Trigger.Request(), Trigger.Response()).success
    assert not base.execution.emergency


def test_base_feedback_preserves_full_path(base):
    base.start_trajectory('MOVE', [(1.0, 0.0, 0.0), (1.0, 2.0, 0.0)])
    base.current_x = base.current_y = 0.0
    feedback = base.move_feedback()
    assert feedback.distance_remaining == pytest.approx(3.0)
    assert feedback.current_waypoint == 1
    assert feedback.total_waypoints == 2






def test_arm_cancel_holds_and_preserves_attached_object(arm):
    arm.held_object = 'cube1'
    assert not arm.stop_for_cancel()  # hold must settle before acknowledgment
    arm.cancel_hold_until = time.monotonic() - 1.0
    assert arm.stop_for_cancel()
    assert arm.held_object == 'cube1'
    assert arm.status == arm.ERROR


def test_arm_stop_waits_for_pending_attachment(arm):
    arm.attachment_future = Future()
    arm.stop_for_cancel()
    arm.cancel_hold_until = time.monotonic() - 1.0
    assert not arm.stop_for_cancel()
    arm.attachment_future.set_result(Trigger.Response(success=True))
    assert arm.stop_for_cancel()


def test_arm_stop_waits_for_gripper_terminal_result(arm):
    canceled = []
    arm.gripper_handle = NS(cancel_goal_async=lambda: canceled.append(True) or Future())
    arm.gripper_goal_future = completed(None)
    arm.gripper_result = None
    arm.stop_for_cancel()
    arm.cancel_hold_until = time.monotonic() - 1.0
    assert not arm.stop_for_cancel()
    assert canceled == [True]
    assert not arm.stop_for_cancel()
    assert canceled == [True]
    arm.gripper_result = NS(status=5)
    assert arm.stop_for_cancel()


def test_bad_calibration_runtime_override_rejected(arm):
    arm.status = arm.IDLE
    before = arm.get_parameter('grasp_joints').value
    result = arm.set_parameters([Parameter('grasp_joints', value=[0.6, 0.0, 9.0])])[0]
    assert not result.successful
    assert arm.get_parameter('grasp_joints').value == before


class TaskHarness(TaskController):
    """Exercise actual client callbacks without constructing a ROS Node."""
    def __init__(self):
        self.state = TaskState('plan', 2)
        self.state.begin('MOVE')
        self.action_queue = deque([{'label': 'MOVE'}, {'label': 'PICK'}])
        self.goal_handle = self.goal_future = self.result_future = None
        self.cancel_future = self.cancel_started = None
        self.current_action = self.action_queue[0]
        self.stop_requests = {}
        self.stop_clients = []
        self.statuses = []

    def publish_status(self):
        self.statuses.append(self.state.snapshot())

    def get_logger(self):
        return NS(info=lambda *a: None, error=lambda *a: None, warning=lambda *a: None)


def test_client_cancel_before_goal_acceptance():
    task = TaskHarness()
    task.stop_task('cancel')
    canceled = []
    handle = NS(accepted=True, get_result_async=lambda: Future(),
                cancel_goal_async=lambda: canceled.append(True) or Future())
    task.goal_response(completed(handle))
    assert canceled == [True]
    assert task.state.task_state == 'CANCELING'
    task.action_result(completed(NS(status=5, result=NS(success=False, message='canceled'))))
    assert task.state.task_state == 'CANCELED'
    assert len(task.action_queue) == 2


def test_client_failure_does_not_pop_queue():
    task = TaskHarness()
    task.action_result(completed(NS(status=6, result=NS(success=False, message='stuck'))))
    assert task.state.task_state == 'FAILED'
    assert task.state.message == 'stuck'
    assert len(task.action_queue) == 2


def test_client_success_advances_once():
    task = TaskHarness()
    task.action_result(completed(NS(status=4, result=NS(success=True, message='completed'))))
    assert len(task.action_queue) == 1
    assert task.state.completed_actions == 1


def test_client_goal_rejection_stops_plan():
    task = TaskHarness()
    task.goal_response(completed(NS(accepted=False)))
    assert task.state.task_state == 'FAILED'
    assert len(task.action_queue) == 2


def test_cancel_transport_failure_remains_stopped():
    task = TaskHarness()
    task.stop_task('cancel')
    future = Future()
    future.set_exception(RuntimeError('disconnected'))
    task.cancel_response(future)
    assert task.state.task_state == 'CANCELING'
    assert len(task.action_queue) == 2


def test_timeout_reason_survives_cancel_acknowledgement():
    state = TaskState('plan', 2)
    state.begin('MOVE')
    state.stop('action timeout', failure=True)
    state.result(False, canceled=True, message='canceled')
    assert state.task_state == 'FAILED'
    assert 'action timeout' in state.message
    assert state.completed_actions == 0


def test_cancel_before_execute_starts_no_motion(base):
    endpoint = base.execution
    goal = request(1.0)
    assert endpoint.goal(goal) == GoalResponse.ACCEPT
    handle = Handle(goal)
    handle.is_cancel_requested = True
    coroutine = endpoint.execute(handle)
    coroutine.send(None)
    assert not base.moving
    base.control_loop()
    assert not finish_coroutine(coroutine).success
    assert handle.terminal == 'CANCELED'


def test_manipulator_server_readiness_follows_startup(arm):
    assert arm.execution.server is None
    arm.status = arm.IDLE
    arm.listen_for_commands()
    assert arm.execution.server is not None


def test_reset_rejected_while_goal_is_pending(base):
    _, coroutine = start(base.execution, request(1.0))
    assert not base.reset_callback(Trigger.Request(), Trigger.Response()).success
    base.execution.handle.is_cancel_requested = True
    base.control_loop()
    finish_coroutine(coroutine)


def test_reset_rejected_while_nested_gripper_pending(arm):
    arm.status = arm.ERROR
    arm.gripper_goal_future = Future()
    assert not arm.reset_callback(Trigger.Request(), Trigger.Response()).success
    arm.gripper_goal_future = completed(None)
    arm.gripper_handle = NS()
    arm.gripper_result = None
    assert not arm.reset_callback(Trigger.Request(), Trigger.Response()).success


def test_stop_exception_does_not_escape_timer(base):
    handle, coroutine = start(base.execution, request())
    base.execution.stop = lambda: (_ for _ in ()).throw(RuntimeError('actuator unavailable'))
    base.execution.request_stop('cancel')
    base.execution.stop_started = time.monotonic() - 16.0
    base.control_loop()
    result = finish_coroutine(coroutine)
    assert handle.terminal == 'ABORTED'
    assert 'stop unconfirmed' in result.message
    assert base.status == base.ERROR


def test_cancel_consumes_delayed_gripper_acceptance_once(arm):
    # A response is complete, but its executor callback has not run yet.
    result = Future()
    requests = []
    cancellations = []
    handle = NS(accepted=True,
                get_result_async=lambda: requests.append(True) or result,
                cancel_goal_async=lambda: cancellations.append(True) or Future())
    acceptance = completed(handle)
    arm.gripper_goal_future = acceptance
    arm.stop_for_cancel()
    arm.cancel_hold_until = time.monotonic() - 1.0
    assert not arm.stop_for_cancel()
    assert arm.gripper_handle is handle
    assert requests == [True]
    assert cancellations == [True]
    # The later executor callback must not create another result request.
    arm.gripper_goal_response(acceptance)
    assert requests == [True]
    assert not arm.stop_for_cancel()
    assert cancellations == [True]
    result.set_result(NS(status=5))
    assert arm.stop_for_cancel()


@pytest.mark.parametrize('response_error', [False, True])
def test_cancel_resolves_delayed_gripper_rejection(arm, response_error):
    acceptance = Future()
    if response_error:
        acceptance.set_exception(RuntimeError('goal response unavailable'))
    else:
        acceptance.set_result(NS(accepted=False))
    arm.gripper_goal_future = acceptance
    arm.stop_for_cancel()
    arm.cancel_hold_until = time.monotonic() - 1.0
    assert arm.stop_for_cancel()
    assert arm.gripper_result == 'rejected'
    arm.gripper_goal_response(acceptance)  # idempotent late callback
    assert arm.gripper_result == 'rejected'


@pytest.mark.parametrize('expired', [False, True])
def test_synchronous_cancel_exception_preserves_watchdog_fallback(expired):
    task = TaskHarness()
    task.state.stop('cancellation requested')
    task.controller_stop_required = False
    task.cancel_started = time.monotonic() - (30.0 if expired else 0.0)
    task.goal_handle = NS(cancel_goal_async=lambda: (
        _ for _ in ()).throw(RuntimeError('cancel transport unavailable')))
    task.try_dispatch_next_action()  # must not raise before the timeout check
    assert len(task.action_queue) == 2
    assert task.state.completed_actions == 0
    if expired:
        assert task.state.task_state == 'FAILED'
        assert task.state.action_state == 'STOP_UNCONFIRMED'
        assert task.controller_stop_required  # independent stop fallback invoked
    else:
        assert task.state.task_state == 'CANCELING'
        assert 'cancellation requested' in task.state.message
        assert 'Cancel transport error' in task.state.message



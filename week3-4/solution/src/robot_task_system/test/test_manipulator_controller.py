from action_msgs.msg import GoalStatus
import pytest
import rclpy
from robot_task_interfaces.msg import ArmWaypoint
from robot_task_interfaces.msg import ManipulatorCommand
from robot_task_interfaces.srv import GetRobotStatus
from robot_task_system.manipulator_controller import ManipulatorController
from robot_task_system.manipulator_controller import StepFailure
from std_srvs.srv import Trigger


class FakeResult:

    def __init__(self, position):
        self.position = position


class FakeGripperResult:

    def __init__(self, position):
        self.status = GoalStatus.STATUS_SUCCEEDED
        self.result = FakeResult(position)


@pytest.fixture
def node():
    rclpy.init()
    controller = ManipulatorController()
    yield controller
    controller.destroy_node()
    rclpy.shutdown()


def command(action_type='pick', obj='cube1'):
    message = ManipulatorCommand()
    message.action_type = action_type
    message.action_label = '{}_{}'.format(action_type.upper(), obj)
    message.object_name = obj
    message.frame_id = 'odom'
    message.target_x = 0.8
    message.target_y = 1.0
    message.arm_start = [0.0, 0.0, 0.0]
    message.arm_goal = [0.1, 0.2, 0.3]
    message.trajectory = [ArmWaypoint(joints=[0.0, 0.0, 0.0]), ArmWaypoint(joints=[0.1, 0.2, 0.3])]
    return message


def test_starts_in_starting_state(node):
    response = node.get_status_callback(GetRobotStatus.Request(), GetRobotStatus.Response())
    assert response.status == 'STARTING'
    assert response.current_action == 'NONE'


def test_startup_waits_for_arm_controller(node):
    node.joint_positions = {'joint1': 0.0, 'joint2': -1.0, 'joint3': 0.3, 'joint4': 0.7}
    node.gripper_client.server_is_ready = lambda: True

    node.arm_publisher.get_subscription_count = lambda: 0
    node.check_startup()
    assert node.status == 'STARTING'

    node.arm_publisher.get_subscription_count = lambda: 1
    node.check_startup()
    assert node.status == 'EXECUTING'
    assert node.current_action == 'STARTUP_HOME'


def test_valid_pick_command_passes_validation(node):
    node.validate_command(command())


def test_unknown_type_is_rejected(node):
    with pytest.raises(StepFailure):
        node.validate_command(command('wave'))


def test_wrong_joint_count_is_rejected(node):
    message = command()
    message.arm_goal = [0.1, 0.2]
    with pytest.raises(StepFailure):
        node.validate_command(message)


def test_empty_trajectory_is_rejected(node):
    message = command()
    message.trajectory = []
    with pytest.raises(StepFailure):
        node.validate_command(message)


def test_place_without_held_object_is_rejected(node):
    with pytest.raises(StepFailure):
        node.validate_command(command('place'))


def test_pick_while_holding_is_rejected(node):
    node.held_object = 'cube0'
    with pytest.raises(StepFailure):
        node.validate_command(command('pick'))


def test_object_in_reach_passes(node):
    node.check_reach((0.20, 0.0))
    node.check_reach((0.0, 0.20))


def test_object_out_of_reach_is_failure(node):
    with pytest.raises(StepFailure):
        node.check_reach((0.40, 0.0))


def test_pick_uses_planner_trajectory(node):
    node.status = node.IDLE
    node.joint_positions = {'joint1': 0.0, 'joint2': -1.0, 'joint3': 0.3, 'joint4': 0.7}
    node.target_in_arm_frame = lambda message: (0.20, 0.0)
    node.start_steps = lambda steps: setattr(node, 'steps', steps)
    node.command_callback(command())
    assert node.steps[1]['value'] == [[0.0, 0.0, 0.0, 0.0], [0.0, 0.1, 0.2, 0.3]]
    assert node.steps[2]['value'] == [[0.0, 0.688, -0.058, 0.94]]


def test_full_pick_runs_all_steps(node):
    results = []
    node.publish_result = results.append
    node.status = node.IDLE
    node.joint_positions = {'joint1': 0.0, 'joint2': -1.0, 'joint3': 0.3, 'joint4': 0.7}
    node.target_in_arm_frame = lambda message: (0.20, 0.0)
    node.gripper_client.server_is_ready = lambda: True

    sent = []

    def fake_arm(points):
        sent.append('arm')
        node.arm_goal = points[-1]
        node.joint_positions = dict(zip(node.joint_names, points[-1]))
        node.step_deadline = node.now_seconds() + 10.0

    def fake_gripper(command):
        sent.append(command)
        node.gripper_result = FakeGripperResult(0.005)
        node.step_deadline = node.now_seconds() + 10.0

    node.send_arm = fake_arm
    node.send_gripper = fake_gripper

    node.command_callback(command())
    for _ in range(20):
        node.control_loop()

    assert results == [True]
    assert node.held_object == 'cube1'
    assert node.status == 'IDLE'
    assert sent == ['open', 'arm', 'arm', 'close', 'arm', 'arm']


def test_empty_gripper_after_close_is_failure(node):
    node.gripper_result = FakeGripperResult(-0.010)
    with pytest.raises(StepFailure):
        node.gripper_finished('close')


def test_command_in_error_state_is_rejected(node):
    results = []
    node.publish_result = results.append
    node.status = node.ERROR
    node.command_callback(command())
    assert results == [False]


def test_reset_clears_error(node):
    node.status = node.ERROR
    node.held_object = 'cube1'
    response = node.reset_callback(Trigger.Request(), Trigger.Response())
    assert response.success
    assert node.status == 'IDLE'
    assert node.held_object is None

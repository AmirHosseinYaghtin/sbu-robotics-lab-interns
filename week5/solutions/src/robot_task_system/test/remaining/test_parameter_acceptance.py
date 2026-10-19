"""TODO-W5-02: enable these acceptance tests after implementing parameters."""
import pytest
import rclpy
from rclpy.parameter import Parameter
from robot_task_system.robot_controller import RobotController

pytestmark = pytest.mark.skip(reason="TODO-W5-02: parameter feature deferred")


@pytest.fixture
def base():
    rclpy.init()
    node = RobotController()
    yield node
    node.destroy_node()
    rclpy.shutdown()

@pytest.mark.parametrize('value', [-1.0, 0.0, float('nan'), float('inf')])
def test_invalid_speed_rejected_without_modifying_parameter(base, value):
    before = base.get_parameter('linear_speed').value
    result = base.set_parameters([Parameter('linear_speed', value=value)])[0]
    assert not result.successful
    assert base.get_parameter('linear_speed').value == before


def test_positive_speed_accepted_idle_but_not_during_move(base):
    assert base.set_parameters([Parameter('linear_speed', value=0.12)])[0].successful
    base.start_trajectory('MOVE', [(1.0, 0.0, 0.0)])
    assert not base.set_parameters([Parameter('linear_speed', value=0.13)])[0].successful


@pytest.mark.parametrize('speed', [0.01, 0.03, 0.15])
@pytest.mark.parametrize('reverse', [False, True])
def test_final_approach_never_exceeds_configured_linear_speed(base, speed, reverse):
    assert base.set_parameters([Parameter('linear_speed', value=speed)])[0].successful
    base.current_x = base.current_y = base.current_yaw = 0.0
    base.last_odom_time = base.get_clock().now()
    base.start_trajectory('MOVE', [(-0.1 if reverse else 0.1, 0.0, 0.0)], reverse)
    captured = []
    base.cmd_vel_publisher.publish = captured.append
    base.control_loop()
    command = captured[-1]
    magnitude = abs(command.linear.x)
    assert 0.0 < magnitude <= speed
    assert magnitude == pytest.approx(min(speed, max(base.MIN_FINAL_SPEED, 0.08)))
    assert (command.linear.x < 0.0) == reverse


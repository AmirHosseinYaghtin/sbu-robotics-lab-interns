import math

import pytest
from robot_task_system import planner_kinematics


def test_planner_fk_matches_reference_values():
    x, y = planner_kinematics.forward_kinematics([0.0, 0.0, 0.0])
    assert (x, y) == pytest.approx((0.45, 0.0))
    x, y = planner_kinematics.forward_kinematics([math.pi / 2.0, 0.0, 0.0])
    assert (x, y) == pytest.approx((0.0, 0.45))


def test_planner_fk_of_real_pick_goal_points_straight_ahead():
    x, y = planner_kinematics.forward_kinematics(
        [-0.3484236439517913, 0.713408911353669, 0.2890816306024251]
    )
    assert math.hypot(x, y) == pytest.approx(0.422, abs=1e-3)
    assert y == pytest.approx(0.0, abs=1e-3)

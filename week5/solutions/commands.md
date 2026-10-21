```
colcon build --symlink-install
source install/setup.bash
export TURTLEBOT3_MODEL=waffle
```
Then run one map at a time:

# Only the cube on its stand and the table, no obstacles
ros2 launch robot_task_system pick_place.launch.py map:=simple

# Pick-and-place with a shelf and two tables
ros2 launch robot_task_system pick_place.launch.py map:=pick_place

# Corridor
ros2 launch robot_task_system pick_place.launch.py map:=corridor

# Three cubes
ros2 launch robot_task_system pick_place.launch.py map:=multi_object

# at_work (5 objects, one at a time)
ros2 launch robot_task_system pick_place.launch.py map:=at_work

# Original default plan (no map:= needed)
ros2 launch robot_task_system pick_place.launch.py





To check that a map finishes on its own, run the verify script from the workspace folder. It starts the launch, waits, and reports pass or fail:
```
python3 tools/verify_pick_place.py --map at_work --timeout 1200
```

Arm motion fix: `continuous2d` describes a different planar arm, so its angles
are retained as plan metadata and no longer sent to OpenMANIPULATOR joint2/3/4.
The task/object order and base paths still come from the plan. Each pick/place
uses `clearance_joints` above the cube, the calibrated `grasp_joints` or
`place_joints`, the same clearance pose to lift/retreat, then `home_joints`.
Invalid ROS poses are rejected instead of clamped. The controller waits for the
trajectory's scheduled end and joint feedback before advancing to the next step.

These poses assume the default 5 cm pedestals and 3 cm cubes in `scene.yaml`.
Changing surface height, robot geometry or object size requires recalibration;
this fixed path is not a general collision-aware 3D motion planner.

After copying the changes into the Ubuntu workspace, rebuild and source it:

```bash
colcon build --symlink-install
source install/setup.bash
colcon test --packages-select robot_task_system
colcon test-result --verbose
ros2 launch robot_task_system pick_place.launch.py map:=at_work
```

Check the second cube visually: before placing it and after opening the gripper,
the arm should pass through `MOVE_CLEARANCE`/`RETREAT` with the fingers down and
in front of the robot. `tools/verify_pick_place.py` checks object attachment and
final placement; it does not verify mesh self-collisions. A traceback immediately
after Ctrl+C is an interruption, not evidence of the arm motion problem.

The pose geometry used for the regression checks follows the official
[ROBOTIS Humble URDF](https://github.com/ROBOTIS-GIT/turtlebot3_manipulation/blob/humble/turtlebot3_manipulation_description/urdf/open_manipulator_x.urdf.xacro).
The timing check follows the positions-only linear interpolation documented by
[ros2_control](https://control.ros.org/humble/doc/ros2_controllers/joint_trajectory_controller/doc/trajectory.html).

# Week 3-4: planner-driven mobile manipulation

This workspace executes a pick-and-place plan with a TurtleBot3 mobile base and
an OpenMANIPULATOR-X arm in Gazebo Classic. The robot follows the planned base
path, approaches the pick stand, grasps `cube1`, carries it to the place stand,
releases it, and returns the arm to its home configuration.

The main entry point is `pick_place.launch.py`. The included JSON plan can be
executed directly; generating another PDDLStream plan is a separate operation.
This document describes the current architecture, the simulated grasp fix,
installation and execution, diagnostic interfaces, and verification results.

## Tested environment and prerequisites

The implementation was built and exercised locally with:

- Ubuntu 22.04 inside WSL 2 on Windows, with WSLg available for graphical output.
- ROS 2 Humble.
- Gazebo Classic 11.10.2.
- TurtleBot3 manipulation packages containing the OpenMANIPULATOR-X model.
- The ROS 2 gripper action controller from `ros-humble-gripper-controllers`.

The C++ attachment plugin targets Gazebo Classic. Its build requires
`ament_cmake`, `gazebo_dev`, `gazebo_ros`, `rclcpp`, and `std_srvs`, with C++17
support. The Python task package also uses the ROS interfaces declared in
`src/robot_task_system/package.xml`. Use a ROS-enabled Linux environment for
building and running this workspace.

Install the TurtleBot3 manipulation simulation and its dependencies using the
[ROBOTIS manipulation instructions](https://emanual.robotis.com/docs/en/platform/turtlebot3/manipulation/).
The commands below assume that its built workspace is `~/turtlebot3_ws`.
If it is elsewhere, source that workspace's `install/setup.bash` instead.

Install the gripper controller if it is missing:

```bash
sudo apt install ros-humble-gripper-controllers
```

The gripper controller is also declared as a runtime dependency of
`robot_task_system`. Without it, the simulated gripper action server cannot
start even if the robot and arm appear in Gazebo.

## Workspace contents

- `src/robot_task_interfaces/`: custom messages for base and arm commands, and
  the `GetRobotStatus` service definition.
- `src/robot_task_system/robot_task_system/`: plan parsing, coordinate conversion,
  task dispatch, mobile-base control, manipulation sequencing, and monitoring.
- `src/robot_task_system/launch/`: the main manipulation launch and the earlier
  base-oriented launch.
- `src/robot_task_system/config/plan_pick_place.json`: the included planner output.
- `src/robot_task_system/config/pick_place.yaml`: parameters for the default
  simulated scene and controllers.
- `src/robot_task_system/config/error_plans/`: invalid plans used to exercise
  validation failures.
- `src/robot_task_system/models/`: the cube, pick stand, and place stand SDF files.
- `src/robot_task_system/test/`: tests for parsing, geometry, commands, and
  controller behavior.
- `src/robot_object_attachment/`: the C++ Gazebo plugin that creates and removes
  the temporary grasp joint.
- `planner_reference/export_plan.py`: an exporter for a separately configured
  PDDLStream `continuous2d` environment.
- `tools/verify_pick_place.py`: a complete headless simulation check.
- `run_simulation.sh`: the launch helper for a built workspace, including WSLg
  resource setup.

Generated `build/`, `install/`, and `log/` directories in this solution are
ignored by Git. They are local build products and execution records.
The shell helper is stored with LF line endings through `.gitattributes`.

## Architecture and execution flow

### Plan loading and validation

`plan_parser.py` reads the exported JSON and converts supported planner actions
into commands used by the execution system. The supported planner action names
are `move_base`, `pick_and_stow`, and the placement variants
`unstow_and_place` / `place_and_unstow`. The merged manipulation actions become
`pick` and `place` commands.

The parser preserves base waypoints and their headings, object names and poses,
grasp offsets, arm start and goal configurations, and arm trajectory waypoints.
Manipulation configurations must contain three planner joints, and the arm
trajectory must be nonempty with the same joint count at every waypoint.

Validation rejects empty executable plans, unsupported actions, missing
manipulation data, a second pick while an object is held, and placement of an
object that has not been picked. Separate unmerged `pick`, `stow`, `unstow`, and
`place` actions are rejected by this executor. A missing or invalid plan causes
the task controller to stop at startup; it does not substitute a fallback plan.

### Geometry preparation

`task_controller.py` can anchor the planner's first base pose to the odometry
origin. `plan_geometry.py` converts between local and world coordinates and
compares the planner arm endpoint with the supplied object pose.

The approach adjustment accounts for the configured arm reach and arm mounting
offset. It adjusts the preceding base goal to put the object within reach and
can insert a reverse `RETREAT` after manipulation. The included plan contains
four planner actions; with the default geometry preparation, the execution
queue also contains the retreat after the pick.

`planner_kinematics.py` implements the planar reference geometry used by the
planner, with link lengths of 0.23 m and 0.22 m. This reference geometry is used
for interpreting the planner output. The physical arm is commanded separately
through the ROS arm controller.

### Task dispatch and base control

The task controller sends one action at a time. It publishes base trajectories
on `/move_command` and manipulation commands on `/manipulator_command`, then
waits for a Boolean result on `/action_done`. It waits for a command subscriber
before dispatching, stops the queue on failure, and applies a configured action
timeout.

`robot_controller.py` follows base waypoints using `/odom` feedback and publishes
velocity commands on `/cmd_vel`. It handles the final heading and reverse
retreat motion, and reports failures for missing odometry, excessive execution
time, or insufficient movement progress. Its status states are `IDLE`,
`EXECUTING`, and `ERROR`.

The shared `/action_done` topic assumes a single task dispatcher with one action
in flight. Its Boolean message carries no action identifier, so this interface
is not intended for concurrent independent task execution.

### Arm and gripper control

`manipulator_controller.py` starts in `STARTING` while waiting for the arm
trajectory subscriber, gripper action server, and joint states. It then accepts
commands in `IDLE`, runs the manipulation steps in `EXECUTING`, and enters
`ERROR` if a step fails.

Planner joint configurations are mapped to `joint2`, `joint3`, and `joint4`;
`joint1` is supplied by the `fixed_joint1` parameter. The arm receives
`trajectory_msgs/msg/JointTrajectory` on `/arm_controller/joint_trajectory`.
Movement timing respects the configured maximum joint speed and minimum segment
duration. Joint-state feedback is used to check arrival at the arm goal.

The gripper uses `control_msgs/action/GripperCommand` at
`/gripper_controller/gripper_cmd`. The controller validates the object identity,
arm data, and target reach before starting a pick or place sequence.

## Cube ejection problem and implemented fix

### Observed behavior and mechanism

The original simulated grasp depended on finger contacts and friction. When
the fingers closed into the cube's collision geometry, contact forces could
eject the cube instead of carrying it. This behavior was consistent with
overlap and conflicting contact constraints during closure.

The cube's visual and collision dimensions are now both 0.03 m on each side.
Its mass is 0.02 kg. Matching the two geometries makes the visible cube agree
with the collision shape used by the simulator.

### Temporary attachment during the grasp

`models/cube.sdf` loads `librobot_object_attachment.so`. The plugin creates a
temporary fixed physics joint between the cube's `link` and the robot's `link5`.
The joint preserves the measured relative pose, so the cube is not teleported
to a predefined tool pose.

This makes the held cube follow the robot's simulated kinematic chain during
the grasp. The implementation creates the connection in the running Gazebo
physics world. It does not rewrite the URDF, change `robot_description`, or
respawn the robot. Editing a URDF file alone would not attach an object that
has already been spawned in the current simulation.

With `use_sim_attachment: true`, the pick sequence is:

1. `OPEN_GRIPPER`: open the fingers.
2. `FOLLOW_PLANNER_TRAJECTORY`: execute the planner arm waypoints.
3. `MOVE_GRASP`: reach the configured final grasp pose.
4. `ATTACH_OBJECT`: request attachment and wait for successful confirmation.
5. `CLOSE_GRIPPER`: close the fingers after the joint exists.
6. `LIFT`: move to the final planner waypoint.
7. `MOVE_HOME`: return the arm to its carrying configuration.

The place sequence is:

1. `FOLLOW_PLANNER_TRAJECTORY`: execute the placement arm waypoints.
2. `MOVE_PLACE`: reach the configured release pose.
3. `OPEN_GRIPPER`: open the fingers before releasing the joint.
4. `DETACH_OBJECT`: remove the joint and wait for successful confirmation.
5. `RETREAT`: move the arm away from the release pose.
6. `MOVE_HOME`: return the arm to its home configuration.

Cube collisions are disabled while the fixed joint holds it. This prevents
finger contact forces from fighting the joint. It also disables cube contacts
with the surrounding environment while carrying. After detachment, collision
handling is restored and the cube settles under gravity. Residual linear and
angular velocities are cleared when attaching and releasing.

### Attachment checks and failure handling

The plugin exposes `std_srvs/srv/Trigger` services using the spawned object name:
`/cube1/attach` and `/cube1/detach` in the default scene.

Before attachment, the plugin finds the requested parent link and checks the
distance from the cube link to the configured gripper tip. The default maximum
is 0.04 m. The tip offset is `(0.126, 0, 0)` in `link5` coordinates, matching the
[ROBOTIS arm URDF](https://github.com/ROBOTIS-GIT/turtlebot3_manipulation/blob/humble/turtlebot3_manipulation_description/urdf/open_manipulator_x.urdf.xacro).

An attachment fails if the robot link is missing, multiple robot models match
an unspecified parent model, the cube is too far from the tip, or the physics
engine cannot create the joint. Repeated attachment of an already attached
cube does not create a second joint.

Physics mutations run on the Gazebo update thread. The service returns success
after the joint has actually been created or removed. If Gazebo does not update
within two wall-clock seconds, the request is cancelled and returns a failure;
unpausing later does not apply that cancelled request.

The Python controller waits for service discovery and acknowledgement before
advancing. Its configured attachment timeout is 5 seconds. Failed attachment
stops the pick before gripper closure and lifting. Failed detachment preserves
the confirmed held-object state.

Possession is recorded as soon as attachment is confirmed and cleared as soon
as detachment is confirmed. Later arm or gripper failures therefore do not erase
the confirmed attachment state. A late successful acknowledgement also updates
possession. Controller reset is refused while an acknowledgement is pending,
and a reset in simulated attachment mode preserves confirmed possession.

Because collisions are disabled during attachment, the fingers can close fully
without being stopped by the cube. A confirmed attachment is therefore used
as grasp evidence in this mode. The gripper action must still succeed.

## Build the solution

The following example uses the WSL path of the local checkout. On another Linux
machine, change the `cd` command to that checkout's `week3-4/solution` directory.
Build this solution workspace, rather than a previous week's workspace.

```bash
source /opt/ros/humble/setup.bash
source ~/turtlebot3_ws/install/setup.bash
cd /mnt/f/Internship/sbu-robotic-mohsen/week3-4/solution
colcon build --symlink-install --packages-up-to robot_task_system
source install/setup.bash
```

`--packages-up-to robot_task_system` includes this workspace's interface and
attachment packages as dependencies. Rebuild after changing C++, interface
definitions, package metadata, or installed configuration resources.
Restart Gazebo after rebuilding the plugin or changing the cube SDF; an already
spawned cube does not automatically acquire the new plugin or model settings.

## Run the simulation

### Launch helper

From the built solution directory:

```bash
bash run_simulation.sh
```

The helper sources ROS, the default TurtleBot3 workspace when present, this
workspace's installed setup, and `/usr/share/gazebo/setup.sh`. It also adds the
TurtleBot3 manipulation package's share directory to `GAZEBO_MODEL_PATH` so robot
meshes can be resolved by the Gazebo client. If the robot workspace has another
path, source it before running the helper.

The task begins after the default 20-second startup delay. To leave more time
to inspect the scene before motion starts:

```bash
bash run_simulation.sh start_delay:=45.0
```

### Windows and WSLg

With the tested WSL 2 Ubuntu installation and WSLg, the Gazebo window appears
on the Windows desktop. Run this command from PowerShell:

```powershell
wsl -d Ubuntu-22.04 -- bash /mnt/f/Internship/sbu-robotic-mohsen/week3-4/solution/run_simulation.sh
```

If the distribution has a different name, inspect it with `wsl --list --verbose`
and replace `Ubuntu-22.04`. Adjust `/mnt/f/...` if the checkout is elsewhere.
The graphical route requires a working display connection; the headless route
below can execute the task without the Gazebo client.

### Direct ROS launch and headless execution

After sourcing ROS, the robot workspace, and this workspace:

```bash
source /usr/share/gazebo/setup.sh
task_robot_share="$(ros2 pkg prefix turtlebot3_manipulation_gazebo)/share"
export GAZEBO_MODEL_PATH="$task_robot_share:$GAZEBO_MODEL_PATH"
ros2 launch robot_task_system pick_place.launch.py
```

For execution without the graphical client:

```bash
bash run_simulation.sh gui:=false
```

Stop a launch with `Ctrl+C` in its terminal. Stop the previous normal launch
before starting another in the same ROS domain and Gazebo master. The task
does not automatically restart its plan when all actions are completed.

### Launch arguments

The available arguments can be inspected without starting the simulation:

```bash
ros2 launch robot_task_system pick_place.launch.py --show-args
```

- `plan_file`: absolute path to the plan JSON; defaults to the installed
  `config/plan_pick_place.json`.
- `params_file`: parameter YAML; defaults to the installed `config/pick_place.yaml`.
- `use_gazebo`: starts the Gazebo and robot launch; default `true`.
- `gui`: enables the Gazebo client; default `true`.
- `spawn_scene`: spawns the stands and cube; default `true`.
- `start_delay`: delay before starting the task controller; default `20.0` seconds.
- `x_pose`, `y_pose`: robot spawn position; both default to `0.0`.
- `world`: Gazebo world file; defaults to TurtleBot3's `empty_world.world`.
- `pick_x`, `pick_y`: pick stand and cube location; defaults to `0.8`, `1.0` m.
- `place_x`, `place_y`: place stand location; defaults to `-1.27`, `1.246` m.

These arguments are defined by this solution. The included robot launch can
also expose inherited arguments such as `start_rviz` and `prefix`; inspect
`--show-args` in the installed environment for the complete list.

Changing scene positions does not regenerate or transform the JSON plan to those
positions. Keep the plan, world placement, odometry assumptions, and controller
poses consistent. `use_gazebo:=false` expects an existing simulator and clock;
this launch still configures the task nodes with `use_sim_time: true`.
Use `spawn_scene:=false` only when the required scene objects already exist.

`planner_execution.launch.py` is the earlier base-oriented entry point. It does
not launch the manipulation controller or this pick-and-place scene.

## Default parameters and adaptation

The main values in `config/pick_place.yaml` are:

- `anchor_to_origin: true` and `apply_approach_adjustment: true` for plan geometry.
- `grasp_reach: 0.20` m and `arm_mount_x: -0.092` m.
- `target_frame: odom`, `consistency_tolerance: 0.05` m, and
  `action_timeout: 300.0` seconds for task dispatch.
- Arm joints `[joint1, joint2, joint3, joint4]` and `arm_base_frame: link1`.
- `fixed_joint1: 0.0` rad and home joints `[0.0, -1.0, 0.3, 0.7]` rad.
- Grasp planner joints `[0.665, -0.062, 0.967]` rad and placement planner joints
  `[0.643, -0.068, 0.995]` rad.
- Gripper open position `0.019`, closed position `-0.006`, and maximum effort
  `10.0`, using the gripper controller's command units.
- `use_sim_attachment: true`, `attachment_timeout: 5.0` seconds, and
  `verify_grasp: true`.
- `reach_tolerance: 0.04` m, `max_joint_speed: 0.2` rad/s,
  `min_segment_time: 1.0` second, and `joint_tolerance: 0.05` rad.

These are the YAML settings used by the main launch. Some Python node defaults
differ; in particular, `use_sim_attachment` defaults to `false` in the node.
Use a separate parameter file to adapt the exercise and pass its absolute path
with `params_file:=...`.

For a different robot or prefixed links, edit the cube plugin's `parent_link`,
`grasp_offset`, and optional `parent_model`. Without `parent_model`, exactly one
model in the world must contain the requested parent link. The plugin measures
the grasp distance to the cube link origin using the configured tip offset.

## Inspect status and diagnose failures

Run these commands in another terminal after sourcing the same ROS and workspace
setup and using the same ROS domain as the running simulation:

```bash
ros2 service call /get_robot_status robot_task_interfaces/srv/GetRobotStatus '{}'
ros2 service call /get_manipulator_status robot_task_interfaces/srv/GetRobotStatus '{}'
ros2 run robot_task_system task_monitor
ros2 action list -t
ros2 service list
ros2 topic echo /action_done
```

The status services return `status`, `current_action`, and `elapsed_time`.
The manipulator status includes the current manipulation step while executing.
`task_monitor` is an optional status query executable; the main launch does not
start it automatically.

The reset interfaces are `/reset_robot_controller` and
`/reset_manipulator_controller`, both using `std_srvs/srv/Trigger`. A controller
reset does not restart the stopped task queue, reset the world, or replay the
plan. Avoid manually attaching or detaching through the cube services during
an active task, since possession is tracked by the manipulation controller.

Common failures and their meaning:

- Missing `turtlebot3_manipulation_gazebo`: install and build the robot packages,
  then source their workspace before building or launching this solution.
- Gripper controller fails to load or its action is absent: check installation
  of `ros-humble-gripper-controllers` and the simulator's controller startup.
- Missing materials, meshes, or a camera `px != 0` assertion: use the helper,
  which sources Gazebo resources and sets the robot model search path.
- Missing `/cube1/attach`: confirm that the attachment library was built, the
  main launch supplied its plugin path, and the current cube was spawned from
  the updated SDF. Restart Gazebo after model or plugin changes.
- Object is not between the fingers: inspect the actual grasp pose, scene
  coordinates, parent link, and tip offset. The distance check refuses a grasp
  outside the configured range.
- Gazebo is not updating: unpause the world and retry after the failed request.
  Cancelled attachment requests are not applied when the simulation resumes.
- Plan fails validation: inspect the error message and use a merged plan with
  complete object, base, and arm trajectory data.

## Verification procedure and recorded results

### Controller and sequence tests

After building and sourcing the workspace, run the focused grasp checks:

```bash
python3 -m pytest src/robot_task_system/test/test_manipulation_sequence.py \
  src/robot_task_system/test/test_manipulator_controller.py -q
```

All 33 focused tests passed in the local verification. They cover the planner
joint mapping, sequence order, command validation, startup readiness, reach
checks, service discovery, waiting for acknowledgements, failed attachment and
detachment, preservation of possession after later failures, late responses,
and reset behavior while a request is pending.

These tests exercise controller logic with simulated or mocked responses; they
do not replace a physics simulation. Other parser, geometry, command, and base
tests also exist in the test directory. The reported count of 33 refers only
to the two focused files above, not to every repository test or lint check.

### Complete Gazebo pick-and-place check

From the solution directory, after sourcing the built workspaces:

```bash
python3 tools/verify_pick_place.py
```

The tool creates a temporary world with the Gazebo entity-state service and
runs the complete default plan headlessly. It uses ROS domain `76` and Gazebo
master `http://127.0.0.1:11476` to separate the check from the normal simulation.
Do not run multiple copies of this verifier simultaneously, since they use the
same fixed domain and port.

The check requires confirmed attachment and release, successful completion of
the task, at least two measurements of the carried cube, relative position
drift below 0.01 m, a final horizontal position within 0.04 m of the place stand,
and final model height between 0.045 m and 0.09 m. It allows up to 480 seconds
for the run and shuts down the launch processes it started.

Logs and the generated verification world are saved under
`log/pick_place_verification/`; the main launch log is
`log/pick_place_verification/launch.log`.

The recorded local run completed the full pick, carry, and place sequence:

- Maximum sampled cube position drift relative to `link5`: `0.000274` m,
  approximately `0.274` mm.
- Final cube model position in the world frame:
  `(-1.2925, 1.2563, 0.0497)` m.
- Placement completed on the place stand and the task logged
  `All actions completed successfully.`

These figures describe that measured run with the included plan and default
scene. They are not a repeated-trial success rate or a hardware result.
The final height is the cube model-frame height; the SDF places its link origin
0.015 m above that model frame.

## Planner export and scope limits

`planner_reference/export_plan.py` imports `domains.continuous2d.run` and
`pddlstream`. Those planner dependencies are external to the three ROS packages
in this solution. The included JSON avoids needing them for the default launch.
To generate another plan, configure that planner environment, use merged actions
(the exporter's default), and provide the resulting JSON through `plan_file`.
Reconcile its object locations and reference geometry with the Gazebo scene.

The fixed joint models an ideal simulated grasp. It does not measure contact
friction, grasp forces, or stability under disturbances, and carried cube
collisions with the environment are disabled. The controller supports one held
object at a time; multi-object stow and unstow behavior is not implemented.

For hardware, use a separate parameter file with `use_sim_attachment: false`
and appropriate controller, frame, pose, and grasp-verification settings.
The physical mode retains the gripper-based verification path, but hardware
operation was not validated in the reported simulation work.

A Gazebo world reset removes the plugin's joint. Restart the task and controller
nodes along with the reset scene so their possession state is synchronized with
the simulator. There is no automatic task recovery after a world reset or
controller failure.

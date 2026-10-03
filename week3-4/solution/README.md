# Week 3–4: simulated pick and place

This workspace targets ROS 2 Humble, Ubuntu 22.04, and Gazebo Classic 11,
using TurtleBot3 with OpenMANIPULATOR-X. Run `pick_place.launch.py` for the
arm/cube exercise; `planner_execution.launch.py` is the earlier base-only launch.

## Build and run

Install the simulation packages following the
[ROBOTIS instructions](https://emanual.robotis.com/docs/en/platform/turtlebot3/manipulation/).
The gripper action controller must also be installed:

```bash
sudo apt install ros-humble-gripper-controllers
source /opt/ros/humble/setup.bash
source ~/turtlebot3_ws/install/setup.bash
cd /mnt/f/Internship/sbu-robotic-mohsen/week3-4/solution
colcon build --symlink-install --packages-up-to robot_task_system
source install/setup.bash
source /usr/share/gazebo/setup.sh
ros2 launch robot_task_system pick_place.launch.py
```

The `cd` above is the WSL path to this local checkout. On another Ubuntu
machine, use its checkout's `week3-4/solution` directory instead. Source the
workspace containing `turtlebot3_manipulation_gazebo` if it has another name.

Restart Gazebo after rebuilding: an already spawned cube does not acquire
the new plugin automatically. `gui:=false` runs without a Gazebo client.

For subsequent launches, `bash run_simulation.sh` sources the installed ROS,
robot workspace, this workspace, and Gazebo's graphical resources automatically.
Under WSLg the Gazebo window appears on the Windows desktop. From PowerShell:

```powershell
wsl -d Ubuntu-22.04 -- bash /mnt/f/Internship/sbu-robotic-mohsen/week3-4/solution/run_simulation.sh
```

Stop an existing launch before running this command again. If Gazebo reports
missing materials or a camera `px != 0` assertion, ensure
`/usr/share/gazebo/setup.sh` is sourced; the script above already does this.

## Stable simulated grasp

Previously, the cube was held only by contact forces and friction. Closing
the fingers into its collision geometry could eject it. The cube's visible
and collision dimensions now both measure 30 mm.

The `robot_object_attachment` package provides a small Gazebo model plugin
loaded by `models/cube.sdf`. It creates a temporary **fixed physics joint**
between the cube's `link` and the robot's `link5`, preserving the current
relative pose. This implements the grasp as part of the simulated robot's
kinematic chain. It does not rewrite `robot_description` or respawn the robot
at runtime; merely editing a URDF file would not attach the already spawned cube.

With `use_sim_attachment: true` in `config/pick_place.yaml`:

1. Open the gripper, follow the planner trajectory, and reach the grasp pose.
2. Attach the cube **before closing the gripper**, and wait for confirmation.
3. Close the gripper, lift, and move home.
4. At the place pose, open the gripper, detach, then retreat.

Cube collisions are disabled while attached so contact forces do not fight
the joint. This also disables contacts with the environment while carrying;
the simulated grasp is an ideal constraint, not a friction/contact experiment.
Collisions and gravity-driven motion resume after release. Because the fingers
can close fully without contacting the attached cube, successful attachment
is used as grasp evidence instead of the finger-stall test.

The plugin checks the actual cube-to-tool distance (at most 4 cm) before
attaching. It refuses missing/ambiguous robot links or an out-of-reach cube,
and the controller stops instead of reporting a successful pick. Failed later
steps keep the confirmed held-object state, including after controller reset.
World resets require restarting the task/controllers too.

The default gripper tip is 0.126 m along `link5`'s X axis, matching the
[ROBOTIS URDF](https://github.com/ROBOTIS-GIT/turtlebot3_manipulation/blob/humble/turtlebot3_manipulation_description/urdf/open_manipulator_x.urdf.xacro).
For another robot or prefixed links, change `parent_link`, `grasp_offset`, and
optionally `parent_model` inside the cube's plugin element. With no
`parent_model`, exactly one model must contain the specified parent link.

Services use the spawned object name (the default scene spawns `cube1`):

```bash
ros2 service list | grep cube1
# /cube1/attach and /cube1/detach, both std_srvs/srv/Trigger
```

`use_sim_attachment` defaults to false in the Python node; enable it only
for simulation. For hardware, use a separate parameter file setting it false,
retaining physical grasp verification.

## Verification

After sourcing the built workspace:

```bash
python3 -m pytest src/robot_task_system/test/test_manipulation_sequence.py \
  src/robot_task_system/test/test_manipulator_controller.py -q
python3 tools/verify_pick_place.py
```

The second command runs the complete default plan in a separate ROS domain
and Gazebo master, checks that the cube follows the gripper while held and
settles on the place stand, and shuts down its own processes. Logs are saved
in `log/pick_place_verification/launch.log`. It requires the same simulation
and gripper packages as the normal launch.

Verified locally with Humble and Gazebo 11.10: all 33 controller/sequence tests
passed; the complete plan picked, carried, and released the cube. Maximum
measured motion relative to the gripper was 0.000274 m. After release, the cube
settled at (-1.2925, 1.2563, 0.0497) m in the world frame, on the place stand.

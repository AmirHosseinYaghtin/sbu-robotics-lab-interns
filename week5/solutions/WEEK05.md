# Week 05 - current runnable scope

This workspace is a partial handoff made from the uploaded `week5.zip`.
The approximately 67/33 division is an engineering estimate by feature effort;
see `TEAMMATE_TASKS.md` for responsibilities and acceptance criteria.

## Implemented and retained

- `/move_to` and `/manipulate` ROS Action servers and TaskController clients.
- Existing command messages, controller trajectories, feedback and results.
- Internal IDLE / EXECUTING / FAILED / CANCELING / CANCELED / COMPLETED /
  EMERGENCY_STOP state, action labels, counters and failure reasons.
- Sequential dispatch, no next action after failure/cancel, rejected-goal handling,
  server/action/cancel watchdogs and late-result protection.
- `/task/cancel`, `/task/emergency_stop` and independent controller stop services.
- Base zero velocity; manipulator joint hold and gripper cancellation, waiting for
  outstanding attachment/gripper replies; acknowledged possession is preserved.
- Existing base/manipulator status services and the original monitor views.
- Original maps, plan parsing/order/geometry, calibrated poses, models and plugin.

## Intentionally remaining

| ID | Missing implementation | Current behavior |
|---|---|---|
| TODO-W5-01 | Whole-task status service/topic and monitor integration | `publish_status()` is a no-op. `GetTaskStatus.srv` is only a contract; `/get_task_status` and `/task/status` are absent. Read task progress/reasons in terminal logs. |
| TODO-W5-02 | Execution-limit ROS parameters and runtime update policy | Base limits and task/arm deadlines are constants. Existing startup configuration works; managed runtime changes are rejected until implemented. |
| TODO-W5-03 | Recorder, QoS, bag info and isolated playback checks | Recording entry points exit with a TODO error before starting simulation; physical placement verification still works without `--record-bag`. |

No completed implementation of these deferred features is hidden elsewhere in
this archive. Parameter acceptance tests remain as explicitly skipped
specifications and are not counted as passing tests.

## Build and normal execution

Use the existing Ubuntu 22.04 / ROS 2 Humble / Gazebo Classic / TurtleBot3
manipulation environment. Replace the previous workspace source copy rather than
overlaying duplicate package names. From this workspace root:

```bash
source /opt/ros/humble/setup.bash
# Source the robot dependency workspace too if it is separate:
# source ~/turtlebot3_ws/install/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
export TURTLEBOT3_MODEL=waffle
ros2 launch robot_task_system pick_place.launch.py map:=simple
```

Other original maps: `pick_place`, `corridor`, `multi_object`, `at_work`.
`planner_execution.launch.py` is the older base-only launch.
Build the interface package too because the Action definitions are required.
The manipulator server becomes available after startup homing ends.

In another sourced terminal in the same domain:

```bash
ros2 action list -t
ros2 run robot_task_system task_monitor
ros2 service call /task/cancel std_srvs/srv/Trigger '{}'
# Or request the retained logical stop:
ros2 service call /task/emergency_stop std_srvs/srv/Trigger '{}'
```

Cancellation acknowledges a request; wait for terminal logs to confirm its
outcome. A missing result/stop acknowledgement reports STOP_UNCONFIRMED and never
advances the queue. Software emergency stop stays latched; it is not safety-rated.
After an interrupted manipulation, inspect/reset the scene and controllers
before restarting. There is no automatic retry or blind mid-plan resumption.

## Fixed execution defaults during the handoff

The former base parameters are not declared or consumed as ROS settings now:
speed 0.15 m/s; waypoint/final/yaw tolerances 0.10/0.02/0.03; movement deadline
600 s; missing-odom deadline 5 s; initial odom wait 120 s; stuck window 20 s and
minimum progress 0.05 m. Task action/server/cancel timeouts are 900/120/20 s.
Arm motion margin/gripper/startup timeouts are 10/10/120 s.

These match the completed archive's shipped configuration. Existing arm poses,
planner/scene startup parameters and their YAML values are preserved. Startup
finite-positive checks and joint-limit validation remain. Managed runtime
configuration changes are rejected, including valid idle changes.
Do not pass removed parameter overrides and expect them to affect execution.

## Verification

```bash
# No ROS installation required; needs pytest and PyYAML:
python3 tools/run_offline_tests.py
# Pending parameter acceptance appears as skipped, not passed.

# On Ubuntu with generated ROS interfaces sourced, in an UNUSED domain:
export ROS_DOMAIN_ID=78
python3 -m pytest -q src/robot_task_system/test/test_week05_ros_integration.py

# Existing physical attachment / placement verifier, without recording:
python3 tools/verify_pick_place.py --map simple
```

Live integration tests exercise transport with mocked actuators/TF; they do not
verify physics. No ROS build, live simulation or bag run was performed here.
Actual checks and limitations are in `TEST_REPORT.md`.

## Live no-odometry failure demonstration

Use an unused ROS domain with no Gazebo or `/odom` publisher. Start the base
controller in one sourced terminal, then TaskController in another:

```bash
# Both terminals:
export ROS_DOMAIN_ID=78

# Terminal 1 (fixed initial odom wait is 120 seconds):
ros2 run robot_task_system robot_controller

# Terminal 2:
SHARE=$(ros2 pkg prefix --share robot_task_system)
ros2 run robot_task_system task_controller --ros-args \
  --params-file "$SHARE/config/pick_place.yaml" \
  -p plan_file:="$SHARE/config/plan_pick_place.json"
```

Expected: MOVE_BASE aborts with `no /odom received`; the task becomes FAILED,
zero actions are completed and PICK is not sent. Inspect terminal logs for now.
This experiment remains to be run on the lab ROS system.

## Recording work

`tools/verify_pick_place.py --record-bag ...` and `tools/verify_bag.py ...`
currently exit 2 with TODO-W5-03. `recording_qos.yaml` and bag-only package
dependencies were removed. Implement and validate recording, info and playback
after task-status publishing exists, following `TEAMMATE_TASKS.md`.

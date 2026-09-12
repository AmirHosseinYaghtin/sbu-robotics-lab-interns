# Week 1 — ROS 2 Robot Task System

A small task-execution system developed with Python and ROS 2 Humble.

This project demonstrates the fundamental concepts of ROS 2 by simulating a robot that receives and executes a sequence of actions. The controller sends one action at a time, the simulator executes it, and the monitor retrieves the current robot status through a custom ROS 2 service.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Learning Objectives](#learning-objectives)
- [System Architecture](#system-architecture)
- [Package Structure](#package-structure)
- [ROS 2 Packages](#ros-2-packages)
- [Nodes](#nodes)
- [Topics](#topics)
- [Custom Service](#custom-service)
- [Task Execution Flow](#task-execution-flow)
- [Robot State Machine](#robot-state-machine)
- [Action Durations](#action-durations)
- [Requirements](#requirements)
- [Installation](#installation)
- [Build Instructions](#build-instructions)
- [Running the Project](#running-the-project)
- [Running Nodes Separately](#running-nodes-separately)
- [Monitoring the System](#monitoring-the-system)
- [Testing Error Handling](#testing-error-handling)
- [Running Automated Tests](#running-automated-tests)
- [Expected Behavior](#expected-behavior)
- [Troubleshooting](#troubleshooting)
- [Development Notes](#development-notes)
- [Contributors](#contributors)

---

## Project Overview

The goal of this project is to simulate a simple robot task-management system.

The robot must execute the following actions in order:

1. Move to a workstation.
2. Pick up an object.
3. Move to a shelf.
4. Place the object on the shelf.

The system is divided into independent ROS 2 nodes. Each node has a specific responsibility and communicates with the other nodes using ROS 2 topics and services.

The main components are:

- **Task Controller:** manages the action queue.
- **Robot Simulator:** simulates execution of robot actions.
- **Task Monitor:** requests and displays the current robot status.
- **Custom Interface Package:** defines the robot status service.

---

## Learning Objectives

This project demonstrates the following ROS 2 concepts:

- Creating a ROS 2 workspace
- Creating Python and interface packages
- Writing ROS 2 nodes with `rclpy`
- Publishing and subscribing to topics
- Creating and using a custom service
- Managing asynchronous operations
- Using ROS 2 timers
- Building packages with `colcon`
- Creating ROS 2 launch files
- Inspecting the ROS graph from the command line
- Writing and running automated tests
- Handling invalid commands and error states
- Organizing a multi-package ROS 2 project

---

## System Architecture

The system uses topic communication for executing actions and service communication for monitoring the robot.

```text
┌──────────────────────┐
│   Task Controller    │
│                      │
│  Maintains a queue   │
│  of robot actions    │
└──────────┬───────────┘
           │
           │ /task/action
           │ std_msgs/msg/String
           ▼
┌──────────────────────┐
│   Robot Simulator    │
│                      │
│ Executes the action  │
│ and tracks its state │
└──────────┬───────────┘
           │
           │ /action_done
           │ std_msgs/msg/Bool
           ▼
┌──────────────────────┐
│   Task Controller    │
│                      │
│ Sends the next task  │
│ only after success   │
└──────────────────────┘
```

The monitoring flow is separate:

```text
┌──────────────────────┐
│     Task Monitor     │
└──────────┬───────────┘
           │
           │ /get_robot_status
           │ robot_task_interfaces/srv/GetRobotStatus
           ▼
┌──────────────────────┐
│   Robot Simulator    │
│                      │
│ Returns:             │
│ - status             │
│ - current action     │
│ - elapsed time       │
└──────────────────────┘
```

---

## Package Structure

The solution contains two ROS 2 packages:

```text
week1/
└── solution/
    ├── README.md
    │
    ├── robot_task_interfaces/
    │   ├── CMakeLists.txt
    │   ├── package.xml
    │   └── srv/
    │       └── GetRobotStatus.srv
    │
    └── robot_task_system/
        ├── package.xml
        ├── setup.py
        ├── setup.cfg
        ├── resource/
        ├── launch/
        │   └── robot_task_system.launch.py
        ├── robot_task_system/
        │   ├── __init__.py
        │   ├── task_controller.py
        │   ├── robot_simulator.py
        │   └── task_monitor.py
        └── test/
```

Generated workspace directories such as `build`, `install`, and `log` are not part of the source code and must not be committed.

---

## ROS 2 Packages

### `robot_task_interfaces`

This package contains the custom service used by the task monitor.

Custom messages and services are placed in a separate interface package because ROS 2 must generate language-specific source code for them during the build process.

The package uses `ament_cmake` and ROS interface-generation tools.

### `robot_task_system`

This package contains the Python nodes and launch file.

It uses:

- `ament_python`
- `rclpy`
- `std_msgs`
- `robot_task_interfaces`

Separating the interface definitions from the Python application logic makes the project easier to maintain and allows other ROS 2 packages to reuse the same service.

---

## Nodes

### 1. Task Controller

Executable name:

```text
task_controller
```

Node name:

```text
/task_controller
```

The Task Controller is responsible for managing the action queue.

Its initial queue is:

```text
MOVE_TO_WORKSTATION
PICK_OBJECT
MOVE_TO_SHELF
PLACE_OBJECT
```

The controller follows these rules:

1. It waits for the Robot Simulator subscriber to become available.
2. It publishes the first action on `/task/action`.
3. It waits for a result on `/action_done`.
4. If the result is `true`, it removes the completed action from the queue.
5. It then publishes the next action.
6. If the result is `false`, it stops processing the remaining queue.
7. When the queue becomes empty, the complete task sequence is finished.

Only one action is allowed to be active at a time.

This behavior prevents the controller from sending all commands at once.

---

### 2. Robot Simulator

Executable name:

```text
robot_simulator
```

Node name:

```text
/robot_simulator
```

The Robot Simulator receives actions from the Task Controller and simulates their execution.

It is responsible for:

- Receiving action names
- Validating actions
- Tracking the current robot state
- Tracking the current action
- Measuring elapsed execution time
- Simulating the required duration
- Reporting success or failure
- Providing robot status through a service

ROS 2 timers are used instead of blocking calls such as `time.sleep()`.

Using timers keeps the node responsive while an operation is being executed. For example, the status service can still answer requests while the robot is moving.

---

### 3. Task Monitor

Executable name:

```text
task_monitor
```

The Task Monitor is a service client.

It sends an empty request to `/get_robot_status` and displays the returned robot information.

The monitor reports:

- Robot state
- Current action
- Elapsed time

The monitor is a short-lived node. It can request the status, print the response, and then exit. Because of this behavior, it may not remain visible in `ros2 node list`.

---

## Topics

### `/task/action`

Message type:

```text
std_msgs/msg/String
```

Publisher:

```text
/task_controller
```

Subscriber:

```text
/robot_simulator
```

Purpose:

This topic transfers action names from the Task Controller to the Robot Simulator.

Example message:

```yaml
data: MOVE_TO_WORKSTATION
```

---

### `/action_done`

Message type:

```text
std_msgs/msg/Bool
```

Publisher:

```text
/robot_simulator
```

Subscriber:

```text
/task_controller
```

Purpose:

This topic reports the result of the current action.

Possible values:

```yaml
data: true
```

The action completed successfully.

```yaml
data: false
```

The action failed, and the controller must stop the remaining queue.

---

## Custom Service

Service name:

```text
/get_robot_status
```

Service type:

```text
robot_task_interfaces/srv/GetRobotStatus
```

Service server:

```text
/robot_simulator
```

Service client:

```text
task_monitor
```

The request is empty because the client only asks for the current status.

The service definition is:

```srv
# Request: empty
---
string status
string current_action
float64 elapsed_time
```

### Response Fields

#### `status`

The current robot state:

```text
IDLE
EXECUTING
ERROR
```

#### `current_action`

The action currently being executed.

Examples:

```text
MOVE_TO_WORKSTATION
PICK_OBJECT
MOVE_TO_SHELF
PLACE_OBJECT
INVALID_ACTION
NONE
```

#### `elapsed_time`

The number of seconds elapsed since the current action started.

When the robot is not executing an action, the value is normally:

```text
0.0
```

---

## Task Execution Flow

The complete execution sequence is:

```text
Task Controller starts
        │
        ▼
Wait for Robot Simulator
        │
        ▼
Publish MOVE_TO_WORKSTATION
        │
        ▼
Robot state becomes EXECUTING
        │
        ▼
Wait 5 seconds using a ROS timer
        │
        ▼
Publish success on /action_done
        │
        ▼
Controller sends PICK_OBJECT
        │
        ▼
Robot executes the next action
        │
        ▼
Continue until the queue is empty
        │
        ▼
Robot returns to IDLE
```

The controller does not remove an action from the queue until a successful result is received.

---

## Robot State Machine

The simulator has three main states.

### `IDLE`

The robot is not executing any action.

Typical status response:

```text
status: IDLE
current_action: NONE
elapsed_time: 0.0
```

### `EXECUTING`

The robot is currently executing a valid action.

Typical response:

```text
status: EXECUTING
current_action: MOVE_TO_WORKSTATION
elapsed_time: 0.91
```

### `ERROR`

The simulator received an unknown or invalid action.

Typical response:

```text
status: ERROR
current_action: INVALID_ACTION
elapsed_time: 0.0
```

### State Transitions

```text
IDLE ──valid action──> EXECUTING
EXECUTING ──success──> IDLE
IDLE ──invalid action──> ERROR
EXECUTING ──failure──> ERROR
```

Restarting the system initializes the simulator in the `IDLE` state.

---

## Action Durations

| Action | Simulated Duration | Description |
|---|---:|---|
| `MOVE_TO_WORKSTATION` | 5 seconds | Moves the robot to the workstation |
| `PICK_OBJECT` | 3 seconds | Picks up the object |
| `MOVE_TO_SHELF` | 5 seconds | Moves the robot to the shelf |
| `PLACE_OBJECT` | 2 seconds | Places the object on the shelf |

The complete successful task sequence takes approximately 15 seconds, excluding startup and communication overhead.

---

## Requirements

The project was developed and tested with:

- Ubuntu 22.04
- WSL 2
- ROS 2 Humble
- Python 3.10
- Colcon
- Git

Verify the ROS distribution:

```bash
source /opt/ros/humble/setup.bash
echo $ROS_DISTRO
```

Expected result:

```text
humble
```

Verify Python:

```bash
python3 --version
```

Verify Colcon:

```bash
colcon --help
```

---

## Installation

Clone the repository:

```bash
git clone \
  https://github.com/AmirHosseinYaghtin/sbu-robotics-lab-interns.git
```

Enter the repository:

```bash
cd sbu-robotics-lab-interns
```

Load the ROS 2 Humble environment:

```bash
source /opt/ros/humble/setup.bash
```

---

## Build Instructions

Run the following commands from the repository root:

```bash
source /opt/ros/humble/setup.bash

colcon build \
  --symlink-install \
  --base-paths week1/solution
```

A successful build should contain output similar to:

```text
Starting >>> robot_task_interfaces
Finished <<< robot_task_interfaces

Starting >>> robot_task_system
Finished <<< robot_task_system

Summary: 2 packages finished
```

The interface package is built first because `robot_task_system` depends on it.

After building, load the workspace overlay:

```bash
source install/setup.bash
```

The overlay makes the newly built packages, executables, launch files, and custom service interface available to ROS 2 commands.

You must source the workspace in every new terminal.

---

## Running the Project

Load both the ROS installation and the workspace:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
```

Run the launch file:

```bash
ros2 launch robot_task_system robot_task_system.launch.py
```

The persistent runtime nodes are:

```text
/robot_simulator
/task_controller
```

The Task Monitor can be executed on demand to retrieve the current status.

Stop the running system using:

```text
Ctrl+C
```

---

## Running Nodes Separately

Running the nodes separately is useful for learning and debugging.

Open a separate terminal for each node.

In every terminal, run:

```bash
source /opt/ros/humble/setup.bash
source ~/sbu-robotics-lab-interns/install/setup.bash
```

### Terminal 1 — Robot Simulator

```bash
ros2 run robot_task_system robot_simulator
```

The simulator should normally be started before the controller so that the controller can find its subscriber.

### Terminal 2 — Task Controller

```bash
ros2 run robot_task_system task_controller
```

The controller begins publishing actions after detecting the simulator.

### Terminal 3 — Task Monitor

```bash
ros2 run robot_task_system task_monitor
```

The monitor requests the current robot status and displays the response.

---

## Monitoring the System

### List Active Nodes

```bash
ros2 node list
```

Expected persistent nodes:

```text
/robot_simulator
/task_controller
```

### Inspect a Node

```bash
ros2 node info /robot_simulator
```

```bash
ros2 node info /task_controller
```

### List Topics

```bash
ros2 topic list
```

Important project topics:

```text
/task/action
/action_done
```

### Inspect Topic Types

```bash
ros2 topic type /task/action
```

Expected result:

```text
std_msgs/msg/String
```

```bash
ros2 topic type /action_done
```

Expected result:

```text
std_msgs/msg/Bool
```

### Observe Published Actions

```bash
ros2 topic echo /task/action
```

### Observe Action Results

```bash
ros2 topic echo /action_done
```

### List Services

```bash
ros2 service list
```

The list should contain:

```text
/get_robot_status
```

### Inspect the Custom Interface

```bash
ros2 interface show \
  robot_task_interfaces/srv/GetRobotStatus
```

Expected interface:

```text
---
string status
string current_action
float64 elapsed_time
```

---

## Query Robot Status Manually

While the system is running, open another terminal and source the environment:

```bash
source /opt/ros/humble/setup.bash
source ~/sbu-robotics-lab-interns/install/setup.bash
```

Call the service:

```bash
ros2 service call \
  /get_robot_status \
  robot_task_interfaces/srv/GetRobotStatus \
  "{}"
```

Example response during execution:

```text
status: EXECUTING
current_action: MOVE_TO_WORKSTATION
elapsed_time: 0.915
```

A later request may return:

```text
status: EXECUTING
current_action: MOVE_TO_SHELF
elapsed_time: 0.252
```

This demonstrates that the controller advances through the queue and that elapsed time resets when a new action begins.

After all actions finish:

```text
status: IDLE
current_action: NONE
elapsed_time: 0.0
```

---

## Testing Error Handling

To test an invalid action, wait until the normal task queue finishes and publish an unknown command:

```bash
ros2 topic pub --once \
  /task/action \
  std_msgs/msg/String \
  "{data: 'INVALID_ACTION'}"
```

Then request the robot status:

```bash
ros2 service call \
  /get_robot_status \
  robot_task_interfaces/srv/GetRobotStatus \
  "{}"
```

Expected response:

```text
status: ERROR
current_action: INVALID_ACTION
elapsed_time: 0.0
```

The simulator must not attempt to execute an unknown action.

It reports failure and enters the `ERROR` state.

Restart the launch file to return the complete system to its initial state.

---

## Running Automated Tests

From the repository root, source the environment:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
```

Run the tests:

```bash
colcon test \
  --base-paths week1/solution \
  --packages-select robot_task_system
```

Display detailed results:

```bash
colcon test-result --verbose
```

The verified result for this implementation is:

```text
9 tests
0 errors
0 failures
1 skipped
```

The skipped test does not indicate a project failure.

A warning similar to the following may also appear:

```text
SelectableGroups dict interface is deprecated
```

This warning is produced by an external Python testing dependency and does not indicate a failure in the ROS 2 nodes.

---

## Expected Behavior

A correct execution should follow this order:

```text
MOVE_TO_WORKSTATION
PICK_OBJECT
MOVE_TO_SHELF
PLACE_OBJECT
```

For each action:

1. The controller publishes the action.
2. The simulator changes its status to `EXECUTING`.
3. The simulator records the current action and start time.
4. The timer simulates the action duration.
5. The simulator publishes `true` on `/action_done`.
6. The simulator returns to `IDLE`.
7. The controller publishes the next queued action.

After the final action, the queue is empty and no additional command is published.

For an invalid action:

1. The simulator detects that the action is unknown.
2. The simulator changes its status to `ERROR`.
3. It stores the invalid command as the current action.
4. It publishes a failure result.
5. The controller stops processing the remaining queue.

---

## Troubleshooting

### `Package 'robot_task_system' not found`

The workspace has not been built or sourced.

Run:

```bash
cd ~/sbu-robotics-lab-interns
source /opt/ros/humble/setup.bash

colcon build \
  --symlink-install \
  --base-paths week1/solution

source install/setup.bash
```

---

### Custom service interface is not found

Example error:

```text
Could not find the interface robot_task_interfaces/srv/GetRobotStatus
```

Rebuild the workspace and source it again:

```bash
source /opt/ros/humble/setup.bash

colcon build \
  --symlink-install \
  --base-paths week1/solution

source install/setup.bash
```

Check the interface:

```bash
ros2 interface show \
  robot_task_interfaces/srv/GetRobotStatus
```

---

### Service remains unavailable

If the following message remains visible:

```text
waiting for service to become available...
```

Make sure the Robot Simulator is running:

```bash
ros2 node list
```

The output must contain:

```text
/robot_simulator
```

---

### Robot status is always `IDLE`

The complete queue may already have finished.

Restart the launch file and call the service immediately while an action is running:

```bash
ros2 launch robot_task_system robot_task_system.launch.py
```

Then, in another terminal:

```bash
ros2 service call \
  /get_robot_status \
  robot_task_interfaces/srv/GetRobotStatus \
  "{}"
```

---

### Changes are not visible after editing Python files

Rebuild the package and source the overlay:

```bash
colcon build \
  --symlink-install \
  --base-paths week1/solution

source install/setup.bash
```

The `--symlink-install` option is useful during Python development because installed Python files are linked to the source files.

---

### WSL proxy or drive-mount warnings

Warnings about a localhost proxy or a Windows drive failing to mount are produced by WSL configuration.

They are not errors in this ROS 2 project if ROS commands, package builds, topics, and services continue to work.

---

### Generated directories appear in Git

The following directories are generated by Colcon and should not be committed:

```text
build/
install/
log/
```

Check repository status:

```bash
git status
```

Make sure these directories are ignored by `.gitignore`.

---

## Development Notes

### Why use a queue?

The queue preserves the required order of operations and allows the controller to stop safely when one action fails.

### Why wait for `/action_done`?

Without waiting for a result, the controller could publish all actions immediately. The simulator would then receive new commands before completing the previous operation.

Waiting for `/action_done` provides sequential execution.

### Why use ROS timers?

Blocking the node with `time.sleep()` prevents it from processing callbacks while an action is running.

ROS timers allow the executor to continue processing:

- Status-service requests
- Incoming topic messages
- Other callbacks

### Why use a custom service?

A custom service provides strongly typed and structured fields:

```text
status
current_action
elapsed_time
```

This is clearer and easier to extend than returning all status information inside a single unstructured string.

### Why use a separate interface package?

ROS 2 interface generation is normally handled by an `ament_cmake` package, while the application nodes in this project use `ament_python`.

Keeping them separate follows common ROS 2 package-design practices.

---

## Verification Summary

The project has been verified with the following checks:

- Both ROS 2 packages build successfully
- All Python executables are registered
- The launch file is installed correctly
- The custom service is generated successfully
- The action queue executes in the required order
- The controller waits for each result
- Robot status can be queried during execution
- Elapsed time is updated during an action
- The robot returns to `IDLE` after completion
- Invalid actions change the state to `ERROR`
- Automated tests complete without failures

---

## Contributors

- [Seyed0Mohammad0Hosseini](https://github.com/Seyed0Mohammad0Hosseini)
- [mohsen-norouzi237](https://github.com/mohsen-norouzi237)

---

## License

See the `LICENSE` file included with the project.

#!/usr/bin/env bash
# Start the built simulation, including Gazebo's graphical resources for WSLg.
set -e
source /opt/ros/humble/setup.bash
if [[ -f "$HOME/turtlebot3_ws/install/setup.bash" ]]; then
  source "$HOME/turtlebot3_ws/install/setup.bash"
fi
cd "$(dirname "${BASH_SOURCE[0]}")"
if [[ ! -f install/setup.bash ]]; then
  printf 'Build this workspace first: colcon build --symlink-install --packages-up-to robot_task_system\n' >&2
  exit 1
fi
source install/setup.bash
source /usr/share/gazebo/setup.sh
task_robot_share="$(ros2 pkg prefix turtlebot3_manipulation_gazebo)/share"
export GAZEBO_MODEL_PATH="$task_robot_share:$GAZEBO_MODEL_PATH"
exec ros2 launch robot_task_system pick_place.launch.py "$@"

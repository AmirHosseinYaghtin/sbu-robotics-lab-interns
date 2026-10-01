import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    planner_launch = os.path.join(
        get_package_share_directory('robot_task_system'),
        'launch',
        'planner_execution.launch.py',
    )

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([planner_launch])
        ),
    ])

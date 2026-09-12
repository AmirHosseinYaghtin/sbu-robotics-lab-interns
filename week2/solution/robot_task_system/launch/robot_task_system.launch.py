from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    robot_simulator_node = Node(
        package='robot_task_system',
        executable='robot_simulator',
        name='robot_simulator',
        output='screen',
    )

    task_controller_node = Node(
        package='robot_task_system',
        executable='task_controller',
        name='task_controller',
        output='screen',
    )

    return LaunchDescription([
        robot_simulator_node,
        task_controller_node,
    ])

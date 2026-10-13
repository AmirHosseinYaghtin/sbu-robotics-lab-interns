import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('robot_task_system')
    default_plan = os.path.join(pkg_share, 'config', 'plan_pick_place.json')

    plan_file = LaunchConfiguration('plan_file')
    use_gazebo = LaunchConfiguration('use_gazebo')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')

    declare_plan_file = DeclareLaunchArgument(
        'plan_file',
        default_value=default_plan,
        description='Absolute path to the PDDLStream plan JSON to execute.',
    )
    declare_use_gazebo = DeclareLaunchArgument(
        'use_gazebo',
        default_value='true',
        description='Whether to start TurtleBot3 in an empty Gazebo world.',
    )
    declare_x_pose = DeclareLaunchArgument(
        'x_pose',
        default_value='0.0',
        description='Robot spawn x. Plan is anchored to this origin.',
    )
    declare_y_pose = DeclareLaunchArgument(
        'y_pose',
        default_value='0.0',
        description='Robot spawn y. Plan is anchored to this origin.',
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('turtlebot3_gazebo'),
                'launch',
                'empty_world.launch.py',
            )
        ]),
        launch_arguments={
            'x_pose': x_pose,
            'y_pose': y_pose,
        }.items(),
        condition=IfCondition(use_gazebo),
    )

    robot_controller_node = Node(
        package='robot_task_system',
        executable='robot_controller',
        name='robot_controller',
        output='screen',
    )

    task_controller_node = Node(
        package='robot_task_system',
        executable='task_controller',
        name='task_controller',
        output='screen',
        parameters=[{'plan_file': plan_file}],
    )

    return LaunchDescription([
        declare_plan_file,
        declare_use_gazebo,
        declare_x_pose,
        declare_y_pose,
        gazebo,
        robot_controller_node,
        task_controller_node,
    ])

import os

from ament_index_python.packages import get_package_prefix
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import RegisterEventHandler
from launch.actions import TimerAction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def spawn_model(name, model_file, x, y, z, spawn_scene, yaw='0.0'):
    return Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', name,
            '-file', model_file,
            '-x', x, '-y', y, '-z', z,
            '-Y', yaw,
            '-timeout', '120',
        ],
        output='screen',
        condition=IfCondition(spawn_scene),
    )


def generate_launch_description():
    pkg_share = get_package_share_directory('robot_task_system')
    default_plan = os.path.join(pkg_share, 'config', 'plan_pick_place.json')
    default_params = os.path.join(pkg_share, 'config', 'pick_place.yaml')
    models = os.path.join(pkg_share, 'models')

    plan_file = LaunchConfiguration('plan_file')
    params_file = LaunchConfiguration('params_file')
    use_gazebo = LaunchConfiguration('use_gazebo')
    gui = LaunchConfiguration('gui')
    spawn_scene = LaunchConfiguration('spawn_scene')
    start_delay = LaunchConfiguration('start_delay')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    world = LaunchConfiguration('world')
    pick_x = LaunchConfiguration('pick_x')
    pick_y = LaunchConfiguration('pick_y')
    place_x = LaunchConfiguration('place_x')
    place_y = LaunchConfiguration('place_y')

    arguments = [
        DeclareLaunchArgument('plan_file', default_value=default_plan),
        DeclareLaunchArgument('params_file', default_value=default_params),
        DeclareLaunchArgument('use_gazebo', default_value='true'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('spawn_scene', default_value='true'),
        DeclareLaunchArgument('start_delay', default_value='20.0'),
        DeclareLaunchArgument('x_pose', default_value='0.0'),
        DeclareLaunchArgument('y_pose', default_value='0.0'),
        DeclareLaunchArgument('pick_x', default_value='0.8'),
        DeclareLaunchArgument('pick_y', default_value='1.0'),
        DeclareLaunchArgument('place_x', default_value='-1.27'),
        DeclareLaunchArgument('place_y', default_value='1.246'),
        DeclareLaunchArgument(
            'world',
            default_value=os.path.join(
                get_package_share_directory('turtlebot3_gazebo'),
                'worlds', 'empty_world.world',
            ),
        ),
    ]

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('turtlebot3_manipulation_gazebo'),
            'launch', 'gazebo.launch.py',
        )),
        launch_arguments={
            'x_pose': x_pose, 'y_pose': y_pose, 'world': world, 'gui': gui,
        }.items(),
        condition=IfCondition(use_gazebo),
    )

    common = [params_file, {'use_sim_time': True}]

    pick_stand = spawn_model('pick_stand', os.path.join(models, 'pick_stand.sdf'),
                             pick_x, pick_y, '0.0', spawn_scene)
    cube = spawn_model('cube1', os.path.join(models, 'cube.sdf'),
                       pick_x, pick_y, '0.051', spawn_scene, '-0.654')

    scene = [
        pick_stand,
        RegisterEventHandler(OnProcessExit(target_action=pick_stand, on_exit=[cube])),
        spawn_model('place_stand', os.path.join(models, 'place_stand.sdf'),
                    place_x, place_y, '0.0', spawn_scene),
    ]

    robot_controller = Node(
        package='robot_task_system',
        executable='robot_controller',
        name='robot_controller',
        output='screen',
        parameters=common,
    )

    manipulator_controller = Node(
        package='robot_task_system',
        executable='manipulator_controller',
        name='manipulator_controller',
        output='screen',
        parameters=common,
    )

    task_controller = Node(
        package='robot_task_system',
        executable='task_controller',
        name='task_controller',
        output='screen',
        parameters=common + [{'plan_file': plan_file}],
    )

    return LaunchDescription(arguments + [
        AppendEnvironmentVariable(
            'GAZEBO_PLUGIN_PATH',
            os.path.join(get_package_prefix('robot_object_attachment'), 'lib'),
        ),
        gazebo,
    ] + scene + [
        robot_controller,
        manipulator_controller,
        TimerAction(period=start_delay, actions=[task_controller]),
    ])

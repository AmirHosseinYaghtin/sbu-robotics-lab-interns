"""
Pick and place on any planner map.

The map comes from the plan: the "scene" block written by
planner_reference/export_plan.py (furniture, regions, objects). Choose a map
with either argument:

    ros2 launch robot_task_system pick_place.launch.py map:=corridor
    ros2 launch robot_task_system pick_place.launch.py plan_file:=/abs/plan.json

map:=NAME loads config/plans/NAME.json. Without arguments the original,
Gazebo-verified config/plan_pick_place.json runs.
"""

import os
import tempfile

from ament_index_python.packages import get_package_prefix
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import LogInfo
from launch.actions import OpaqueFunction
from launch.actions import RegisterEventHandler
from launch.actions import TimerAction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from robot_task_system import scene as scene_builder


def spawn(name, model_file, x, y, z, yaw):
    return Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', name,
            '-file', model_file,
            '-x', str(x), '-y', str(y), '-z', str(z),
            '-Y', str(yaw),
            '-timeout', '120',
        ],
        output='screen',
    )


def resolve_plan_file(context, pkg_share):
    map_name = LaunchConfiguration('map').perform(context).strip()
    plan_file = LaunchConfiguration('plan_file').perform(context).strip()
    if map_name:
        candidate = map_name if map_name.endswith('.json') else map_name + '.json'
        plan_file = os.path.join(pkg_share, 'config', 'plans', candidate)
    if not os.path.isfile(plan_file):
        available = sorted(
            f[:-5] for f in os.listdir(os.path.join(pkg_share, 'config', 'plans'))
            if f.endswith('.json')
        )
        raise RuntimeError('plan file "{}" not found. Available maps: {}'.format(
            plan_file, ', '.join(available)
        ))
    return plan_file


def launch_scene_and_tasks(context, pkg_share):
    plan_file = resolve_plan_file(context, pkg_share)
    params_file = LaunchConfiguration('params_file').perform(context)
    config_file = LaunchConfiguration('scene_config').perform(context)
    offset = (
        float(LaunchConfiguration('x_pose').perform(context)),
        float(LaunchConfiguration('y_pose').perform(context)),
    )

    # Same validation and anchoring the Task Controller performs.
    config = scene_builder.load_config(config_file or None)
    plan, actions, scene = scene_builder.prepare_plan(plan_file, config, offset)
    directory = tempfile.mkdtemp(prefix='robot_task_scene_')
    scene_sdf, objects = scene_builder.write_scene_files(scene, config, directory)

    actions_out = [
        LogInfo(msg='Plan: {} ({})'.format(plan_file, plan.get('problem', '?'))),
        LogInfo(msg=scene_builder.describe(scene)),
    ]

    if LaunchConfiguration('spawn_scene').perform(context).lower() in ('true', '1'):
        object_spawns = [
            spawn(obj['name'], path, obj['x'], obj['y'], obj['z'], obj['yaw'])
            for obj, path in objects
        ]
        if scene_sdf is not None:
            # Objects only after their pedestals exist, or they fall.
            stands = spawn('planner_scene', scene_sdf, 0.0, 0.0, 0.0, 0.0)
            actions_out += [
                stands,
                RegisterEventHandler(OnProcessExit(target_action=stands,
                                                   on_exit=object_spawns)),
            ]
        else:
            actions_out += object_spawns

    common = [params_file, {'use_sim_time': True}]
    task_controller = Node(
        package='robot_task_system',
        executable='task_controller',
        name='task_controller',
        output='screen',
        parameters=common + [{'plan_file': plan_file}],
    )
    actions_out.append(TimerAction(
        period=float(LaunchConfiguration('start_delay').perform(context)),
        actions=[task_controller],
    ))
    return actions_out


def generate_launch_description():
    pkg_share = get_package_share_directory('robot_task_system')
    default_plan = os.path.join(pkg_share, 'config', 'plan_pick_place.json')
    default_params = os.path.join(pkg_share, 'config', 'pick_place.yaml')
    default_scene = os.path.join(pkg_share, 'config', 'scene.yaml')

    params_file = LaunchConfiguration('params_file')
    use_gazebo = LaunchConfiguration('use_gazebo')
    gui = LaunchConfiguration('gui')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    world = LaunchConfiguration('world')

    arguments = [
        DeclareLaunchArgument('map', default_value='',
                              description='Map name in config/plans (overrides plan_file), '
                                          'e.g. pick_place, corridor, multi_object, at_work'),
        DeclareLaunchArgument('plan_file', default_value=default_plan,
                              description='Plan JSON from export_plan.py'),
        DeclareLaunchArgument('params_file', default_value=default_params),
        DeclareLaunchArgument('scene_config', default_value=default_scene,
                              description='YAML controlling how the scene is built'),
        DeclareLaunchArgument('use_gazebo', default_value='true'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('spawn_scene', default_value='true'),
        DeclareLaunchArgument('start_delay', default_value='20.0'),
        DeclareLaunchArgument('x_pose', default_value='0.0',
                              description='Robot spawn x; the scene is shifted with it'),
        DeclareLaunchArgument('y_pose', default_value='0.0',
                              description='Robot spawn y; the scene is shifted with it'),
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

    return LaunchDescription(arguments + [
        AppendEnvironmentVariable(
            'GAZEBO_PLUGIN_PATH',
            os.path.join(get_package_prefix('robot_object_attachment'), 'lib'),
        ),
        gazebo,
        OpaqueFunction(function=launch_scene_and_tasks, args=[pkg_share]),
        robot_controller,
        manipulator_controller,
    ])

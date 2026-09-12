import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'robot_task_system'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mohammad05',
    maintainer_email='mohammad05@todo.todo',
    description='A simple ROS 2 robot task execution system with a '
                'Task Controller, Robot Simulator, and Task Monitor.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'task_controller = robot_task_system.task_controller:main',
            'robot_simulator = robot_task_system.robot_simulator:main',
            'task_monitor = robot_task_system.task_monitor:main',
        ],
    },
)

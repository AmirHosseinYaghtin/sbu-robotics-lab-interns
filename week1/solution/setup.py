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
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mohammad05',
    maintainer_email='mohammad05@todo.todo',
    description='TODO: Package description',
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
        ],
    },
)


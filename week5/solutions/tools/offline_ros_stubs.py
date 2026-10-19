"""Opt-in test doubles, NOT ROS emulation or integration evidence.

Imported only by run_offline_tests.py. Never installed as ROS packages.
"""
import copy
import enum
import sys
import time
import types


def module(name):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
        if '.' in name:
            parent, leaf = name.rsplit('.', 1)
            setattr(module(parent), leaf, sys.modules[name])
    return sys.modules[name]


def message(class_name, **defaults):
    class Message:
        def __init__(self, **values):
            for key, value in defaults.items():
                setattr(self, key, value() if callable(value) else copy.deepcopy(value))
            self.__dict__.update(values)
    Message.__name__ = class_name
    return Message


class Future:
    def __init__(self):
        self.value = None
        self.error = None
        self.ready = False
        self.callbacks = []

    def done(self):
        return self.ready

    def result(self):
        if self.error:
            raise self.error
        return self.value

    def set_result(self, value):
        self.value, self.ready = value, True
        for callback in list(self.callbacks):
            callback(self)

    def set_exception(self, error):
        self.error = error
        self.set_result(None)

    def add_done_callback(self, callback):
        if self.ready:
            callback(self)
        else:
            self.callbacks.append(callback)

    def __await__(self):
        if not self.ready:
            yield self
        return self.result()


class Duration:
    def __init__(self, seconds=0.0, nanoseconds=0):
        self.nanoseconds = int(seconds * 1e9) + nanoseconds

    def __add__(self, other):
        return Duration(nanoseconds=self.nanoseconds + other.nanoseconds)

    def __sub__(self, other):
        return Duration(nanoseconds=self.nanoseconds - other.nanoseconds)

    def __lt__(self, other):
        return self.nanoseconds < other.nanoseconds

    def __gt__(self, other):
        return self.nanoseconds > other.nanoseconds


class Parameter:
    def __init__(self, name, value=None):
        self.name, self.value = name, value


class Publisher:
    def __init__(self):
        self.messages = []

    def publish(self, value):
        self.messages.append(value)

    def get_subscription_count(self):
        return 0


class Logger:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class Node:
    def __init__(self, name, **node_options):
        self.name = name
        self.parameters = {}
        self.parameter_overrides = {
            parameter.name: parameter.value
            for parameter in node_options.get('parameter_overrides', [])}
        self.parameter_callbacks = []
        self.timer_callbacks = []

    def get_name(self):
        return self.name

    def declare_parameter(self, name, value):
        self.parameters[name] = Parameter(name, self.parameter_overrides.get(name, value))

    def get_parameter(self, name):
        return self.parameters[name]

    def add_on_set_parameters_callback(self, callback):
        self.parameter_callbacks.insert(0, callback)

    def set_parameters(self, parameters):
        results = []
        for parameter in parameters:
            result = types.SimpleNamespace(successful=True, reason='')
            for callback in self.parameter_callbacks:
                result = callback([parameter])
                if not result.successful:
                    break
            if result.successful:
                self.parameters[parameter.name] = parameter
            results.append(result)
        return results

    def get_clock(self):
        return types.SimpleNamespace(now=lambda: Duration(seconds=time.monotonic()))

    def get_logger(self):
        return Logger()

    def create_publisher(self, *args, **kwargs):
        return Publisher()

    def create_subscription(self, *args, **kwargs):
        return object()

    def create_service(self, *args, **kwargs):
        return object()

    def create_client(self, *args, **kwargs):
        return types.SimpleNamespace(service_is_ready=lambda: False, call_async=lambda request: Future())

    def create_timer(self, duration, callback):
        self.timer_callbacks.append(callback)
        return types.SimpleNamespace(cancel=lambda: None)

    def destroy_timer(self, *args):
        pass

    def destroy_node(self):
        pass


class ActionClient:
    def __init__(self, *args, **kwargs):
        pass

    def server_is_ready(self):
        return False

    def send_goal_async(self, *args, **kwargs):
        return Future()


class Response(enum.IntEnum):
    REJECT = 0
    ACCEPT = 1


def install():
    ros = module('rclpy')
    ros.init = lambda *args, **kwargs: None
    ros.shutdown = lambda: None
    ros.ok = lambda: True
    module('rclpy.node').Node = Node
    module('rclpy.duration').Duration = Duration
    module('rclpy.time').Time = Duration
    module('rclpy.parameter').Parameter = Parameter
    module('rclpy.task').Future = Future
    action = module('rclpy.action')
    action.ActionClient = ActionClient
    action.ActionServer = lambda *args, **kwargs: object()
    action.GoalResponse = action.CancelResponse = Response
    module('rclpy.callback_groups').ReentrantCallbackGroup = object
    qos = module('rclpy.qos')
    qos.QoSProfile = message('QoSProfile')
    qos.DurabilityPolicy = types.SimpleNamespace(TRANSIENT_LOCAL=1)
    qos.ReliabilityPolicy = types.SimpleNamespace(RELIABLE=1)
    module('rcl_interfaces.msg').SetParametersResult = message('SetParametersResult', successful=True, reason='')
    module('std_msgs.msg').Bool = message('Bool', data=False)
    module('std_msgs.msg').String = message('String', data='')
    trigger = type('Trigger', (), {'Request': message('Request'), 'Response': message('Response', success=False, message='')})
    module('std_srvs.srv').Trigger = trigger
    for name in ['GetRobotStatus', 'GetTaskStatus']:
        setattr(module('robot_task_interfaces.srv'), name, type(name, (), {
            'Request': message('Request'), 'Response': message('Response')}))
    msg = module('robot_task_interfaces.msg')
    msg.Waypoint = message('Waypoint', x=0.0, y=0.0, theta=0.0)
    msg.MoveCommand = message('MoveCommand', action_label='', reverse=False, waypoints=[])
    msg.ArmWaypoint = message('ArmWaypoint', joints=[])
    msg.ManipulatorCommand = message('ManipulatorCommand', action_label='', object_name='',
        grasp_dx=0.0, grasp_dy=0.0, grasp_dtheta=0.0, arm_start=[], arm_goal=[],
        trajectory=[], action_type='', frame_id='', target_x=0.0, target_y=0.0)
    for name in ['MoveTo', 'Manipulate']:
        setattr(module('robot_task_interfaces.action'), name, type(name, (), {
            'Goal': message('Goal', command=None),
            'Result': message('Result', success=False, message=''),
            'Feedback': message('Feedback')}))
    module('action_msgs.msg').GoalStatus = types.SimpleNamespace(
        STATUS_SUCCEEDED=4, STATUS_CANCELED=5, STATUS_ABORTED=6)
    module('builtin_interfaces.msg').Duration = message('Duration', sec=0, nanosec=0)
    module('control_msgs.action').GripperCommand = type('GripperCommand', (), {
        'Goal': message('Goal', command=lambda: types.SimpleNamespace(position=0.0, max_effort=0.0))})
    vector = message('Vector', x=0.0, y=0.0, z=0.0)
    module('geometry_msgs.msg').Twist = message('Twist', linear=vector, angular=vector)
    module('geometry_msgs.msg').PointStamped = message('PointStamped', point=vector,
        header=lambda: types.SimpleNamespace(frame_id=''))
    module('nav_msgs.msg').Odometry = message('Odometry')
    module('sensor_msgs.msg').JointState = message('JointState', name=[], position=[])
    module('trajectory_msgs.msg').JointTrajectory = message('JointTrajectory', joint_names=[], points=[])
    module('trajectory_msgs.msg').JointTrajectoryPoint = message('JointTrajectoryPoint', positions=[], time_from_start=None)
    module('tf2_geometry_msgs').do_transform_point = lambda point, transform: point
    module('tf2_ros').TransformException = type('TransformException', (Exception,), {})
    module('tf2_ros.buffer').Buffer = object
    module('tf2_ros.transform_listener').TransformListener = lambda *args: object()

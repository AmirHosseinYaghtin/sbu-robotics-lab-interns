"""ROS Action lifecycle around the existing nonblocking controller timers.

No worker threads, sleeps, or blocking spins. A reserved goal remains exclusive
until its result has been consumed by the execute coroutine.
"""
import time
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.task import Future
from std_srvs.srv import Trigger


class ControllerAction:
    def __init__(self, node, action_type, name, start, validate, feedback, stop, defer=False):
        self.node, self.action_type = node, action_type
        self.start, self.validate = start, validate
        self.feedback, self.stop = feedback, stop
        self.reserved = False
        self.handle = None
        self.future = None
        self.stop_reason = None
        self.stop_started = None
        self.emergency = False
        self.last_feedback = 0.0
        self.name = name
        self.server = None
        if not defer:
            self.activate()
        self.stop_service = node.create_service(
            Trigger, '/' + node.get_name() + '/emergency_stop', self.emergency_stop)

    def activate(self):
        if self.server is None:
            self.server = ActionServer(
                self.node, self.action_type, self.name, execute_callback=self.execute,
                goal_callback=self.goal, cancel_callback=self.cancel,
                callback_group=ReentrantCallbackGroup())

    def goal(self, request):
        if self.reserved or self.emergency or self.node.status != self.node.IDLE:
            return GoalResponse.REJECT
        try:
            self.validate(request.command)
        except Exception as error:
            self.node.get_logger().error('Goal rejected: ' + str(error))
            return GoalResponse.REJECT
        self.reserved = True
        return GoalResponse.ACCEPT

    def cancel(self, handle):
        # The timer observes is_cancel_requested only after rclpy transitions
        # the goal to CANCELING. Do not call canceled() inside this callback.
        return CancelResponse.ACCEPT

    async def execute(self, handle):
        self.handle = handle
        self.future = Future()
        self.stop_reason = None
        self.stop_started = None
        try:
            if self.emergency or handle.is_cancel_requested:
                self.request_stop('software emergency stop' if self.emergency else 'canceled')
            else:
                self.start(handle.request.command)
            return await self.future
        except Exception as error:
            self.request_stop('controller exception: ' + str(error))
            # Keep the result pending until the timer completes the software stop procedure.
            return await self.future
        finally:
            self.handle = None
            self.future = None
            self.reserved = False
            self.stop_reason = None
            self.stop_started = None

    def request_stop(self, reason):
        if self.stop_reason is None:
            self.stop_reason = reason
            self.stop_started = time.monotonic()

    def emergency_stop(self, request, response):
        self.emergency = True
        self.request_stop('software emergency stop')
        # Also stop startup homing or an idle controller, not just task goals.
        self.try_stop()
        response.success = True
        response.message = 'Software stop latched; reset controller explicitly after inspection'
        return response

    def try_stop(self):
        try:
            return self.stop()
        except Exception as error:
            self.node.status = self.node.ERROR
            self.node.get_logger().error('Software stop error: ' + str(error))
            return False

    def tick(self):
        if self.handle is not None and self.handle.is_cancel_requested:
            self.request_stop('canceled')
        if self.stop_reason is not None:
            if self.try_stop():
                if self.handle is not None:
                    canceled = self.handle.is_cancel_requested
                    self.complete(False, self.stop_reason, canceled=canceled)
                elif not self.reserved:
                    self.stop_reason = None
                return True
            if time.monotonic() - self.stop_started > 15.0:
                self.node.status = self.node.ERROR
                self.complete(False, 'stop unconfirmed: ' + self.stop_reason)
            return True
        if self.emergency:
            self.try_stop()
            return True
        if self.handle is not None and self.handle.is_active and time.monotonic() - self.last_feedback >= 0.5:
            self.handle.publish_feedback(self.feedback())
            self.last_feedback = time.monotonic()
        return False

    def complete(self, success, message, canceled=False):
        if self.handle is None or self.future is None or self.future.done():
            return
        if not success and not canceled and self.stop_reason is None:
            self.request_stop(message)
            return
        result = self.action_type.Result(success=bool(success), message=message)
        if canceled:
            self.handle.canceled()
        elif success:
            self.handle.succeed()
        else:
            self.handle.abort()
        self.future.set_result(result)

    def reset(self):
        if self.reserved:
            return False
        self.emergency = False
        self.stop_reason = None
        self.stop_started = None
        return True

"""Task bookkeeping, independent of ROS and of the planner."""

class TaskState:
    TERMINAL = {'FAILED', 'CANCELED', 'COMPLETED', 'EMERGENCY_STOP'}

    def __init__(self, plan_file, total):
        self.plan_file = plan_file
        self.total_actions = total
        self.completed_actions = 0
        self.task_state = 'IDLE'
        self.current_action = 'NONE'
        self.action_state = 'IDLE'
        self.message = ''

    def begin(self, label):
        if self.task_state in self.TERMINAL or self.task_state == 'CANCELING':
            raise RuntimeError('task is stopped')
        self.task_state = 'EXECUTING'
        self.current_action = label
        self.action_state = 'SENDING'

    def stop(self, reason, emergency=False, failure=False):
        if self.task_state in self.TERMINAL and not emergency:
            return
        self.task_state = 'EMERGENCY_STOP' if emergency else ('FAILED' if failure else 'CANCELING')
        self.message = reason
        if self.current_action != 'NONE':
            self.action_state = 'CANCELING'
        elif not emergency and not failure:
            self.task_state = 'CANCELED'

    def result(self, succeeded, canceled=False, message=''):
        if self.task_state in self.TERMINAL or self.task_state == 'CANCELING':
            if message:
                self.message = (self.message + '; action result: ' + message) if self.message else message
            self.action_state = 'CANCELED' if canceled else ('SUCCEEDED' if succeeded else 'FAILED')
            if succeeded:
                self.completed_actions += 1
            if self.task_state == 'CANCELING':
                self.task_state = 'CANCELED' if canceled or succeeded else 'FAILED'
            return False
        self.message = message or self.message
        if canceled:
            self.task_state, self.action_state = 'CANCELED', 'CANCELED'
            return False
        if not succeeded:
            self.task_state, self.action_state = 'FAILED', 'FAILED'
            return False
        self.completed_actions += 1
        self.action_state = 'SUCCEEDED'
        self.current_action = 'NONE'
        if self.completed_actions == self.total_actions:
            self.task_state = 'COMPLETED'
        return True

    def snapshot(self):
        return dict(vars(self))

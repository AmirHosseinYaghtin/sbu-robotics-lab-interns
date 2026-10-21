"""Validate configurable execution limits without callback side effects."""
import math
from rcl_interfaces.msg import SetParametersResult


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0.0


def install_validation(node, rules, startup_only=()):
    def check(parameters):
        for parameter in parameters:
            name, value = parameter.name, parameter.value
            if name in startup_only:
                return SetParametersResult(successful=False, reason=name + ' requires restart')
            if name in rules:
                if not rules[name](value):
                    return SetParametersResult(successful=False, reason='invalid ' + name)
                if getattr(node, 'status', 'IDLE') != 'IDLE':
                    return SetParametersResult(successful=False, reason='execution settings change only while IDLE')
        return SetParametersResult(successful=True)
    for name, rule in rules.items():
        if not rule(node.get_parameter(name).value):
            raise ValueError('invalid initial parameter: ' + name)
    node.add_on_set_parameters_callback(check)

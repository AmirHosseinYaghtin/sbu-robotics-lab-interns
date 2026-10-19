"""Startup guards and a conservative fallback for TODO-W5-02.

Dynamic parameter configuration is deliberately unfinished. Keep startup safety
checks; reject managed changes until the teammate implements the idle/active
policy and restores the execution-limit parameters.
"""
import math
from rcl_interfaces.msg import SetParametersResult


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0.0


def validate_startup(node, rules):
    for name, rule in rules.items():
        if not rule(node.get_parameter(name).value):
            raise ValueError('invalid initial parameter: ' + name)


def freeze_parameters(node, names):
    managed = frozenset(names)

    def check(parameters):
        for parameter in parameters:
            if parameter.name in managed:
                return SetParametersResult(
                    successful=False,
                    reason='TODO-W5-02: execution settings are frozen; restart for existing startup settings')
        return SetParametersResult(successful=True)

    node.add_on_set_parameters_callback(check)

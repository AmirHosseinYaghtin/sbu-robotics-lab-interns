import math

LINK_1 = 0.23
LINK_2 = 0.22


def forward_kinematics(joints):
    j1 = float(joints[0])
    j2 = float(joints[1])
    x = LINK_1 * math.cos(j1) + LINK_2 * math.cos(j1 + j2)
    y = LINK_1 * math.sin(j1) + LINK_2 * math.sin(j1 + j2)
    return x, y

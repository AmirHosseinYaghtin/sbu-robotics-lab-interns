"""Export a PDDLStream continuous2d plan, plus the map it was solved on, to JSON.

Run from the root of the pddlstream-robocup-at-work checkout:

    python export_plan.py --list
    python export_plan.py -p get_pick_and_place_problem -o plan_pick_place.json
    python export_plan.py -p get_at_work_problem --skeleton -o plan_at_work.json

The "scene" block describes the map (furniture, regions, objects, sizes, and
initial base pose) so the ROS side can build the matching Gazebo world without
any hand-copied coordinates.
"""

from __future__ import print_function

import argparse
import json

import numpy as np

from domains.continuous2d import run as continuous2d
from domains.continuous2d.primitives import get_object_size
from pddlstream.language.constants import print_solution

SCHEMA_VERSION = 2
SKELETON_PROBLEMS = ('get_at_work_problem',)


def to_jsonable(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return [to_jsonable(x) for x in obj.tolist()]
    if isinstance(obj, tuple) and hasattr(obj, "_fields"):
        d = {"__type__": type(obj).__name__}
        for f in obj._fields:
            d[f] = to_jsonable(getattr(obj, f))
        return d
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    return obj


def action_to_dict(action):
    name, args = action[0], action[1]
    return {"name": name, "args": [to_jsonable(a) for a in args]}


def _size(name):
    return [float(v) for v in get_object_size(name)]


def scene_to_dict(tamp_problem):
    """Describe the map. Call after problem_fn(): it fills OBJECT_SIZES."""
    initial = tamp_problem.initial
    base = initial.base_conf
    return {
        "frame": "planner",
        "initial_base": {"x": float(base.x), "y": float(base.y),
                         "theta": float(base.theta)},
        "objects": [
            {
                "name": str(name),
                "type": str(obj_type),
                "size": _size(obj_type),
                "pose": [float(v) for v in initial.object_poses[name]],
                "goal_region": tamp_problem.goal_regions.get(name),
            }
            for name, obj_type in sorted(tamp_problem.object_types.items())
        ],
        "furniture": [
            {
                "name": str(name),
                "size": _size(name),
                "pose": [float(v) for v in pose],
                "is_region": name in tamp_problem.regions,
            }
            for name, pose in tamp_problem.furniture
        ],
        "regions": {
            str(name): {"lower": [float(v) for v in region.lower],
                        "upper": [float(v) for v in region.upper]}
            for name, region in tamp_problem.regions.items()
        },
    }


def main():
    names = [fn.__name__ for fn in continuous2d.PROBLEMS]
    parser = argparse.ArgumentParser(description="Export a PDDLStream plan and its map to JSON")
    parser.add_argument("-p", "--problem", default=continuous2d.DEFAULT_PROBLEM,
                        help="problem function name: " + ", ".join(names))
    parser.add_argument("--list", action="store_true", help="list problems and exit")
    parser.add_argument("-ma", "--merge", dest="merge", action="store_true", default=True,
                        help="merged pick_and_stow/unstow_and_place actions (default)")
    parser.add_argument("--no-merge", dest="merge", action="store_false",
                        help="separate pick/stow/unstow/place (not executable by ROS)")
    parser.add_argument("-s", "--skeleton", action="store_true",
                        help="use the repository's hard skeleton (at_work only)")
    parser.add_argument("-c", "--cfree", action="store_true", help="disable collision checking")
    parser.add_argument("--algorithm", default="adaptive",
                        help="incremental | focused | binding | adaptive")
    parser.add_argument("--max-time", type=float, default=300.0)
    parser.add_argument("--seed", type=int, default=None, help="numpy random seed")
    parser.add_argument("-o", "--output", default="plan.json")
    args = parser.parse_args()

    if args.list:
        print("\n".join(names))
        return 0
    if args.skeleton and args.problem not in SKELETON_PROBLEMS:
        parser.error("--skeleton is TIGHT_SKELETON_work and only fits: "
                     + ", ".join(SKELETON_PROBLEMS))
    if args.seed is not None:
        np.random.seed(args.seed)

    problem_fn = continuous2d.get_problem_fn(args.problem)
    tamp_problem = problem_fn()
    scene = scene_to_dict(tamp_problem)

    solution = continuous2d.solve_tamp(
        tamp_problem,
        algorithm=args.algorithm,
        collisions=not args.cfree,
        merge_pick_and_stow=args.merge,
        skeleton=args.skeleton,
        max_time=args.max_time,
    )
    print_solution(solution)

    plan, cost, evaluations = solution
    if plan is None:
        print("No plan found -- try re-running (sampling is randomized) or --algorithm adaptive.")
        return 1

    out = {
        "schema_version": SCHEMA_VERSION,
        "problem": args.problem,
        "merged_actions": bool(args.merge),
        "algorithm": args.algorithm,
        "cost": float(cost),
        "length": len(plan),
        "scene": scene,
        "actions": [action_to_dict(a) for a in plan],
    }
    with open(args.output, "w") as f:
        json.dump(out, f, indent=2)
    print("\nWrote {} ({} actions, cost {:.3f}).".format(args.output, len(plan), cost))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

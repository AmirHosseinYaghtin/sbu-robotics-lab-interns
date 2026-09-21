from __future__ import print_function

import argparse
import json

import numpy as np

from domains.continuous2d.run import get_problem_fn, solve_tamp
from pddlstream.language.constants import print_solution


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


def main():
    parser = argparse.ArgumentParser(description="Export a PDDLStream plan to JSON")
    parser.add_argument("-p", "--problem", default="get_pick_and_place_problem",
                        help="problem function name from domains.continuous2d.run.PROBLEMS")
    parser.add_argument("--merge", dest="merge", action="store_true", default=True,
                        help="merge pick/stow actions (default: on)")
    parser.add_argument("--no-merge", dest="merge", action="store_false",
                        help="use separate pick/stow/unstow/place actions")
    parser.add_argument("--algorithm", default="adaptive",
                        help="incremental | focused | binding | adaptive")
    parser.add_argument("--max-time", type=float, default=300.0)
    parser.add_argument("-o", "--output", default="plan.json")
    args = parser.parse_args()

    problem_fn = get_problem_fn(args.problem)
    tamp_problem = problem_fn()

    solution = solve_tamp(
        tamp_problem,
        algorithm=args.algorithm,
        collisions=True,
        merge_pick_and_stow=args.merge,
        max_time=args.max_time,
    )
    print_solution(solution)

    plan, cost, evaluations = solution
    if plan is None:
        print("No plan found -- try re-running (sampling is randomized) or --algorithm adaptive.")
        return 1

    out = {
        "problem": args.problem,
        "merged_actions": bool(args.merge),
        "algorithm": args.algorithm,
        "cost": float(cost),
        "length": len(plan),
        "actions": [action_to_dict(a) for a in plan],
    }
    with open(args.output, "w") as f:
        json.dump(out, f, indent=2)
    print("\nWrote {} ({} actions, cost {:.3f}).".format(args.output, len(plan), cost))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

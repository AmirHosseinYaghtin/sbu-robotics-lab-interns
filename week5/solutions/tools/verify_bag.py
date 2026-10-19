"""TODO-W5-03: implement isolated verification of a real rosbag2 recording."""

import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bag', help='path to a real recorded rosbag2 directory')
    parser.add_argument('--timeout', type=float, default=600.0)
    parser.parse_args()
    parser.error(
        'TODO-W5-03: inspect bag info, replay in an isolated ROS domain, and '
        'verify recorded task status and robot data. Verification is not implemented.')


if __name__ == '__main__':
    main()

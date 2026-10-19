"""Run pure regressions and explicitly mocked controller unit tests (no DDS).

Usage: python3 tools/run_offline_tests.py
Requires pytest and PyYAML. This is NOT a replacement for colcon/ROS/Gazebo.
"""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src/robot_task_system'))
from offline_ros_stubs import install
install()
import pytest

tests = root / 'src/robot_task_system/test'
files = [str(p) for p in sorted(tests.glob('test_*.py')) if p.name not in {
    'test_copyright.py', 'test_flake8.py', 'test_pep257.py', 'test_week05_ros_integration.py'}]
# Collect the teammate's pending acceptance cases and report their explicit skips.
files += [str(p) for p in sorted((tests / 'remaining').glob('test_*.py'))]
raise SystemExit(pytest.main(['-q', *files, *sys.argv[1:]]))

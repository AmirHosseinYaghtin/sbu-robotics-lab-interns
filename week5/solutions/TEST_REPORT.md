# Verification of the 67/33 handoff

Checked on Windows, Python 3.12.4, on 2026-10-19. ROS 2/rclpy, generated ROS
interfaces, colcon and Gazebo are unavailable in this execution environment.

| Check actually executed | Result |
|---|---|
| Uploaded completed archive, offline functional suite | 178 passed |
| Modified archive, offline functional suite | 171 passed, 11 explicitly skipped |
| Retained functional tests | 167 passed (178 minus 11 deferred parameter cases) |
| Added boundary checks | 4 passed: forward/reverse fixed-speed approach, frozen runtime setting, full TaskController startup/dispatch without status publishing |
| Deferred acceptance cases | 11 parameter cases, moved to `test/remaining/test_parameter_acceptance.py`; skip is intentional, never reported as success |
| Syntax and JSON/YAML/XML/SDF/interface-path checks | Passed; details in `test_evidence/static_checks.json` |
| Deferred recording entry points | Both exit 2 with TODO-W5-03 before ROS/simulation startup |
| Source preservation checks | Passed; see `test_evidence/static_checks.json` and `input_file_manifest.json` |
| ROS/DDS integration, rosidl/colcon/C++ build | Not executed |
| Gazebo physics, live failure/cancel demonstration | Not executed |
| Actual rosbag record/info/playback | Intentionally pending TODO-W5-03; not executed |

Offline tests explicitly install doubles for ROS APIs and messages. They verify
Python execution/state branches, not DDS transport, generated message support,
timing, physics, object placement or physical stopping. The separate live ROS
integration module remains and needs the lab environment. Its no-odom tests now
expire the controller's deadline directly because runtime timeout parameters are
part of the deferred work.

`tools/run_offline_tests.py` now accepts normal pytest arguments and includes
pending parameter tests so their skipped status is visible. The normal offline
suite excludes ROS integration and ament copyright/style plugins, as before.
The runner's doubles support constructor parameter overrides for the new startup
test. They are only loaded explicitly by the runner and are not installed.

Raw successful pytest output is retained in `test_evidence/input_offline.txt`
and `split_offline.txt`. A Windows console-cleanup exception from pyreadline3 can
appear after the pytest summary; pytest returned exit code 0. An initial run used
a restricted default temp directory; rerunning with a workspace temp directory
resolved the seven temp-directory setup errors, without changing product code.

The original archive's historical test reports were replaced to avoid presenting
its completed features/results as evidence for this intentionally partial copy.
The provided older-baseline hash manifest is retained separately for provenance.

To reproduce the current offline check from the workspace root:

```bash
python3 tools/run_offline_tests.py
# Optional on Windows if the default temp directory is restricted:
python tools/run_offline_tests.py --basetemp=./test_tmp
```

Follow `WEEK05.md` for ROS integration, build and simulation checks. Passing the
offline suite does not establish that the final lab deployment is complete.

# Changes relative to the uploaded completed ZIP

All paths below are relative to this workspace. The input archive is untouched.

- TODO-W5-01: removed task publisher/service wiring and task-level monitor view; retained interface schema and internal state.
- TODO-W5-02: removed new execution-limit parameter declarations/readbacks/YAML; retained matching fixed defaults and conservative startup/frozen guards.
- TODO-W5-03: removed recorder/replay implementation, QoS and bag-only dependencies; retained physical verification and explicit failing scaffolds.
- Retained all Action/cancellation/failure/stop machinery. The shared Action lifecycle, internal state and Action schemas are byte-identical.
- Deferred 11 parameter acceptance cases; retained 167 functional cases and added four boundary checks.
- Replaced historical completed-feature reports/evidence with current results.

## Scope and baseline

The requirements are from the supplied week05-exercise.pdf. The read-only GitHub comparison used
`week03-04-exercise` at `bfe36088f52701f3d9732fa63607d45a88d0b9a7`:
[verified branch commit](https://github.com/Seyed0Mohammad0Hosseini/sbu-robotics-lab-interns/commit/bfe36088f52701f3d9732fa63607d45a88d0b9a7).

That branch predates the uploaded maps/fixed baseline. The supplied hash manifest
marks 54 files as pre-week-five unchanged; all 54 remain byte-identical.
Earlier map/scene/order/geometry/calibration work was excluded from the 67/33 estimate.
No GitHub write or push was performed.

## Changed implementation/configuration

- `src/robot_task_system/robot_task_system/task_controller.py`
- `src/robot_task_system/robot_task_system/task_monitor.py`
- `src/robot_task_system/robot_task_system/robot_controller.py`
- `src/robot_task_system/robot_task_system/manipulator_controller.py`
- `src/robot_task_system/robot_task_system/parameter_validation.py`
- `src/robot_task_system/config/pick_place.yaml`
- `src/robot_task_system/package.xml`
- `tools/verify_pick_place.py`
- `tools/verify_bag.py`

## Changed tests and offline support

- `src/robot_task_system/test/test_week05_execution.py`
- `src/robot_task_system/test/test_week05_ros_integration.py`
- `tools/offline_ros_stubs.py`
- `tools/run_offline_tests.py`

## Removed feature file

- `src/robot_task_system/config/recording_qos.yaml`

## Added files

- `CHANGES.md`
- `README.md`
- `TEAMMATE_TASKS.md`
- `src/robot_task_system/test/remaining/test_parameter_acceptance.py`
- `src/robot_task_system/test/test_split_handoff.py`
- `test_evidence/input_file_manifest.json`
- `test_evidence/input_offline.txt`
- `test_evidence/provided_pre_week05_hashes.json`
- `test_evidence/split_offline.txt`
- `test_evidence/static_checks.json`

## Other replaced or removed files

- changed: `TEST_REPORT.md`
- changed: `WEEK05.md`
- removed: `test_evidence/original_baseline.txt`
- removed: `test_evidence/original_file_hashes.json`
- removed: `test_evidence/updated_offline.txt`
- removed: `test_evidence/updated_pure.txt`

Machine-readable input/output SHA-256 values are in
`test_evidence/input_file_manifest.json`. New evidence is in `static_checks.json`.

import copy
import json
import math
import os
import xml.etree.ElementTree as ET

import pytest
from robot_task_system import plan_geometry
from robot_task_system import scene

CONFIG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
PLANS = os.path.join(CONFIG, 'plans')
MAPS = sorted(f[:-5] for f in os.listdir(PLANS) if f.endswith('.json'))
SCENE_YAML = os.path.join(CONFIG, 'scene.yaml')


def prepared(name, config=None, offset=(0.0, 0.0)):
    return scene.prepare_plan(os.path.join(PLANS, name + '.json'), config, offset)


def test_every_planner_map_is_shipped():
    assert {'pick_place', 'corridor', 'multi_object', 'at_work', 'simple'} <= set(MAPS)


def test_scene_yaml_matches_defaults():
    assert scene.load_config(SCENE_YAML) == scene.DEFAULT_CONFIG


def test_unknown_config_key_is_rejected(tmp_path):
    path = tmp_path / 'bad.yaml'
    path.write_text('surface_hieght: 0.05\n')
    with pytest.raises(scene.SceneError):
        scene.load_config(str(path))


def test_verified_plan_reproduces_hand_tuned_scene():
    # The coordinates that used to be hard-coded in pick_place.launch.py.
    _, _, result = scene.prepare_plan(os.path.join(CONFIG, 'plan_pick_place.json'))
    cube = result['objects'][0]
    assert cube['name'] == 'cube1'
    assert (cube['x'], cube['y']) == pytest.approx((0.8, 1.0), abs=1e-3)
    assert cube['z'] == pytest.approx(0.051)
    assert cube['yaw'] == pytest.approx(-0.654, abs=1e-3)
    assert result['expected_final']['cube1'] == pytest.approx((-1.27, 1.246), abs=1e-3)
    kinds = sorted(b['kind'] for b in result['boxes'])
    assert kinds == ['pick_stand', 'place_stand']


def test_simple_map_has_only_the_cube_and_two_stands():
    _, _, result = prepared('simple')
    assert [o['name'] for o in result['objects']] == ['cube1']
    assert sorted(b['kind'] for b in result['boxes']) == ['pick_stand', 'place_stand']
    _, _, default = scene.prepare_plan(os.path.join(CONFIG, 'plan_pick_place.json'))
    for key in ('boxes', 'objects', 'expected_final'):
        assert result[key] == default[key]


def test_pick_place_map_spawns_planner_furniture():
    _, _, result = prepared('pick_place')
    kinds = {b['name']: b['kind'] for b in result['boxes']}
    assert kinds['shelf0'] == 'obstacle'
    assert kinds['table1'] == 'region'


@pytest.mark.parametrize('name', MAPS)
def test_every_map_builds_a_consistent_scene(name):
    plan, actions, result = prepared(name)
    picks = {a['obj'] for a in actions if a['type'] == 'pick'}
    assert {o['name'] for o in result['objects']} == picks
    assert set(result['expected_final']) == picks
    stands = [b for b in result['boxes'] if b['kind'] == 'pick_stand']
    assert len(stands) == len(picks)
    places = [a for a in actions if a['type'] == 'place']
    assert len([b for b in result['boxes'] if b['kind'] == 'place_stand']) == len(places)
    for obj in plan['scene']['objects']:
        assert obj['name'] in picks


@pytest.mark.parametrize('name', MAPS)
def test_every_map_is_reachable_after_approach(name):
    _, actions, _ = prepared(name)
    result = plan_geometry.prepare_actions(actions)
    for action in result:
        if action['type'] == 'move_base':
            continue
        local = plan_geometry.world_to_local(action['base_conf'], action['target_world'])
        assert math.hypot(local[0] + 0.092, local[1]) == pytest.approx(0.20, abs=1e-6)
        assert action['consistency_error'] < 1e-3


def test_offset_moves_the_whole_scene():
    _, _, origin = prepared('corridor')
    _, _, shifted = prepared('corridor', offset=(1.0, -2.0))
    for a, b in zip(origin['boxes'] + origin['objects'], shifted['boxes'] + shifted['objects']):
        assert b['x'] == pytest.approx(a['x'] + 1.0)
        assert b['y'] == pytest.approx(a['y'] - 2.0)


def test_full_surface_mode_spawns_tables_instead_of_pedestals():
    config = dict(scene.DEFAULT_CONFIG, surface_mode='full')
    _, _, result = prepared('pick_place', config)
    kinds = {b['kind'] for b in result['boxes']}
    assert 'surface' in kinds
    assert 'pick_stand' not in kinds and 'region' not in kinds


def test_plan_without_scene_block_still_spawns_objects(tmp_path):
    with open(os.path.join(PLANS, 'multi_object.json')) as file:
        plan = json.load(file)
    del plan['scene']
    path = tmp_path / 'legacy.json'
    path.write_text(json.dumps(plan))
    _, _, result = scene.prepare_plan(str(path))
    assert {o['name'] for o in result['objects']} == {'cube1', 'cube2', 'cube3'}
    assert not [b for b in result['boxes'] if b['kind'] == 'obstacle']


def test_anchor_maps_start_pose_to_origin():
    transform = scene.make_transform((1.0, 2.0, math.pi / 2))
    assert transform(1.0, 2.0, math.pi / 2) == pytest.approx((0.0, 0.0, 0.0))
    assert transform(1.0, 3.0, 0.0)[:2] == pytest.approx((1.0, 0.0))


@pytest.mark.parametrize('name', MAPS)
def test_generated_sdf_is_valid_xml(name, tmp_path):
    config = scene.load_config(SCENE_YAML)
    _, _, result = prepared(name, config)
    scene_path, objects = scene.write_scene_files(result, config, str(tmp_path))
    root = ET.parse(scene_path).getroot()
    assert len(root.find('model').findall('link')) == len(result['boxes'])
    for obj, path in objects:
        model = ET.parse(path).getroot().find('model')
        assert model.get('name') == obj['name']
        plugin = model.find('plugin')
        assert plugin.get('filename') == 'librobot_object_attachment.so'


def test_build_scene_does_not_modify_actions():
    _, actions, _ = prepared('at_work')
    before = copy.deepcopy(actions)
    scene.build_scene({}, actions)
    assert actions == before

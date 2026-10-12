import json
import mimetypes
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from web_client.simulation import EvaluationConfig
from conf.client_conf import get_client_config

playwright = pytest.importorskip('playwright.sync_api')
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def dashboard_browser():
    with playwright.sync_playwright() as runtime:
        try:
            browser = runtime.chromium.launch(headless=True, args=['--no-sandbox'])
        except playwright.Error as error:
            if "Executable doesn't exist" in str(error):
                pytest.skip('Install Chromium with: python -m playwright install chromium --only-shell')
            raise
        yield browser
        browser.close()


@pytest.mark.parametrize('selection', ['single', 'suite'])
def test_dashboard_evaluation_controls_and_shared_preview(dashboard_browser, tmp_path, selection):
    page = dashboard_browser.new_page(viewport={'width': 1600, 'height': 1000})
    errors, requests, jobs = [], [], []
    defaults = EvaluationConfig(env_name='PickPlaceCounterToCabinet').model_dump()
    client_config = json.loads(json.dumps(get_client_config().to_dict(), default=lambda value: value.value))
    client_config['robots']['type'] = 'mock'
    client_config['vla_zmq'].update(ip='192.0.2.10', port='5566')
    page.on('pageerror', lambda error: errors.append(str(error)))

    def route_request(route):
        request = route.request
        path = urlparse(request.url).path
        if path.startswith('/api/'):
            data = {}
            if path == '/api/client/config':
                data = {'config': client_config}
            elif path == '/api/simulation/options':
                platform = parse_qs(urlparse(request.url).query).get('platform', ['robocasa'])[0]
                data = {**defaults, 'platform': platform, 'robotwin_root': '/configured/RoboTwin',
                        'server_ip': '192.0.2.10', 'server_port': 5566}
                if platform == 'robotwin':
                    data.update(n_action_steps=50, seed=0)
            elif path == '/api/simulation/jobs':
                if request.method == 'POST':
                    config = json.loads(request.post_data)
                    config = EvaluationConfig(**config).model_dump()
                    requests.append(config)
                    jobs.append({'id': 'test-job', 'status': 'running', 'config': config,
                                 'progress': [{'env_name': config['env_name'] or config['task_suite'].split(',')[0], 'num_episodes': 2, 'success_rate': .5}], 'stats': []})
                    data = jobs[-1]
                else:
                    data = jobs
            elif path == '/api/simulation/preview':
                data = {'job': {'id': 'test-job', 'env_name': 'Task'} if jobs and jobs[-1]['status'] == 'running' else None, 'frames': [], 'trajectory': {'stream_id': 'test-stream', 'labels': ['left_joint', 'right_joint'], 'samples': [{'sequence': 1, 'timestamp': 1.0, 'state': [.1, .2]}]}}
            elif path.endswith('/stop'):
                jobs[-1]['status'] = 'cancelled'
            elif path.endswith('/resume'):
                jobs[-1]['status'] = 'running'
            elif path.endswith('/logs'):
                data = {'text': 'evaluation log'}
            elif path.endswith('/files'):
                data = ['output/stats.json', 'output/episode.mp4']
            elif path == '/api/simulation/jobs/test-job':
                data = jobs[-1]
            route.fulfill(json=data)
            return
        relative = ('web_client/static/index.html' if path == '/' else
                    'web_client/static/simulation.html' if path == '/simulation' else
                    'web_client/static/' + path[len('/static/'):] if path.startswith('/static/') else path.lstrip('/'))
        file = ROOT / relative
        if file.is_file():
            route.fulfill(body=file.read_bytes(), content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:
            route.fulfill(status=404, body='')

    page.route('**/*', route_request)
    page.goto('http://dashboard.test/')
    robot_selector = page.locator('.cfg-row[data-key="robots.type"] select').first
    robot_selector.wait_for()
    assert page.locator('#sim-start').is_disabled()
    robot_selector.select_option('robocasa')
    page.wait_for_function('document.getElementById("sim-start").disabled === false')
    assert page.locator('#sim-field-platform').count() == 0
    assert 'robocasa' in page.locator('#sim-configuration-summary').inner_text()
    robot_selector.select_option('aloha_robotwin')
    page.wait_for_function('document.getElementById("sim-start").disabled === false')
    page.locator('.cfg-row[data-key="rdm.mode"] select').first.select_option('async' if selection == 'suite' else 'sync')
    page.locator('.cfg-row[data-key="intra_chunk.intra_chunk_mode"] select').first.select_option('raw')
    page.locator('.cfg-row[data-key="controller.action_steps"] input').first.fill('48')
    page.locator('.cfg-row[data-key="controller.period"] input').first.fill('4.5')
    ids = page.locator('[id]').evaluate_all('(nodes) => nodes.map(node => node.id)')
    assert len(ids) == len(set(ids))
    assert page.locator('#simulation-body').is_hidden()
    page.locator('#panel-simulation-header > span').click()
    assert page.locator('#simulation-body').is_visible()
    assert page.locator('#config-body').is_hidden()
    assert page.url == 'http://dashboard.test/'
    page.wait_for_function('document.getElementById("sim-start").disabled === false')
    assert page.locator('#sim-field-python').count() == 0
    assert page.locator('#sim-field-robotwin_root').count() == 0
    assert page.locator('#sim-field-server_ip').count() == 0
    assert page.locator('#sim-field-record_fps').count() == 0
    assert page.locator('#sim-field-no_expert_check').count() == 0
    assert page.locator('#sim-fields input, #sim-fields select').count() == 5
    assert page.locator('#sim-field-mode').count() == 0
    assert page.locator('#sim-field-intra_chunk_mode').count() == 0
    page.locator('#sim-task-selection').select_option(selection)
    page.locator('#sim-task-name').fill('Task' if selection == 'single' else 'Task,OtherTask')
    page.locator('#sim-field-record').check()
    page.locator('#sim-start').click()
    page.wait_for_function('document.getElementById("sim-stop").disabled === false')
    assert requests[0]['platform'] == 'robotwin'
    assert requests[0]['record'] is True
    assert requests[0]['mode'] == ('async' if selection == 'suite' else 'sync')
    assert requests[0]['async_replenish_threshold'] == (0 if selection == 'suite' else None)
    assert requests[0]['n_action_steps'] == 48
    assert requests[0]['control_period_ms'] == 4.5
    assert requests[0]['client_config']['robots']['type'] == 'aloha_robotwin'
    assert requests[0]['client_config']['intra_chunk']['intra_chunk_mode'] == 'raw'
    assert requests[0]['intra_chunk_mode'] == 'raw'
    assert requests[0]['seed'] == 0
    assert requests[0]['env_name'] == ('Task' if selection == 'single' else '')
    assert requests[0]['task_suite'] == ('Task,OtherTask' if selection == 'suite' else '')
    assert requests[0]['robotwin_root'] == '/configured/RoboTwin'
    assert requests[0]['server_ip'] == '192.0.2.10'
    assert requests[0]['server_port'] == 5566
    assert requests[0]['record_fps'] == 20
    assert requests[0]['video_layout'] == 'grid'
    assert requests[0]['no_expert_check'] is False
    assert '2 / 10' in page.locator('#sim-results').inner_text()
    page.wait_for_function('simulationPreview.active === true')
    assert 'Simulation Trajectories' in page.locator('#trajectory-source-label').inner_text()
    page.locator('#sim-preview-source').select_option('robot')
    page.wait_for_function('simulationPreview.active === false')
    assert page.locator('#camera-source-label').inner_text() == 'Camera Viewer'
    assert page.evaluate('App.traj.simulationLayout == null')
    page.locator('#sim-preview-source').select_option('simulation')
    page.wait_for_function('simulationPreview.active === true')
    page.locator('#sim-files').select_option('output/episode.mp4')
    assert page.locator('#sim-video').is_visible()
    assert page.locator('#sim-video').get_attribute('src').endswith('/output/episode.mp4')
    page.locator('#sim-config summary').filter(has_text='Evaluation Configuration').click()
    page.screenshot(path=str(tmp_path / 'simulation-dashboard.png'))
    page.locator('#sim-stop').click()
    page.wait_for_function('document.getElementById("sim-resume").disabled === false')
    page.locator('#sim-resume').click()
    page.wait_for_function('document.getElementById("sim-stop").disabled === false')
    page.locator('#panel-config-header > span').click()
    robot_selector.select_option('mock')
    assert page.locator('#sim-start').is_disabled()
    assert len(requests) == 1
    page.locator('#panel-recording-header > span').click()
    assert page.locator('#simulation-body').is_hidden()
    assert page.locator('#recording-body').is_visible()
    page.goto('http://dashboard.test/simulation')
    page.wait_for_function('document.getElementById("field-platform") !== null')
    assert page.locator('#task-name').is_visible()
    assert page.locator('#field-python').count() == 0
    assert not errors
    page.close()

import asyncio
import json
import threading
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from ml_collections import ConfigDict

from client.core.task_language_manager import TaskLanguageManager
from client.core.vla_client import VLAClient
from web_client import server


def _runtime(tmp_path, monkeypatch):
    language_file = tmp_path / 'language.json'
    language_file.write_text(json.dumps({'tea': ['first', 'second'], 'coffee': ['brew']}))
    language_cfg = ConfigDict({
        'file_path': str(language_file),
        'task_id': 'tea',
        'sub_task_id': 0,
        'auto_mode': False,
        'auto_mode_start_sub_task_id': 0,
    })
    config = SimpleNamespace(language=language_cfg, record=SimpleNamespace(switch=False))
    runtime = SimpleNamespace(config=config, task_language_manager=TaskLanguageManager(language_cfg))
    monkeypatch.setattr(server.client_state, 'vla_client', runtime)
    monkeypatch.setattr(server.client_state, 'robot', object())
    monkeypatch.setattr(server.client_state, 'lock', threading.Lock())
    return runtime


def test_repeated_selection_applies_even_when_index_is_unchanged(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path, monkeypatch)
    req = server.LanguageSelectRequest(task_id='tea', sub_task_id=1, language='second')
    for _ in range(2):
        runtime.task_language_manager.currt_language_instruction = 'stale'
        result = asyncio.run(server.client_language_select(req))
        assert result['language'] == 'second'
        assert runtime.config.language.sub_task_id == 1
        assert runtime.task_language_manager.get_current_language() == 'second'


def test_selection_rejects_mismatched_text_without_changing_state(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path, monkeypatch)
    req = server.LanguageSelectRequest(task_id='coffee', sub_task_id=0, language='wrong')
    with pytest.raises(HTTPException) as error:
        asyncio.run(server.client_language_select(req))
    assert error.value.status_code == 409
    assert runtime.config.language.task_id == 'tea'
    assert runtime.task_language_manager.get_current_language() == 'first'


def test_relative_language_file_load_and_save(tmp_path, monkeypatch):
    monkeypatch.setattr(server, 'ROOT', tmp_path)
    conf_dir = tmp_path / 'conf'
    conf_dir.mkdir()
    (conf_dir / 'language_cmd.json').write_text(json.dumps({'tea': ['old']}))
    loaded = asyncio.run(server.load_lang_file(server.LangFileRequest(path='language_cmd.json')))
    assert loaded['data'] == {'tea': ['old']}
    asyncio.run(server.save_lang_file(server.LangSaveRequest(
        path='language_cmd.json', data={'tea': ['new']}
    )))
    assert json.loads((conf_dir / 'language_cmd.json').read_text()) == {'tea': ['new']}


@pytest.mark.parametrize('history', [False, True])
def test_next_manual_inference_uses_current_language(history):
    sent = []

    class FakeZmq:
        def sendMessage(self, data, meta):
            sent.append(data)
            self.request_id = meta['request_id']
            return True

        def recvMessage(self, timeout_ms):
            return {'meta': {'request_id': self.request_id}, 'data': {}}

    client = VLAClient.__new__(VLAClient)
    client.config = SimpleNamespace(language=SimpleNamespace(auto_mode=False))
    client.task_language_manager = SimpleNamespace(get_current_language=lambda: 'new')
    client.vla_zmq = FakeZmq()
    client._request_id = 0
    client.logger = SimpleNamespace(warning=lambda *args: None)
    frame = {'obs': {'language': ['old']}}
    data = [frame, {'obs': {'language': ['old']}}] if history else frame
    client._request_inference(data, timeout_ms=100)
    frames = sent[0] if history else [sent[0]]
    assert all(item['obs']['language'] == ['new'] for item in frames)

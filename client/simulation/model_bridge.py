"""Policy SDK compatibility without modifying the upstream model adapters."""

import copy
from contextvars import ContextVar
import json
from pathlib import Path
from tempfile import TemporaryDirectory

_REQUEST = ContextVar('model_request', default=None)
_WIRE_CAMERAS = {
    'tao': ('base_image', 'left_wrist_image', 'right_wrist_image'),
    'gr00t_n1': ('video.cam_right_high', 'video.cam_left_wrist', 'video.cam_right_wrist'),
    'gr00t_n1_5': ('video.cam_top_head', 'video.cam_left_wrist', 'video.cam_right_wrist'),
    'gr00t_n1_6': ('cam_top_head', 'cam_left_wrist', 'cam_right_wrist'),
}


class PolicyProxy:
    def __init__(
        self,
        policy,
        *,
        source_cameras,
        target_cameras,
        nested=False,
        language_key=None,
        action_keys=(),
    ):
        self.policy = policy
        self.source_cameras = source_cameras
        self.target_cameras = target_cameras
        self.nested = nested
        self.language_key = language_key
        self.action_keys = list(action_keys)

    def __getattr__(self, name):
        return getattr(self.policy, name)

    def predict_action_chunk(self, observation):
        context = _REQUEST.get()
        if context is not None:
            language = context['language']
            observation = {
                **observation,
                'task': language if isinstance(language, list) else [language],
            }
        return self.policy.predict_action_chunk(observation)

    def get_action(self, observation):
        observation = dict(observation)
        if len(self.source_cameras) != len(self.target_cameras) or len(
            set(self.target_cameras)
        ) != len(self.target_cameras):
            raise ValueError('Model camera roles require an explicit compatible SDK camera mapping')
        camera_data = dict(observation['video']) if self.nested else observation
        values = [camera_data[key] for key in self.source_cameras]
        for key in self.source_cameras:
            camera_data.pop(key)
        camera_data.update(zip(self.target_cameras, values))
        if self.nested:
            observation['video'] = camera_data
        if self.language_key:
            value = observation.pop('annotation.human.task_description')
            observation[self.language_key] = value
        result = self.policy.get_action(observation)
        payload = result[0] if isinstance(result, tuple) else result
        if not isinstance(payload, dict):
            return result
        nested_actions = 'action' in payload and isinstance(payload['action'], dict)
        actions = payload['action'] if nested_actions else payload
        if not self.action_keys:
            return result
        keys = []
        for name in self.action_keys:
            matches = [
                key
                for key in actions
                if key == name or key.removeprefix('action.') == name.removeprefix('action.')
            ]
            if len(matches) != 1:
                raise ValueError(f'Policy output must contain exactly one action field {name!r}')
            keys.append(matches[0])
        ordered = {key: actions[key] for key in keys}
        if nested_actions:
            payload = {**payload, 'action': ordered}
        else:
            payload = {
                **ordered,
                **{key: actions[key] for key in ('prob_progress', 'progress') if key in actions},
            }
        return (payload, *result[1:]) if isinstance(result, tuple) else payload


class SimulationModelBridge:
    def __init__(self, model, model_type, checkpoint_view=None):
        self.model = model
        self.cfg = model.cfg
        self.checkpoint_view = checkpoint_view
        policy = getattr(model, 'policy', None)
        cameras = _WIRE_CAMERAS.get(model_type)
        targets, language, action_keys = cameras, None, []
        if model_type == 'tao' and policy is not None:
            embodiment = getattr(policy, 'embodiment', None)
            targets = tuple(getattr(embodiment, 'observations', {}).get('video', {})) or cameras
            layout = getattr(embodiment, 'indices', {}).get('action', {}).get('sub_components', {})
            action_keys = sorted(layout, key=lambda key: layout[key]['start'])
        elif model_type == 'gr00t_n1_5' and policy is not None:
            from gr00t.experiment.data_config import DATA_CONFIG_MAP

            data_config = DATA_CONFIG_MAP[self.cfg['data_config_key']]
            targets = tuple(data_config.video_keys)
            languages = list(data_config.language_keys)
            if len(languages) != 1:
                raise ValueError('GR00T data configuration must declare one language field')
            language = languages[0]
            action_keys = list(data_config.action_keys)
        if cameras and policy is not None:
            model.policy = PolicyProxy(
                policy,
                source_cameras=cameras,
                target_cameras=targets,
                nested=model_type in ('tao', 'gr00t_n1_6'),
                language_key=language,
                action_keys=action_keys,
            )
        elif model_type == 'smolvla' and policy is not None:
            model.policy = PolicyProxy(policy, source_cameras=(), target_cameras=())

    def __getattr__(self, name):
        return getattr(self.model, name)

    def infer(self, sequence):
        token = _REQUEST.set({'language': sequence[0]['obs']['language']})
        try:
            return self.model.infer(sequence)
        finally:
            _REQUEST.reset(token)


def _checkpoint_view(config):
    """Alias metadata in a temporary view; original checkpoint files stay untouched."""
    root = Path(config.model_path).expanduser().resolve()
    metadata_path = root / 'experiment_cfg/metadata.json'
    metadata = json.loads(metadata_path.read_text())
    key = config.data_config_key
    if key in metadata:
        return None
    candidate = config.get('embodiment_tag')
    if candidate not in metadata:
        if len(metadata) != 1:
            raise ValueError(f'No unambiguous checkpoint metadata for {key!r}')
        candidate = next(iter(metadata))
    temporary = TemporaryDirectory(prefix='open-rail-checkpoint-')
    try:
        view = Path(temporary.name)
        for path in root.iterdir():
            if path.name != 'experiment_cfg':
                (view / path.name).symlink_to(path)
        (view / 'experiment_cfg').mkdir()
        for path in metadata_path.parent.iterdir():
            if path.name != 'metadata.json':
                (view / 'experiment_cfg' / path.name).symlink_to(path)
        metadata[key] = metadata[candidate]
        (view / 'experiment_cfg/metadata.json').write_text(json.dumps(metadata))
        return temporary
    except BaseException:
        temporary.cleanup()
        raise


def build_model(config, factory):
    model_type = str(getattr(config.type, 'value', config.type))
    view = None
    prepared = config
    if model_type == 'gr00t_n1_5':
        view = _checkpoint_view(config.gr00t)
        if view:
            prepared = copy.deepcopy(config)
            prepared.gr00t.model_path = view.name
    try:
        model = factory(prepared)
        if not hasattr(model, 'cfg'):
            group = (
                'gr00t' if model_type in ('gr00t_n1', 'gr00t_n1_5', 'gr00t_n1_6') else model_type
            )
            model.cfg = config[group]
        if view:
            model.cfg = config.gr00t
        return SimulationModelBridge(model, model_type, view)
    except BaseException:
        if view:
            view.cleanup()
        raise

"""Configure model layouts and adapt vectors at the simulation boundary."""

from pathlib import Path

import numpy as np
import yaml


def field_name(name, width):
    name = name.removeprefix('action.').removeprefix('state.')
    if width == 1 and name in ('left_hand', 'right_hand'):
        return name.replace('_hand', '_gripper')
    return name


def fields_from_layout(layout):
    fields = []
    end = 0
    for name, segment in sorted(layout.items(), key=lambda item: item[1]['start']):
        start, stop = int(segment['start']), int(segment['end'])
        if start != end or stop <= start:
            raise ValueError(f'Non-contiguous vector layout at {name}: {start}:{stop}')
        fields.append({'name': field_name(name, stop - start), 'width': stop - start})
        end = stop
    return fields


def validate_fields(fields):
    names = set()
    for field in fields:
        name, width = field['name'], field['width']
        if not isinstance(name, str) or not name or name in names:
            raise ValueError(f'Invalid or duplicate vector field: {name}')
        if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
            raise ValueError(f'Invalid width for {name}: {width}')
        names.add(name)
    return fields


def vector_width(fields):
    return sum(field['width'] for field in validate_fields(fields))


def validate_layout(schema):
    for key in ('state', 'action'):
        validate_fields(schema.get(key, []))
    history = schema.get('history_frames', 1)
    if isinstance(history, bool) or not isinstance(history, int) or history < 1:
        raise ValueError('history_frames must be a positive integer')
    interval = schema.get('action_dt')
    if interval is not None and (not np.isfinite(interval) or interval <= 0):
        raise ValueError('action_dt must be positive finite seconds')
    return schema


def resolve_profile_path(path):
    filename, separator, name = str(path).partition('#')
    if not filename or (separator and not name):
        raise ValueError('Expected a YAML path or YAML path#profile name')
    return f'{Path(filename).expanduser().resolve()}{separator}{name}'


def load_profile(path):
    if not path:
        return {}
    filename, separator, name = resolve_profile_path(path).partition('#')
    profile = yaml.safe_load(Path(filename).read_text())
    if not isinstance(profile, dict):
        raise ValueError('Simulation IO profile must be a YAML mapping')
    if separator:
        profiles = profile.get('io_profiles', {})
        if not isinstance(profiles, dict) or name not in profiles:
            raise ValueError(f'Unknown simulation IO profile {name!r} in {filename}')
        profile = profiles[name]
        if not isinstance(profile, dict):
            raise ValueError(f'Simulation IO profile {name!r} must be a YAML mapping')
    elif 'io_profiles' in profile:
        raise ValueError('Select a simulation IO profile using YAML path#profile name')
    validate_layout(profile)
    return profile


def map_vector(values, source, target, mapping=None):
    """Reorder named fields and apply explicit affine unit/range conversions."""
    source, target = validate_fields(source), validate_fields(target)
    values = np.asarray(values)
    if values.ndim < 1 or values.shape[-1] != vector_width(source):
        raise ValueError(f'Vector shape {values.shape} does not match source schema')
    if not np.isfinite(values).all():
        raise ValueError('Policy vectors must contain only finite values')
    slices = {}
    offset = 0
    for field in source:
        slices[field['name']] = (field, slice(offset, offset + field['width']))
        offset += field['width']
    result = []
    for field in target:
        conversion = (mapping or {}).get(field['name'], {})
        name = conversion.get('source', field['name'])
        if name not in slices:
            raise ValueError(f'Missing vector field {name!r}; available: {list(slices)}')
        original, selection = slices[name]
        if original['width'] != field['width']:
            raise ValueError(
                f'Incompatible width for {name}: {original["width"]} != {field["width"]}'
            )
        for attribute in ('kind', 'frame', 'rotation'):
            if original.get(attribute) != field.get(attribute):
                raise ValueError(f'Explicit semantic conversion required for {name}.{attribute}')
        if original.get('unit') != field.get('unit') and 'scale' not in conversion:
            raise ValueError(f'Explicit unit conversion required for {name}')
        part = values[..., selection]
        shape = part.shape
        part = part * np.asarray(conversion.get('scale', 1)) + np.asarray(
            conversion.get('offset', 0)
        )
        if part.shape != shape or not np.isfinite(part).all():
            raise ValueError(f'Invalid affine conversion for {name}')
        result.append(part)
    if not result:
        raise ValueError('Target vector schema is empty')
    return np.concatenate(result, axis=-1)


CONVERTERS = {}


def register_io_converter(name, converter):
    if name in CONVERTERS:
        raise ValueError(f'IO converter already registered: {name}')
    CONVERTERS[name] = converter


class SimulationIOAdapter:
    def __init__(self, robot, transport, profile_path=''):
        self.robot = robot
        self.transport = transport
        profile_path = profile_path or getattr(robot, 'config', {}).get('io_profile', '')
        self.profile = load_profile(profile_path)
        self.environment = robot.describe_io() if hasattr(robot, 'describe_io') else {}
        self.environment.update(self.profile.get('environment', {}))
        if self.environment:
            validate_layout(self.environment)
        model_type = str(getattr(transport, 'heartbeat_info', {}).get('model_type', ''))
        model_type = model_type.rsplit('.', 1)[-1].lower()
        self.model = {}
        if model_type == 'rdt':
            self.model['history_frames'] = 2
        self.model.update(self.profile)
        validate_layout(self.model)
        self.history_frames = self.model.get('history_frames')
        converter = self.profile.get('converter')
        if converter and converter not in CONVERTERS:
            raise ValueError(f'Unknown IO converter: {converter}')
        self.converter = CONVERTERS.get(converter)
        self._check_layout()

    def _check_layout(self):
        if self.converter:
            return
        for direction, source, target in (
            ('state', self.environment.get('state'), self.model.get('state')),
            ('action', self.model.get('action'), self.environment.get('action')),
        ):
            if source and target:
                map_vector(
                    np.zeros(vector_width(source)),
                    source,
                    target,
                    self.profile.get(f'{direction}_mapping'),
                )

    def prepare(self, data):
        frames = data if isinstance(data, list) else [data]
        if self.history_frames and len(frames) != self.history_frames:
            raise ValueError(
                f'Policy requires {self.history_frames} observation frames, got {len(frames)}'
            )
        context = {
            'state': np.array(frames[0]['obs']['state'], copy=True),
            'environment': self.environment,
            'model': self.model,
        }
        prepared = []
        for frame in frames:
            item = {**frame, 'obs': dict(frame['obs']), 'meta': dict(frame.get('meta', {}))}
            state = np.asarray(item['obs']['state'])
            if state.ndim != 1 or not np.isfinite(state).all():
                raise ValueError(f'Invalid environment state vector: {state.shape}')
            if self.environment.get('state') and state.size != vector_width(
                self.environment['state']
            ):
                raise ValueError('State width does not match benchmark schema')
            item['obs']['state'] = np.array(state, copy=True)
            if self.converter:
                item['obs'] = self.converter.encode(item['obs'], context)
            elif self.model.get('state'):
                if not self.environment.get('state'):
                    raise ValueError('Benchmark must declare its state layout for this policy')
                item['obs']['state'] = map_vector(
                    item['obs']['state'],
                    self.environment['state'],
                    self.model['state'],
                    self.profile.get('state_mapping'),
                )
            cameras = self.profile.get('camera_mapping', {})
            original = dict(item['obs'])
            for target, source in cameras.items():
                item['obs'][f'cam.{target}'] = original[f'cam.{source}']
            prepared.append(item)
        return (prepared if isinstance(data, list) else prepared[0]), context

    def decode(self, message, context):
        result = message.get('data', {})
        if result.get('type') == 'vla_error':
            raise RuntimeError(f'Model inference failed: {result.get("error")}')
        if result.get('type') == 'vla_status' and result.get('status') == 'not_ready':
            return None
        if result.get('type') != 'vla_action':
            raise RuntimeError(f'Unexpected model response: {result.get("type")}')
        source = self.model.get('action')
        actions = np.asarray(result['pred_action'])
        if actions.ndim != 2 or not len(actions) or not np.isfinite(actions).all():
            raise ValueError(f'Invalid policy action matrix: {actions.shape}')
        if self.converter:
            actions = self.converter.decode(actions, context)
        elif source:
            actions = map_vector(
                actions, source, self.environment['action'], self.profile.get('action_mapping')
            )
        actions = np.asarray(actions)
        if actions.ndim != 2 or not len(actions) or not np.isfinite(actions).all():
            raise ValueError('IO converter returned an invalid action matrix')
        if self.environment.get('action') and actions.shape[1] != vector_width(
            self.environment['action']
        ):
            raise ValueError(
                'Policy action width does not match benchmark; supply an IO profile or converter'
            )
        return {**message, 'data': {**result, 'pred_action': actions}}

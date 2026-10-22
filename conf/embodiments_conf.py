"""Resolve shared simulation names to model-specific deployment settings."""

from dataclasses import dataclass
from pathlib import Path

import yaml

SIMULATION_CONFIG = Path(__file__).resolve().parent / 'simulation.yml'
GR00T_DATA_CONFIG_BY_EMBODIMENT = {
    'a2d': 'a2d_arms_only',
    'robocasa_panda_omron': 'panda_omron',
}


@dataclass(frozen=True)
class SimulationEmbodiment:
    name: str
    platform: str
    io_profile: str
    models: dict


def simulation_embodiment(tag):
    settings = yaml.safe_load(SIMULATION_CONFIG.read_text()) or {}
    matches = [
        (name, value)
        for name, value in settings.get('embodiments', {}).items()
        if tag == name or tag in value.get('aliases', [])
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError(f'Ambiguous simulation embodiment: {tag!r}')
    name, value = matches[0]
    profile = value['io_profile']
    if profile not in settings.get('io_profiles', {}):
        raise ValueError(f'Missing IO profile {profile!r} for {name}')
    return SimulationEmbodiment(
        name, value['platform'], f'{SIMULATION_CONFIG}#{profile}', value.get('models', {}),
    )


def select_model_embodiment(models, tag):
    model_type = str(getattr(models.type, 'value', models.type))
    group = 'gr00t' if model_type in ('gr00t_n1', 'gr00t_n1_5', 'gr00t_n1_6') else model_type
    config = models[group]
    embodiment = simulation_embodiment(tag)
    if embodiment is not None:
        if model_type not in embodiment.models:
            raise ValueError(
                f'{model_type} has no simulation adaptation for {embodiment.name}; '
                'register a compatible adapter and model settings in conf/simulation.yml'
            )
        overrides = embodiment.models[model_type]
        if not isinstance(overrides, dict) or 'model_path' in overrides:
            raise ValueError(f'Invalid model settings for {model_type}/{embodiment.name}')
        for key, value in overrides.items():
            config[key] = value
        config.simulation_embodiment = embodiment.name
        config.simulation_io_profile = embodiment.io_profile
    elif model_type == 'gr00t_n1_5':
        config.embodiment_tag = tag
        mapping = config.get('data_config_by_embodiment', GR00T_DATA_CONFIG_BY_EMBODIMENT)
        config.data_config_key = mapping.get(tag, tag)
    elif model_type in ('tao', 'gr00t_n1_7_eef'):
        config.embodiment_tag = tag
    else:
        raise ValueError(f'Unknown or unsupported simulation embodiment {tag!r} for {model_type}')


def select_evaluation_embodiment(config, tag, platform=None):
    embodiment = simulation_embodiment(tag)
    if embodiment is None:
        raise ValueError(f'Unknown simulation embodiment: {tag!r}')
    if platform is not None and embodiment.platform != platform:
        raise ValueError(f'{embodiment.name} requires {embodiment.platform}, not {platform}')
    config.vla_zmq.embodiment_tag = embodiment.name
    config.vla_zmq.io_profile = embodiment.io_profile
    return embodiment

"""Cached task discovery through the simulation benchmark registry."""

from functools import lru_cache
import json

from client.simulation.benchmarks import get_benchmark


@lru_cache(maxsize=8)
def task_catalog(platform, python, robotwin_root, project_root, options_json='{}'):
    settings = {'robotwin_root': robotwin_root, **json.loads(options_json)}
    return get_benchmark(platform).catalog(python, settings, project_root)

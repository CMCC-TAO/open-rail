import sys
from pathlib import Path
from threading import Lock


class ModelVLA:
    """Wall-X A2D policy using the shared open-rail server."""

    def __init__(self, config):
        self.cfg = config
        repo_path = str(Path(config['repo_path']).expanduser().resolve())
        if repo_path not in sys.path:
            sys.path.insert(0, repo_path)
        from wall_x.serving.a2d import A2DPolicy

        self.policy = A2DPolicy(
            config['model_path'], device=config.get('device', 'cuda:0'),
            flow_steps=int(config.get('flow_steps', 10)),
        )
        self._lock = Lock()

    def infer(self, sequence, verbose=False):
        with self._lock:
            return self.policy.infer(sequence)

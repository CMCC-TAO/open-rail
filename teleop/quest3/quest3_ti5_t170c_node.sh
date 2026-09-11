#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

python3 -m teleop.quest3.quest3 \
  --config teleop/quest3/config/ti5_t170c.yaml \
  "$@"

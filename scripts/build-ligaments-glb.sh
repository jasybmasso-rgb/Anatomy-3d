#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build_skeleton_glb.py
python3 scripts/build_ligaments_glb.py

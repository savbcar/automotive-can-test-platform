#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

./scripts/setup_vcan.sh vcan0
python -m automotive_can socketcan-demo --channel vcan0 --cycles 20 --period-ms 100

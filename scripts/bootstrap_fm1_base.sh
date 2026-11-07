#!/usr/bin/env bash
# Bootstrap an fm1-base build checkout for GrooveScape.
# Does not flash hardware or modify firmware on a device.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="${FM1_BASE_DIR:-$ROOT/.work/fm1-base}"
if [ ! -f "$BASE/tools/build.py" ]; then
  mkdir -p "$(dirname "$BASE")"
  git clone --recursive https://github.com/charlesvestal/fm1-base.git "$BASE"
else
  git -C "$BASE" submodule update --init --recursive
fi
printf 'Upstream platform: %s\n' "$(git -C "$BASE" rev-parse HEAD)"
echo 'Build baseline host simulator (no hardware flash):'
"$BASE/tools/build.py" "$BASE/template" --host
echo 'Build baseline browser emulator:'
"$BASE/tools/build.py" "$BASE/template" --web
echo 'GrooveScape DSP is NOT wired into this baseline template yet.'

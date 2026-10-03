#!/bin/zsh
# =============================================================================
# Build the CrisperWhisper wheelhouse on the CONTROL node (the M4) for the
# transcription_worker role.
#
# Why: the M2 worker never clones from GitHub and holds no keys, but CrisperWhisper
# needs the nyrahealth/transformers fork (4.37.2), which only exists as a git URL.
# This builds every pinned package — the fork included — as a local wheel, and
# writes an offline requirements file the M2 installs with `--no-index`.
#
# Source of the pins: the venv FliTools actually runs CrisperWhisper with on the M4.
#
# Usage:
#   scripts/build-crisper-wheelhouse.sh [source-venv] [out-dir]
#   defaults: ~/.venvs/align-spike   ~/.cache/appydave/crisper-wheelhouse
# Re-run whenever the M4's CrisperWhisper venv changes.
# =============================================================================
set -euo pipefail
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"

SRC_VENV="${1:-$HOME/.venvs/align-spike}"
OUT="${2:-$HOME/.cache/appydave/crisper-wheelhouse}"

[[ -x "$SRC_VENV/bin/python" ]] || { echo "no venv at $SRC_VENV" >&2; exit 1; }
mkdir -p "$OUT"

# ctc-forced-aligner belongs to the alignment spike, not to CrisperWhisper — leave it behind.
uv pip freeze --python "$SRC_VENV/bin/python" \
  | grep -v '^ctc-forced-aligner' > "$OUT/requirements.lock"

# --no-deps: the freeze is already the full, exact set.
uvx --python 3.11 pip wheel --no-deps -r "$OUT/requirements.lock" -w "$OUT"

# The M2 installs offline: replace git URLs with the version of the wheel just built.
sed -E 's|^transformers @ git\+.*$|transformers==4.37.2|' "$OUT/requirements.lock" > "$OUT/requirements-offline.txt"
if grep -q 'git+' "$OUT/requirements-offline.txt"; then
  echo "requirements-offline.txt still has a git URL — add a rewrite for it above" >&2
  exit 1
fi

echo "wheelhouse: $OUT ($(ls "$OUT"/*.whl | wc -l | tr -d ' ') wheels, $(du -sh "$OUT" | cut -f1))"

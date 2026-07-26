#!/usr/bin/env bash
set -euo pipefail

RUNTIME_DIR="${RUNTIME_DIR:-/Users/shike/.codex/runtimes/video-skills-py311}"
PYTHON_BIN="${PYTHON_BIN:-/Users/shike/.local/bin/python3.11}"

if [[ "${1:-}" != "--install" ]]; then
  echo "Refusing to install. Re-run with --install after the user explicitly approves installation."
  exit 2
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python 3.11 not found at: $PYTHON_BIN"
  echo "Install or provide Python 3.11, then set PYTHON_BIN to its absolute path."
  exit 1
fi

if [[ ! -x "$RUNTIME_DIR/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$RUNTIME_DIR"
fi

"$RUNTIME_DIR/bin/python" -m pip install --upgrade pip
"$RUNTIME_DIR/bin/python" -m pip install "faster-whisper==1.2.1" "manim" "PyYAML"
"$RUNTIME_DIR/bin/python" -m pip freeze > "$RUNTIME_DIR/requirements.lock.txt"

echo "Runtime ready: $RUNTIME_DIR"
echo "Model files are downloaded only when a transcription job is run."

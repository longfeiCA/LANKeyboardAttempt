#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_SCRIPT="$SCRIPT_DIR/src/server/server.py"

if [ ! -f "$SERVER_SCRIPT" ]; then
    echo "Error: server.py not found at $SERVER_SCRIPT"
    exit 1
fi

if ! command -v xdotool &>/dev/null; then
    echo "Error: xdotool is not installed. Please install it first:"
    echo "  sudo apt install xdotool   # Debian/Ubuntu"
    echo "  sudo dnf install xdotool   # Fedora"
    exit 1
fi

if ! python3 -c "import flask" &>/dev/null; then
    echo "Installing Python dependencies..."
    pip install flask
fi

echo "Starting Remote Keyboard server..."
python3 "$SERVER_SCRIPT"

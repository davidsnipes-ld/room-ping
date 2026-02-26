#!/usr/bin/env bash
# Build RoomPing Pro for Linux. Run this on a Linux machine.
# Output: dist/RoomPingPro (and optionally dist/RoomPingPro-Linux.zip)

set -e
cd "$(dirname "$0")"
echo "Installing dependencies..."
pip3 install -q pyinstaller -r requirements.txt "pywebview[qt]"
echo "Building..."
pyinstaller --noconfirm RoomPingPro.spec
chmod +x dist/RoomPingPro
echo "Done. Run with: ./dist/RoomPingPro"
echo "Optional: create zip with: cd dist && zip RoomPingPro-Linux.zip RoomPingPro && mv RoomPingPro-Linux.zip .. && cd .."

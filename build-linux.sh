#!/usr/bin/env bash
# For maintainers: builds the self-contained Linux binary.
# End users should download RoomPingPro-Linux.zip from the repo Releases page, unzip, and double-click RoomPingPro (no terminal needed).
# Run this on a Linux machine. Output: dist/RoomPingPro

set -e
cd "$(dirname "$0")"
echo "Installing dependencies..."
pip3 install -q pyinstaller -r requirements.txt "pywebview[qt]"
echo "Building..."
pyinstaller --noconfirm RoomPingPro.spec
chmod +x dist/RoomPingPro
echo "Done. Output: dist/RoomPingPro (single executable)."
echo "To distribute: zip it and upload to Releases; users unzip and double-click (no terminal required)."

#!/usr/bin/env bash
# For maintainers: builds the self-contained macOS .app bundle.
# End users should download RoomPingPro-macOS.zip from the repo Releases page, unzip, and double-click RoomPingPro.app.
set -e
cd "$(dirname "$0")"
echo "Building RoomPing Pro for macOS..."
echo "Installing dependencies..."
pip3 install -q pyinstaller -r requirements.txt
echo "Building..."
pyinstaller --noconfirm RoomPingPro.spec
echo "Done. Output: dist/RoomPingPro.app"
echo "To distribute: zip the .app and upload to Releases; users unzip and double-click."

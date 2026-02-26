#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "RoomPing Pro – checking dependencies..."
pip3 install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt
echo "Starting..."
python3 main.py 2>/dev/null || python main.py

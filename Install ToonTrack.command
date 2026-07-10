#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "Building ToonTrack.app…"
source .venv/bin/activate
python3 build_icon.py
rm -rf build dist
python3 setup.py py2app

echo "Quitting any running ToonTrack…"
osascript -e 'quit app "ToonTrack"' 2>/dev/null || true
sleep 1

echo "Installing to /Applications/ToonTrack.app…"
rm -rf /Applications/ToonTrack.app
cp -R dist/ToonTrack.app /Applications/ToonTrack.app

echo "Done. Launching ToonTrack v1.2.1…"
open /Applications/ToonTrack.app

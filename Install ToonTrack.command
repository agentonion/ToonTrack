#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

clean_dir() {
  local dir="$1"
  [[ -e "$dir" ]] || return 0
  chmod -R u+w "$dir" 2>/dev/null || true
  if [[ -d "$dir" ]]; then
    find "$dir" -mindepth 1 -delete 2>/dev/null || true
  fi
  rm -rf "$dir" 2>/dev/null || true
  if [[ -e "$dir" ]]; then
    echo "Could not remove $dir. Close Finder windows showing it, quit ToonTrack, then retry." >&2
    exit 1
  fi
}

echo "Quitting any running ToonTrack…"
osascript -e 'quit app "ToonTrack"' 2>/dev/null || true
sleep 1

echo "Building ToonTrack.app…"
source .venv/bin/activate
python3 build_icon.py
clean_dir build
clean_dir dist
python3 setup.py py2app

echo "Installing to /Applications/ToonTrack.app…"
clean_dir /Applications/ToonTrack.app
cp -R dist/ToonTrack.app /Applications/ToonTrack.app

echo "Done. Launching ToonTrack v1.2.1…"
open /Applications/ToonTrack.app

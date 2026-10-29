#!/bin/bash
set -euo pipefail

repo_dir=$(cd "$(dirname "$0")" && pwd)
timestamp=$(date '+%Y%m%d-%H%M%S')

resolve_bin() {
  local override=$1
  local command_name=$2
  shift 2
  if [[ -n "$override" && -x "$override" ]]; then
    printf '%s\n' "$override"
    return
  fi
  if command -v "$command_name" >/dev/null 2>&1; then
    command -v "$command_name"
    return
  fi
  local candidate
  for candidate in "$@"; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return
    fi
  done
  printf 'Missing required command: %s\n' "$command_name" >&2
  exit 1
}

aerospace_bin=$(resolve_bin "${AEROSPACE_BIN:-}" aerospace /opt/homebrew/bin/aerospace /usr/local/bin/aerospace)
sketchybar_bin=$(resolve_bin "${SKETCHYBAR_BIN:-}" sketchybar /opt/homebrew/bin/sketchybar /usr/local/bin/sketchybar "$HOME/.config/sketchybar/bin/sketchybar")
borders_bin=$(resolve_bin "${BORDERS_BIN:-}" borders /opt/homebrew/bin/borders /usr/local/bin/borders)
python_bin=${PYTHON_BIN:-/usr/bin/python3}
if [[ ! -x "$python_bin" ]]; then
  printf 'Missing required Python executable: %s\n' "$python_bin" >&2
  exit 1
fi

backup_file() {
  local path=$1
  if [[ -e "$path" ]]; then
    cp -p "$path" "$path.backup-$timestamp"
  fi
}

render() {
  local source=$1
  local destination=$2
  sed \
    -e "s|__HOME__|$HOME|g" \
    -e "s|__AEROSPACE_BIN__|$aerospace_bin|g" \
    -e "s|__SKETCHYBAR_BIN__|$sketchybar_bin|g" \
    -e "s|__BORDERS_BIN__|$borders_bin|g" \
    -e "s|__PYTHON_BIN__|$python_bin|g" \
    "$source" > "$destination"
}

mkdir -p "$HOME/.config/sketchybar" "$HOME/.config/aerospace-pairs" "$HOME/Library/LaunchAgents"

backup_file "$HOME/.aerospace.toml"
backup_file "$HOME/.config/sketchybar/sketchybarrc"
backup_file "$HOME/.config/sketchybar/update-desktop.sh"
backup_file "$HOME/.config/aerospace-pairs/pairs.py"
backup_file "$HOME/.config/aerospace-pairs/displays.json"
backup_file "$HOME/Library/LaunchAgents/local.sketchybar.desktop-indicator.plist"

render "$repo_dir/templates/aerospace.toml" "$HOME/.aerospace.toml"
render "$repo_dir/templates/sketchybarrc" "$HOME/.config/sketchybar/sketchybarrc"
render "$repo_dir/templates/update-desktop.sh" "$HOME/.config/sketchybar/update-desktop.sh"
render "$repo_dir/templates/pairs.py" "$HOME/.config/aerospace-pairs/pairs.py"
render "$repo_dir/templates/local.sketchybar.desktop-indicator.plist" "$HOME/Library/LaunchAgents/local.sketchybar.desktop-indicator.plist"

chmod 755 "$HOME/.config/sketchybar/sketchybarrc" "$HOME/.config/sketchybar/update-desktop.sh" "$HOME/.config/aerospace-pairs/pairs.py"
chmod 644 "$HOME/.aerospace.toml" "$HOME/Library/LaunchAgents/local.sketchybar.desktop-indicator.plist"

if pgrep -x AeroSpace >/dev/null 2>&1; then
  "$aerospace_bin" reload-config
fi

launchctl bootout "gui/$UID/local.sketchybar.desktop-indicator" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$HOME/Library/LaunchAgents/local.sketchybar.desktop-indicator.plist"
launchctl kickstart -k "gui/$UID/local.sketchybar.desktop-indicator"

printf 'Installed AeroSpace setup for %s.\n' "$USER"
printf 'Display topology is detected automatically.\n'
if [[ "$(defaults read com.apple.spaces spans-displays 2>/dev/null || true)" != "1" ]]; then
  printf '%s\n' \
    'Stability note: disable “Displays have separate Spaces” in System Settings → Desktop & Dock → Mission Control, then log out and back in.'
fi

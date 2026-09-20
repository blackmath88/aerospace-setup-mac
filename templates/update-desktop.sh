#!/bin/bash
workspace=$('__AEROSPACE_BIN__' list-workspaces --focused 2>/dev/null) || exit 0
case "$workspace" in
  1|6) active=1;; 2|7) active=2;; 3|8) active=3;; 4|9) active=4;; *) active=0;;
esac

args=()
for n in 1 2 3 4; do
  case "$n" in
    1) active_color=0xff8aadf4; inactive_color=0x663b4c6b; border_inactive=0xff8aadf4;;
    2) active_color=0xffc6a0f6; inactive_color=0x6654456b; border_inactive=0xffc6a0f6;;
    3) active_color=0xffa6da95; inactive_color=0x66495f45; border_inactive=0xffa6da95;;
    4) active_color=0xffeed49f; inactive_color=0x66645943; border_inactive=0xffeed49f;;
  esac
  if [[ "$n" == "$active" ]]; then
    args+=(--set "desktop.$n" background.color="$active_color" label.color=0xff18201a)
    border_active=$active_color
    border_dim=$border_inactive
  else
    args+=(--set "desktop.$n" background.color="$inactive_color" label.color=0xffc4c9d4)
  fi
done

if [[ "$active" == 0 ]]; then
  exit 0
fi

'__SKETCHYBAR_BIN__' \
  --bar color=0x00000000 border_color=0x00000000 border_width=0 blur_radius=0 \
  --set desktop.line.left background.color="$border_active" \
  --set desktop.line.right background.color="$border_active" \
  "${args[@]}"

border_state=/tmp/aerospace-border-theme-$USER
if [[ "$(cat "$border_state" 2>/dev/null)" != "$active" ]]; then
  '__BORDERS_BIN__' \
    style=round \
    width=6.0 \
    hidpi=on \
    active_color="$border_active" \
    inactive_color="$border_dim" \
    >/dev/null 2>&1 &
  printf '%s\n' "$active" > "$border_state"
fi

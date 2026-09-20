#!/usr/bin/python3
"""Switch synchronized AeroSpace workspace pairs across one or two displays."""
import json
import subprocess
import sys
from pathlib import Path

CLI = '__AEROSPACE_BIN__'
SKETCHYBAR = '__SKETCHYBAR_BIN__'
EXTERNAL_MONITOR = '__EXTERNAL_MONITOR__'
STATE = Path('__HOME__/.config/aerospace-pairs/history.json')


def run(*args):
    return subprocess.check_output([CLI, *args], text=True).strip()


def pair(workspace):
    if not workspace.isdigit():
        return 1
    number = int(workspace)
    return min(4, number - 5 if number >= 6 else number)


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: pairs.py next|prev|back|1|2|3|4|move N|send N')

    action = sys.argv[1]
    monitors = json.loads(run('list-monitors', '--json'))
    focused = json.loads(run('list-monitors', '--focused', '--json'))[0]
    current = pair(run('list-workspaces', '--focused'))
    try:
        history = json.loads(STATE.read_text())
    except (OSError, ValueError):
        history = {}

    if action == 'next':
        target = current % 4 + 1
    elif action == 'prev':
        target = (current - 2) % 4 + 1
    elif action == 'back':
        target = history.get('previous', current)
    else:
        target = pair(sys.argv[2] if action in ('move', 'send') else action)

    builtin = next((m for m in monitors if 'built-in' in m['monitor-name'].lower()), None)
    external = next((m for m in monitors if EXTERNAL_MONITOR and m['monitor-name'] == EXTERNAL_MONITOR), None)
    dual = builtin is not None and external is not None
    destination = target + 5 if dual and focused['monitor-id'] == builtin['monitor-id'] else target

    if action in ('move', 'send'):
        run('move-node-to-workspace', str(destination))
        if action == 'send':
            return

    if dual:
        if focused['monitor-id'] == builtin['monitor-id']:
            run('workspace', str(target))
            run('workspace', str(target + 5))
        else:
            run('workspace', str(target + 5))
            run('workspace', str(target))
    else:
        run('workspace', str(target))

    subprocess.run([SKETCHYBAR, '--trigger', 'desktop_pair_changed'], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if current != target:
        STATE.write_text(json.dumps({'previous': current}))


if __name__ == '__main__':
    main()

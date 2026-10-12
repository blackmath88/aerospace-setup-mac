#!/usr/bin/python3
"""Switch synchronized AeroSpace workspace groups across any display topology."""
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

CLI = '__AEROSPACE_BIN__'
SKETCHYBAR = '__SKETCHYBAR_BIN__'
STATE = Path('__HOME__/.config/aerospace-pairs/history.json')
LOCK = STATE.with_suffix('.lock')
DISPLAY_CACHE = STATE.with_name('displays.json')
GROUPS = range(1, 5)
WORKSPACE_STRIDE = 5


def run(*args):
    result = subprocess.run(
        [CLI, *args], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.strip()


def workspace_group(workspace):
    if not workspace.isdigit():
        return None
    group = (int(workspace) - 1) % WORKSPACE_STRIDE + 1
    return group if group in GROUPS else None


def workspace_for(group, slot):
    return group + WORKSPACE_STRIDE * slot


def load_state():
    try:
        data = json.loads(STATE.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, sort_keys=True))
    os.replace(temporary, STATE)


def read_display_cache(signature):
    try:
        cache = json.loads(DISPLAY_CACHE.read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(cache, dict):
        return None
    if cache.get('signature') != signature:
        return None
    return {
        int(screen_id): tuple(size)
        for screen_id, size in cache.get('geometries', {}).items()
    }


def query_display_geometries():
    """Return NSScreen sizes keyed by their one-based AppKit array index."""
    script = r'''
ObjC.import('AppKit');
var lines = [];
$.NSScreen.screens.js.forEach(function(screen, index) {
    var frame = screen.frame;
    lines.push((index + 1) + '|' + frame.size.width + '|' + frame.size.height);
});
lines.join('\n');
'''
    result = subprocess.run(
        ['/usr/bin/osascript', '-l', 'JavaScript', '-e', script],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    geometries = {}
    for line in result.stdout.splitlines():
        screen_id, width, height = line.split('|', 2)
        geometries[int(screen_id)] = (int(float(width)), int(float(height)))
    return geometries


def display_geometries(signature):
    refresh = os.environ.get('SENDER') == 'display_change'
    geometries = None if refresh else read_display_cache(signature)
    if geometries is None:
        try:
            geometries = query_display_geometries()
        except (OSError, subprocess.CalledProcessError, ValueError):
            geometries = {}
        if geometries:
            temporary = DISPLAY_CACHE.with_suffix('.tmp')
            temporary.write_text(json.dumps({
                'signature': signature,
                'geometries': geometries,
            }, sort_keys=True))
            os.replace(temporary, DISPLAY_CACHE)
    return geometries


def list_monitors():
    output = run(
        'list-monitors', '--format',
        '%{monitor-id}%{tab}%{monitor-appkit-nsscreen-screens-id}'
        '%{tab}%{monitor-name}%{tab}%{monitor-is-main}',
    )
    rows = []
    for line in output.splitlines():
        monitor_id, screen_id, name, is_main = line.split('\t', 3)
        rows.append((monitor_id, screen_id, name, is_main))
    signature = [f'{screen_id}:{name}' for _, screen_id, name, _ in rows]
    geometries = display_geometries(signature)
    monitors = []
    for monitor_id, screen_id, name, is_main in rows:
        width, height = geometries.get(int(screen_id), (0, 0))
        monitors.append({
            'monitor-id': int(monitor_id),
            'screen-id': int(screen_id),
            'monitor-name': name,
            'is-main': is_main == 'true',
            'width': width,
            'height': height,
        })
    return ordered_monitors(monitors)


def monitor_role(monitor):
    name = monitor['monitor-name'].lower()
    if 'built-in' in name:
        return 'built-in'
    if monitor['height'] > monitor['width']:
        return 'portrait'
    return 'landscape'


def ordered_monitors(monitors):
    """Use stable screen roles instead of temporary AeroSpace monitor ids."""
    role_order = {'landscape': 0, 'portrait': 1, 'built-in': 2}
    return sorted(
        monitors,
        key=lambda monitor: (
            role_order[monitor_role(monitor)],
            monitor['monitor-name'].lower(),
            monitor['screen-id'],
        ),
    )


def monitor_topology(monitors):
    return [
        '{}:{}x{}:{}'.format(
            monitor['monitor-name'], monitor['width'], monitor['height'],
            monitor_role(monitor),
        )
        for monitor in monitors
    ]


def windows_on(workspace):
    output = run(
        'list-windows', '--workspace', str(workspace),
        '--format', '%{window-id}',
    )
    return output.splitlines() if output else []


def adopt_separator_windows(group, monitors):
    """Move windows from AeroSpace's unmanaged 5/10/... slots into a group."""
    for slot, monitor in enumerate(monitors):
        visible = run(
            'list-workspaces', '--monitor', str(monitor['monitor-id']),
            '--visible', '--format', '%{workspace}',
        )
        if not visible.isdigit() or int(visible) % WORKSPACE_STRIDE != 0:
            continue
        destination = workspace_for(group, slot)
        for window_id in windows_on(visible):
            run(
                'move-node-to-workspace', '--window-id', window_id,
                str(destination),
            )


def collapse_removed_slots(state, old_count, new_count):
    if new_count < 1:
        return
    collapsed = state.setdefault('collapsed', {})
    for slot in range(new_count, old_count):
        destination_slot = slot % new_count
        for group in GROUPS:
            source = workspace_for(group, slot)
            destination = workspace_for(group, destination_slot)
            for window_id in windows_on(source):
                run(
                    'move-node-to-workspace', '--window-id', window_id,
                    str(destination),
                )
                collapsed[window_id] = {'group': group, 'slot': slot}


def restore_added_slots(state, new_count):
    collapsed = state.setdefault('collapsed', {})
    for window_id, home in list(collapsed.items()):
        if home['slot'] >= new_count:
            continue
        try:
            run(
                'move-node-to-workspace', '--window-id', window_id,
                str(workspace_for(home['group'], home['slot'])),
            )
        except subprocess.CalledProcessError:
            pass
        del collapsed[window_id]


def reconcile_topology(state, monitors):
    topology = monitor_topology(monitors)
    previous = state.get('topology')
    if previous is None:
        state['topology'] = topology
        return False
    if previous == topology:
        return False

    old_count = len(previous)
    new_count = len(topology)
    if new_count < old_count:
        collapse_removed_slots(state, old_count, new_count)
    elif new_count > old_count:
        restore_added_slots(state, new_count)
    state['topology'] = topology
    return True


def visible_groups(monitors):
    groups = []
    for monitor in monitors:
        workspace = run(
            'list-workspaces', '--monitor', str(monitor['monitor-id']),
            '--visible', '--format', '%{workspace}',
        )
        groups.append(workspace_group(workspace))
    return groups


def show_group(group, monitors, focused_monitor_id):
    adopt_separator_windows(group, monitors)
    for slot, monitor in enumerate(monitors):
        run(
            'move-workspace-to-monitor', '--workspace',
            str(workspace_for(group, slot)), str(monitor['monitor-id']),
        )

    ordered = [m for m in monitors if m['monitor-id'] != focused_monitor_id]
    ordered += [m for m in monitors if m['monitor-id'] == focused_monitor_id]
    slot_by_id = {m['monitor-id']: slot for slot, m in enumerate(monitors)}
    for monitor in ordered:
        run('workspace', str(workspace_for(group, slot_by_id[monitor['monitor-id']])))


def notify_indicator():
    subprocess.run(
        [SKETCHYBAR, '--trigger', 'desktop_pair_changed'], check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: pairs.py sync|next|prev|back|1|2|3|4|move N|send N')

    STATE.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open('w') as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return

        action = sys.argv[1]
        monitors = list_monitors()
        if not monitors:
            return
        focused = json.loads(run('list-monitors', '--focused', '--json'))[0]
        state = load_state()
        topology_changed = reconcile_topology(state, monitors)

        focused_group = workspace_group(run('list-workspaces', '--focused'))
        current = focused_group or state.get('active', 1)

        if action == 'sync':
            out_of_sync = any(group != current for group in visible_groups(monitors))
            if topology_changed or out_of_sync:
                show_group(current, monitors, focused['monitor-id'])
                notify_indicator()
            state['active'] = current
            save_state(state)
            return

        if action == 'next':
            target = current % 4 + 1
        elif action == 'prev':
            target = (current - 2) % 4 + 1
        elif action == 'back':
            target = state.get('previous', current)
        else:
            raw_target = sys.argv[2] if action in ('move', 'send') else action
            target = workspace_group(raw_target)
            if target is None:
                raise SystemExit('desktop group must be 1, 2, 3, or 4')

        slot_by_id = {m['monitor-id']: slot for slot, m in enumerate(monitors)}
        destination = workspace_for(target, slot_by_id[focused['monitor-id']])
        run(
            'move-workspace-to-monitor', '--workspace', str(destination),
            str(focused['monitor-id']),
        )

        if action in ('move', 'send'):
            run('move-node-to-workspace', str(destination))
            if action == 'send':
                save_state(state)
                return

        show_group(target, monitors, focused['monitor-id'])
        notify_indicator()
        if current != target:
            state['previous'] = current
        state['active'] = target
        save_state(state)


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        message = (error.stderr or error.stdout or str(error)).strip()
        raise SystemExit(message)

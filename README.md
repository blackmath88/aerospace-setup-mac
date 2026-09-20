# AeroSpace setup for macOS

A reusable macOS tiling setup built around AeroSpace, SketchyBar, and JankyBorders.

It provides:

- four keyboard-driven desktop groups;
- synchronized workspace pairs across a Mac display and an optional external display;
- a compact, centered workspace indicator with short accent lines;
- per-workspace colors shared by the indicator and window borders;
- small window gaps and a compact top clearance;
- navigation, move, send, resize, stack, and fullscreen shortcuts.

The repository contains configuration templates and scripts only. It does not contain credentials, logs, machine state, or bundled application binaries.

## Prerequisites

Install these components before running the installer:

- [AeroSpace](https://github.com/nikitabobko/AeroSpace)
- [SketchyBar](https://github.com/FelixKratz/SketchyBar)
- [JankyBorders](https://github.com/FelixKratz/JankyBorders)
- macOS Command Line Tools, including `/usr/bin/python3`

Grant AeroSpace the Accessibility permission requested by macOS. Ensure the `aerospace`, `sketchybar`, and `borders` commands are available, or set `AEROSPACE_BIN`, `SKETCHYBAR_BIN`, and `BORDERS_BIN` when running the installer.

## Install

Clone the repository on the target Mac, then run:

```bash
./install.sh
```

For synchronized workspace pairs across the built-in display and an external monitor, pass the exact external monitor name:

```bash
aerospace list-monitors
./install.sh "S34CG50"
```

The installer:

1. verifies the required commands;
2. backs up any existing managed files with a timestamp;
3. renders paths and the optional monitor name for the current Mac;
4. installs the AeroSpace, SketchyBar, workspace-pair, and LaunchAgent files;
5. reloads AeroSpace and starts the workspace indicator.

## Main shortcuts

Option acts as the main modifier.

| Shortcut | Action |
| --- | --- |
| `Option + Arrow` | Focus in a direction |
| `Option + Shift + Arrow` | Swap in a direction |
| `Option + 1…4` | Open a desktop group |
| `Option + Shift + 1…4` | Move the focused window and follow it |
| `Option + Control + Shift + 1…4` | Send the focused window without following |
| `Option + Tab` | Next desktop group |
| `Option + Shift + Tab` | Previous desktop group |
| `Option + Control + Tab` | Return to the previous desktop group |
| `Option + W` | Close the focused window |
| `Option + F` | Toggle fullscreen |
| `Option + T` | Toggle floating/tiling |
| `Option + V` | Stack with the right-hand window |
| `Option + Shift + V` | Stack with the left-hand window |
| `Option + Shift + R` | Reload AeroSpace configuration |

## Layout details

- Inner and outer side gaps: 12 points.
- Top clearance: 42 points.
- Workspace indicator: transparent full-width canvas, centered workspace buttons, and two 56×1-point accent lines.
- Workspace colors: blue, mauve, green, and gold.

## Restore an earlier configuration

Backups are written beside the replaced files with names such as:

```text
~/.aerospace.toml.backup-YYYYMMDD-HHMMSS
```

Stop the indicator before restoring a LaunchAgent backup:

```bash
launchctl bootout "gui/$UID/local.sketchybar.desktop-indicator" 2>/dev/null || true
```

Then copy the desired backup into place and reload AeroSpace.

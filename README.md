# AeroSpace · Adaptive Workspaces

**Four desktop groups. Any display setup. One keyboard-driven workflow.**

A small, opinionated macOS tiling configuration built with [AeroSpace](https://github.com/nikitabobko/AeroSpace), [SketchyBar](https://github.com/FelixKratz/SketchyBar), and [JankyBorders](https://github.com/FelixKratz/JankyBorders).

Instead of treating each monitor as a separate set of desktops, it maintains **four logical workspace groups** across connected displays. The same setup works on a laptop alone, a docked multi-monitor desk, and during display changes.

> [!NOTE]
> Screenshots or a short demo GIF are welcome contributions. No demo media is bundled yet.

## How it works

A group selects a corresponding workspace on each connected display:

| Group | Landscape external | Portrait external | Built-in display |
| --- | --- | --- | --- |
| 1 | 1 | 6 | 11 |
| 2 | 2 | 7 | 12 |
| 3 | 3 | 8 | 13 |
| 4 | 4 | 9 | 14 |

Roles are assigned automatically, ordered landscape → portrait → built-in. With fewer displays, only the available slots are used. Workspaces 5, 10, 15, … are reserved as separators rather than normal desktop groups.

When a monitor disconnects, the Python manager moves windows from unavailable slots to remaining displays, tracks their former slots, and tries to restore them if displays return. SketchyBar shows the active group; JankyBorders follows its accent color.

## Features

- Four linked workspace groups across available screens.
- Automatic landscape, portrait, and built-in display role selection.
- Group navigation, moving and sending windows, focus, resizing, stacking, and fullscreen shortcuts.
- Compact centered SketchyBar indicator and matching border accents.
- Small gaps, modest top clearance, and timestamped config backups.
- Python logic tests; no proprietary binaries or credentials bundled.

## Requirements

- macOS, with the Accessibility permissions AeroSpace requires.
- [AeroSpace](https://github.com/nikitabobko/AeroSpace)
- [SketchyBar](https://github.com/FelixKratz/SketchyBar)
- [JankyBorders](https://github.com/FelixKratz/JankyBorders)
- macOS Command Line Tools / system Python 3 (or set `PYTHON_BIN`).

Install and configure those tools first. The installer expects `aerospace`, `sketchybar`, and `borders` in your PATH, with Homebrew locations as fallbacks. You can override them using `AEROSPACE_BIN`, `SKETCHYBAR_BIN`, and `BORDERS_BIN`.

## Install

**Important:** This is an opinionated *replacement configuration*, not a merge with your current dotfiles. The installer overwrites managed AeroSpace and SketchyBar configuration files, after making timestamped backups if they already exist. Read the files and inspect the dry run before installing.

```bash
git clone https://github.com/blackmath88/aerospace-setup-mac.git
cd aerospace-setup-mac
./install.sh --dry-run
./install.sh
```

The script renders machine-local paths, installs the templates and a per-user LaunchAgent, reloads AeroSpace if running, and restarts the SketchyBar indicator. It does not install AeroSpace, SketchyBar, or JankyBorders themselves.

Run the included logic tests:

```bash
python3 -m unittest discover -s tests -v
```

## Main shortcuts

Option (⌥) is the primary modifier.

| Shortcut | Action |
| --- | --- |
| `Option + Arrow` | Focus a window in that direction |
| `Option + Shift + Arrow` | Swap windows |
| `Option + 1…4` | Switch logical group |
| `Option + Shift + 1…4` | Move focused window and follow |
| `Option + Control + Shift + 1…4` | Send focused window without following |
| `Option + Tab` / `Option + Shift + Tab` | Next / previous group |
| `Option + Control + Tab` | Previous active group |
| `Option + Control + Arrow` | Switch focused monitor |
| `Option + W` | Close window |
| `Option + F` | Fullscreen |
| `Option + T` | Toggle floating / tiling |
| `Option + V` / `Option + Shift + V` | Join with right / left window |
| `Option + Shift + R` | Reload AeroSpace config |

For the full mappings, see [`templates/aerospace.toml`](templates/aerospace.toml).

## Appearance

Inner and side gaps are 12 points; top clearance is 42 points. The workspace indicator is transparent, centered, and flanked by small accent lines. Groups use blue, mauve, green, and gold colors.

## Limitations and assumptions

- Monitor roles depend on display orientation and names. Multiple displays with identical roles/names may not stay in your desired physical order.
- The built-in display is identified by the monitor name containing `built-in`. Localized or differently named devices may require adjustment.
- Monitor topology reconciliation and window restoration are best-effort, not a guarantee that every app will return to its previous physical display.
- Requires live macOS services, so CI only validates static syntax and pure Python logic, not real dock/undock behavior.
- The script writes machine-local history and display cache in `~/.config/aerospace-pairs/` and logs in `~/.config/sketchybar/`. None are committed to this repository.

## Restore or uninstall

The installer backs up existing managed files next to them using a suffix like `.backup-YYYYMMDD-HHMMSS`.

To stop the indicator:

```bash
launchctl bootout "gui/$UID/local.sketchybar.desktop-indicator" 2>/dev/null || true
```

To roll back, **first identify your desired timestamped backups**. Restore those files over the generated configurations (including the AeroSpace config and, if previously present, SketchyBar config and LaunchAgent), then reload AeroSpace and restart your original services if needed. If a destination had no previous file, remove the file created by this installer rather than restoring a nonexistent backup.

The installer does not uninstall the three underlying applications. Do not delete shared SketchyBar files or your current LaunchAgent unless they belong to this installation.

## License

MIT — see [LICENSE](LICENSE). This is a personal, community-maintained configuration, not an official project of the upstream tools.

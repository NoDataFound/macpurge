# MacPurge Help Documentation

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Commands Reference](#commands-reference)
5. [Examples](#examples)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Overview

MacPurge is a command-line utility for cleaning up macOS systems. It intelligently scans for and removes:

- Application caches (`~/Library/Caches`)
- System logs (`~/Library/Logs`)
- Python virtual environments and bytecode caches
- Node.js `node_modules` directories
- Docker images, containers, and volumes
- Xcode derived data and simulators
- Homebrew download cache
- Trash contents
- Old downloads

### Key Features

- **Safe by default**: Only automatically cleans items that are safe to delete
- **Checkpoint/resume**: Long operations can be interrupted and resumed
- **Dry-run mode**: Preview what would be deleted without making changes
- **Category filtering**: Clean only specific types of items
- **Interactive mode**: Menu-driven selection for fine-grained control

---

## Installation

### Requirements

- macOS 10.15 or later
- Python 3.10 or later
- Command-line tools (Xcode or standalone)

### Quick Install

```bash
cd mac_cleaner
chmod +x installer.sh
./installer.sh
```

### Manual Install

```bash
python3 -m venv macpurge_venv
source macpurge_venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p state logs
```

---

## Configuration

MacPurge uses environment variables for configuration. Edit `.env` to customize:

### Path Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MACPURGE_HOME_DIR` | `~` | Home directory to scan |
| `MACPURGE_STATE_DIR` | `state` | Directory for checkpoints |

### Checkpoint Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MACPURGE_CHECKPOINT_INTERVAL` | `10` | Items between checkpoint saves |

### Scan Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MACPURGE_MIN_SIZE_MB` | `10` | Minimum size to include in results |
| `MACPURGE_SCAN_DOWNLOADS` | `true` | Include Downloads folder |
| `MACPURGE_SCAN_TRASH` | `true` | Include Trash |
| `MACPURGE_SCAN_XCODE` | `true` | Include Xcode data |
| `MACPURGE_SCAN_DOCKER` | `true` | Include Docker |
| `MACPURGE_SCAN_HOMEBREW` | `true` | Include Homebrew cache |
| `MACPURGE_SCAN_PYTHON` | `true` | Include Python environments |
| `MACPURGE_SCAN_NODE` | `true` | Include node_modules |

---

## Commands Reference

### scan

Scan system for cleanable items without making changes.

```
macpurge scan [OPTIONS]

Options:
  --all       Include dangerous items requiring confirmation
  --detailed  Show detailed list instead of summary
  --limit N   Limit detailed output to N items (default: 20)
```

### clean

Perform cleanup with interactive confirmation.

```
macpurge clean [OPTIONS]

Options:
  --dry-run          Preview without deleting anything
  --resume           Resume from previous checkpoint (default)
  --fresh            Ignore checkpoint, start fresh
  -y, --yes          Auto-confirm safe items
  -c, --category X   Only clean category X (can repeat)

Categories: cache, logs, python_venv, node_modules, brew, 
            docker, xcode, app_support, trash, downloads
```

### quick

Fast cleanup of only safe-to-delete items.

```
macpurge quick [OPTIONS]

Options:
  --dry-run  Preview without deleting
```

### interactive

Menu-driven cleanup interface.

```
macpurge interactive
```

### status

Show checkpoint status.

```
macpurge status
```

### clear-checkpoint

Remove checkpoint file.

```
macpurge clear-checkpoint
```

---

## Examples

### Basic scan

```bash
# See what can be cleaned
python src/main.py scan

# Include items that need confirmation
python src/main.py scan --all

# Show detailed list
python src/main.py scan --detailed --limit 50
```

### Safe cleanup

```bash
# Quick cleanup of caches and logs only
python src/main.py quick

# Preview first
python src/main.py quick --dry-run
```

### Full cleanup

```bash
# Interactive cleanup with confirmations
python src/main.py clean

# Skip confirmations for safe items
python src/main.py clean -y

# Only clean Python environments
python src/main.py clean -c python_venv

# Clean multiple categories
python src/main.py clean -c cache -c logs -c brew
```

### Resume interrupted cleanup

```bash
# Check if there's a checkpoint
python src/main.py status

# Resume from checkpoint
python src/main.py clean --resume

# Or start fresh
python src/main.py clean --fresh
```

---

## Troubleshooting

### "Permission denied" errors

Some system caches require elevated permissions. MacPurge skips these automatically.

For full access:
```bash
sudo python src/main.py clean
```

**Note**: Running as root is generally not recommended. Most user-space cleanup works without sudo.

### Docker cleanup not working

Ensure Docker Desktop is running:
```bash
open -a Docker
```

Then retry the cleanup.

### Homebrew cleanup not working

Ensure Homebrew is in PATH:
```bash
which brew
```

If not found, add to your shell profile:
```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Checkpoint file corrupted

Clear and start fresh:
```bash
python src/main.py clear-checkpoint
python src/main.py clean --fresh
```

### Scan is slow

Large directories take time to measure. To speed up:
1. Increase `MACPURGE_MIN_SIZE_MB` to skip smaller items
2. Disable categories you don't need in `.env`

---

## FAQ

### Is it safe?

MacPurge categorizes items as "safe" (auto-deletable) or "requires confirmation". Safe items include caches and logs that applications regenerate. Items like virtual environments always prompt before deletion.

### Will it break my apps?

Deleting caches may cause apps to start slower the first time (as they rebuild caches) but won't break functionality. Virtual environments and node_modules can be recreated with `pip install` and `npm install`.

### What's a checkpoint?

During cleanup, MacPurge saves progress every N items. If interrupted (Ctrl+C, power loss, etc.), you can resume where you left off instead of restarting.

### Can I exclude specific paths?

Currently, use category filtering. Path-level exclusions are planned for a future release.

### How is size calculated?

MacPurge uses `du -sk` for directories when available (fast), falling back to recursive Python traversal (slower but more compatible).

### Does it work on Linux?

MacPurge is designed for macOS but many features work on Linux. The scanner looks for macOS-specific paths like `~/Library` which don't exist on Linux.

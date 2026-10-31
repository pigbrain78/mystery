# Network Presence Monitor Architecture

This document describes the structure and configuration of the Python-based network presence monitor.

## Project Structure

```text
project_root/
├── config/
│   └── settings.py      # Main configuration (MACs, ranges, intervals)
├── core/
│   └── monitor.py       # Main loop: scans network, tracks state, dispatches events
├── automation/
│   └── handlers.py      # Logic triggered by state changes (scripts, logs)
├── notifications/
│   └── notify.py        # External notification integrations (macOS, ntfy)
├── dashboards/
│   └── server.py        # (Optional) Dashboard for viewing event history
└── logs/
    ├── events.log       # JSONL event history
    └── monitor.log      # Application logs
```

## Configuration Schema (`config/settings.py`)

| Key | Description | Example |
| :--- | :--- | :--- |
| `NETWORK_RANGE` | Subnet to scan | `"192.168.1.0/24"` |
| `DEVICES` | Dict of MAC -> Name mapping | `{"AA:BB:CC:DD:EE:01": "Sean iPhone"}` |
| `SCAN_INTERVAL` | Seconds between scans | `30` |
| `NOTIFICATIONS` | Dict for `enable_macos`, `enable_ntfy`, `ntfy_topic` | `{"enable_ntfy": True, "ntfy_topic": "..."}` |
| `AUTOMATIONS` | Lists of function paths for `on_online` and `on_offline` | `["automation.handlers.notify_online"]` |
| `ONLINE_SCRIPT` | Path to bash script for online events | `"/path/to/script.sh"` |

## Core Logic Flow

1.  **Scan**: Runs `arp-scan --localnet` (requires sudo) to get active MAC addresses.
2.  **State Tracking**: Compares current MACs against the configured `DEVICES` and the `last_state` cache.
3.  **Event Dispatch**: If state changes (online -> offline or vice versa):
    *   Logs JSON event to `logs/events.log`.
    *   Dynamically imports and calls functions listed in `AUTOMATIONS`.
    *   Sends notifications via `notifications/notify.py`.

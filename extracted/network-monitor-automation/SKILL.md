---
name: network-monitor-automation
description: "Managing, extending, and debugging the network presence monitor system. Use for: adding new devices, updating notification settings, troubleshooting scan errors, and adding new automation handlers."
---

# Network Presence Monitor Automation

This skill provides the procedural knowledge required to manage and extend the network presence monitor system, which tracks MAC addresses on a local network and triggers automations (scripts, notifications) when devices come online or go offline.

## Core Capabilities

- **Device Management**: Add or update MAC addresses and names in `config/settings.py`.
- **Notification Configuration**: Toggle macOS notifications or `ntfy.sh` push alerts.
- **Automation Handlers**: Create new functions in `automation/handlers.py` and register them in `config/settings.py`.
- **System Monitoring**: Check `logs/monitor.log` for scan errors and `logs/events.log` for presence history.
- **Mobile Integration**: Configure iOS 18 / iPhone 16 features (Action Button, Shortcuts, NFC) to interact with the monitor.

## Common Workflows

### 1. Adding a New Device
1.  Open `config/settings.py`.
2.  Add the MAC address (case-insensitive) and a descriptive name to the `DEVICES` dictionary.
3.  The monitor will automatically start tracking it on the next loop.

### 2. Adding a New Automation Handler
1.  Define a new function in `automation/handlers.py` that accepts a `device` dictionary (keys: `mac`, `name`, `state`).
2.  Example handler:
    ```python
    def my_new_handler(device: Dict) -> None:
        print(f"Custom logic for {device["name"]}")
    ```
3.  Register the full function path (e.g., `"automation.handlers.my_new_handler"`) in the `AUTOMATIONS` dictionary within `config/settings.py`.

### 3. Troubleshooting Scan Failures
- If the log shows `Error during network scan`, verify that `arp-scan` is installed and that the user has `sudo` privileges for it.
- Check the `NETWORK_RANGE` in `config/settings.py` matches the local subnet.

## Reference Documentation

For detailed architecture, configuration schema, and file structure, read:
- `/home/ubuntu/skills/network-monitor-automation/references/architecture.md`

For iOS-specific automation triggers, Shortcuts recipes, and iPhone 16 best practices, read:
- `/home/ubuntu/skills/network-monitor-automation/references/ios_automation.md`

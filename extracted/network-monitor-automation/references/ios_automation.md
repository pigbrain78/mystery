# iOS 18 & iPhone 16 Automation Best Practices

This document outlines how to integrate the Network Presence Monitor with native iOS features for a seamless mobile experience, based on the *Madness AI iPhone Automation Expert Playbook*.

## Hardware Triggers for Network Status

| Trigger | Recommended Use Case | Setup |
| :--- | :--- | :--- |
| **Action Button** | Quick Status Check | Map the Action Button to a Shortcut that calls the `dashboards/server.py` API or reads the `logs/events.log`. |
| **Back Tap** | Silent Toggle | Set a double-tap on the back of the iPhone to trigger a notification showing the last 3 network events. |
| **NFC Tags** | Contextual Monitoring | Place an NFC tag on your desk; scanning it triggers a "Work Laptop Status" check via the monitor. |

## Shortcut Design Principles

- **Modularity**: Break large workflows into smaller, single-purpose Shortcuts (e.g., "Fetch Status" vs. "Display Alert").
- **Error Handling**: Use "If" statements to check for network availability before attempting to reach the monitor's dashboard.
- **Variables & Typing**: Explicitly name Magic Variables and coerce types (e.g., force JSON response from the dashboard to be recognized as a Dictionary).

## Security & Privacy Settings

| Feature | Recommended Configuration | Rationale |
| :--- | :--- | :--- |
| **Clipboard Access** | "Ask" or "Deny" by default | Prevents automated background reading of sensitive data unless explicitly triggered. |
| **Location Services** | "While Using App" | Minimizes battery drain and ensures privacy while using location-aware triggers. |

## Example Automation Recipes

1.  **The Morning Briefing**: Triggered by the Wake Up Alarm. Fetches the current state of all devices from the monitor and speaks a summary via Siri.
2.  **Meeting Notes Cleanup**: Triggered by an NFC tag on the desk. Appends the "Work Laptop Online" timestamp to the current meeting note in Apple Notes.
3.  **Quick Contextual Prompt**: Triggered by a Control Center Widget. Asks for text input and sends it to the monitor's automation handler for custom processing.

## Troubleshooting Checklist
- **Memory Limits**: If a Shortcut fails, try restarting the iPhone as iOS may have hit a memory limit.
- **Privacy Permissions**: Check *Settings > Shortcuts > Advanced* to ensure "Allow Running Scripts" and "Allow Sharing Large Amounts of Data" are enabled.
- **Network Connection**: Ensure the iPhone is on the same subnet as the monitor or can reach it via a secure VPN/Proxy.

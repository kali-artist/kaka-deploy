---
name: systemd-service-troubleshooting
trigger: When troubleshooting systemd-managed services (restart, config changes, high resource usage)
description: Standardized procedure for service management and debugging
---

steps:
1. Stop conflicting processes: `pkill -f <service_name>`
2. Verify dependencies: `pip install -r requirements.txt`
3. Configure service keepalive (optional but recommended):
   - Edit service unit file: `systemctl --user edit --full <service_name>.service`
   - Set restart policy: `Restart=always`
   - Set restart interval: `RestartSec=5`
   - Reload systemd daemon: `systemctl --user daemon-reload`
4. Start the service: `systemctl --user start <service_name>.service`
5. Monitor logs: `journalctl --user -u <service_name>.service -f`
6. Check resource usage: `ps -o %cpu,%mem,cmd -p $(pgrep <service_name>)`

pitfalls:
- Avoid shell-level backgrounding (use terminal(background=true))
- Ensure log paths exist before starting
- Verify config file syntax before restart

verification:
- Confirm service is running: `ps aux | grep <service_name>`
- Validate log output contains 'CONFIG LOADED'
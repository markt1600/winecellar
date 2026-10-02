#!/bin/sh
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run using sudo.'; exit 1; }
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
test -x /usr/bin/nmcli
test -x /usr/sbin/modprobe
install -o root -g root -m 755 "$source_dir/wifi_recovery.py" /usr/local/sbin/winecellar-wifi-recovery
install -d -o root -g root -m 755 /var/lib/winecellar-wifi-recovery
cat > /etc/systemd/system/winecellar-wifi-recovery.service <<'EOF'
[Unit]
Description=Recover sustained cellar Wi-Fi disconnections without rebooting
After=NetworkManager.service

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /usr/local/sbin/winecellar-wifi-recovery
TimeoutStartSec=150
UMask=0022
EOF
cat > /etc/systemd/system/winecellar-wifi-recovery.timer <<'EOF'
[Unit]
Description=Check cellar Wi-Fi every minute

[Timer]
OnBootSec=2min
OnUnitInactiveSec=60s
AccuracySec=5s

[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now winecellar-wifi-recovery.timer
echo 'Wi-Fi watchdog enabled. A healthy connection is left alone. No Pi reboots.'

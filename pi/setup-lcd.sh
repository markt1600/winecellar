#!/bin/sh
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run using sudo.'; exit 1; }
base=/home/markt1600/winecellar
config=/boot/firmware/config.txt
test -s "$base/waveshare35c.dtbo"
apt-get install -y python3-pil fonts-dejavu-core
cp -n "$config" "$base/config.before-lcd.txt"
install -m 644 "$base/waveshare35c.dtbo" /boot/firmware/overlays/winecellar35c.dtbo
if ! grep -q '^dtoverlay=winecellar35c' "$config"; then
 cat >> "$config" <<'EOF'

# Wine cellar SPI LCD, conservative clock for jumper wiring
[all]
dtparam=spi=on
dtoverlay=winecellar35c,speed=8000000,rotate=90,fps=10
EOF
fi
printf '%s\n' 'LCD configuration installed. Reboot with: sudo reboot'

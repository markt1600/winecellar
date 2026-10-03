# Fresh Raspberry Pi installation and recovery

This guide reproduces Cellar @ BH on a Raspberry Pi Zero 2 W using Raspberry Pi OS Lite **32-bit, Debian 13 Trixie**, username **markt1600**, hostname **winecellar**. Verified against the working Pi on 3 October 2026. The complete process has not yet been exercised on a newly erased card; perform the acceptance checks below before relying on it.

## What GitHub contains

Website/API source, all seven Pi application services, bottle artwork, sensor and LCD software, control helpers, diagnostic recorder, Wi-Fi recovery installer and the working LCD device-tree overlay are included.

GitHub does **not** contain the private upload signing key, SSH keys, Wi-Fi password, Vercel secrets, SQLite history, private videos, touch calibration or an SD-card image. Do not commit them. The live Pi executes copies in `~/winecellar`, not the `pi/` directory of a checkout; pulling Git alone does not update the running services.

This is a replacement-device guide, not a second-device installation. Do not run two uploaders against the same cloud paths/signing identity concurrently.

## 1. Preserve private files before erasing an existing card

Store a private backup of:

- `~/winecellar/keys/upload.pem` (essential for the existing website to accept uploads).
- `~/winecellar/data/`, including readings, monitoring session, calibration, controls and diagnostic reports.
- `~/winecellar/camera/motion.json` and, if wanted, pending `camera/spool/` files.
- `/boot/firmware/config.txt` and the active overlay for reference.

For a consistent filesystem copy of SQLite/WAL files, shut down or stop the application services before copying the complete data directory. Alternatively use SQLite's backup facility. A copy of only the main database while it is being written can omit WAL data. Keep the original card intact until the replacement passes testing. No backup of private files is created automatically by this guide.

## 2. Image and connect

Use Raspberry Pi Imager on Windows to write Raspberry Pi OS Lite 32-bit. Configure the username, hostname, country, time zone, 2.4 GHz Wi-Fi and SSH. Enable password authentication initially or install your SSH public key. Boot, then from PowerShell:

```powershell
ssh markt1600@winecellar.local
```

If discovery fails, find its IP in the router and SSH to that address. The existing computer's SSH key does not automatically become authorized on a newly imaged Pi. A new host key is expected after reimaging: verify the destination before updating a saved host-key entry.

Commands below run **on the Pi**, unless indicated otherwise. The helper scripts assume username `markt1600`; adapt their paths and sudoers entries if choosing another username.

## 3. Dependencies and application files

```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip python3-dev build-essential python3-pil fonts-dejavu-core python3-lgpio python3-libgpiod libgpiod3 rpicam-apps-lite ffmpeg openssl iw device-tree-compiler
sudo timedatectl set-timezone Asia/Singapore
sudo usermod -aG gpio,video,input,spi,i2c,adm markt1600
sudo loginctl enable-linger markt1600
git clone https://github.com/markt1600/winecellar.git ~/winecellar-source
mkdir -p ~/winecellar/data ~/winecellar/keys ~/.config/systemd/user
cp -a ~/winecellar-source/pi/. ~/winecellar/
python3 -m venv --system-site-packages ~/winecellar/.venv
~/winecellar/.venv/bin/pip install 'Adafruit-Blinka==9.2.0' 'adafruit-circuitpython-dht==4.0.12' 'RPi.GPIO==0.7.1'
cp ~/winecellar/winecellar-*.service ~/.config/systemd/user/
```

Log out/in after changing group membership (the reboot below also does this). LCD and camera use system Python; sensor logging uses the virtual environment. These are the top-level package versions observed on the working system, not a lockfile for every transitive dependency.

## 4. Hardware and boot configuration

Disconnect power before wiring GPIO or camera ribbons. Use the narrow Pi Zero camera cable. This configuration uses DS18B20 data on **BCM GPIO4 (physical pin 7)**, DHT22 output on **BCM GPIO22 (physical pin 15)**, 3.3V sensor logic and a shared ground. Verify each probe's wire assignments, including any adapter; wire colours alone are not a pinout. Keep the DS18B20 pull-up between data and 3.3V.

The LCD is specifically the **Waveshare 3.5-inch RPi LCD (C), ILI9486, ADS7846 touch**. The supplied overlay uses SPI0 CE0 for display, CE1 for touch, GPIO25 reset, GPIO24 data/command, GPIO17 touch interrupt. Do not use it with another LCD model without checking its wiring. On a 40-pin Pi those signals are pins 24, 26, 22, 18 and 11 respectively; SPI MOSI/MISO/SCLK are pins 19/21/23. Power and ground connections must follow the LCD manufacturer's pinout; this guide is not a socket-orientation diagram.

Edit `/boot/firmware/config.txt`; ensure these appear under `[all]` without conflicting duplicates:

```ini
camera_auto_detect=1
dtoverlay=w1-gpio
```

Install the included, working LCD overlay:

```bash
sudo sh ~/winecellar/setup-lcd.sh
sudo reboot
```

The LCD installer adds SPI and `dtoverlay=winecellar35c,speed=1000000,rotate=90,fps=10`. **Keep the 1 MHz speed** used with our Dupont wiring. If an LCD entry already exists, check it manually: the installer does not replace an existing entry. The original faster setup produced a white screen. The framebuffer should be 480×320, 16-bit, with a name containing `ili9486`.

Included `pi/waveshare35c.dtbo` is a byte-for-byte copy of the working device's active overlay, not newly generated source. SHA-256:

```text
28e896d16fe4026c62f04bf85eb5426239f384c79e0bcc3db6975e053b4f3ec4
```

It depends on kernel support for the ILI9486 framebuffer and ADS7846 input driver. A different OS/kernel may require additional LCD work; do not blindly replace all boot settings with an old config file.

## 5. Register the actual probe and signing identity

```bash
ls /sys/bus/w1/devices/28-*
```

Edit `PROBE` in `~/winecellar/logger.py` to match the detected `28-.../w1_slave` path. The repository currently uses replacement probe **28-2e470087136b**. A new probe has a different identity and will not work with the old hard-coded path. If no probe appears, investigate wiring before changing software.

Restore the private `upload.pem` backup into `~/winecellar/keys/`, then:

```bash
chmod 700 ~/winecellar/keys
chmod 600 ~/winecellar/keys/upload.pem
```

If the key is lost, generate a replacement on the Pi:

```bash
umask 077
openssl genpkey -algorithm ED25519 -out ~/winecellar/keys/upload.pem
openssl pkey -in ~/winecellar/keys/upload.pem -pubout
```

Copy **only the public key** into `lib/ingestion.mjs` in the source repository, commit and deploy the website. The private key stays off GitHub. Never overwrite an existing key as a routine installation step. Ensure the clock is synchronized (`timedatectl status`): signed requests expire after five minutes.

Restore backed-up `data/` before starting services if preserving history. Local SQLite data drives historical statistics; an empty Pi does not automatically rebuild it from Blob archives.

## 6. Controls, Wi-Fi and background services

```bash
sudo sh ~/winecellar/setup-reboot.sh
sudo sh ~/winecellar/setup-shutdown.sh
```

These grant only fixed reboot/shutdown helper commands to the application. Neither setup command powers off the Pi.

Find the Wi-Fi connection profile name (not necessarily the SSID):

```bash
nmcli -t -f NAME,TYPE connection show --active
```

For our profile:

```bash
sudo nmcli connection modify netplan-wlan0-markt1600 connection.autoconnect yes connection.autoconnect-retries 0 802-11-wireless.powersave 2
sudo /usr/sbin/iw dev wlan0 set power_save off
```

If the profile differs, substitute its name above and edit `PROFILE` in `~/winecellar/wifi_recovery.py` **before installation**:

```bash
sudo sh ~/winecellar/setup-wifi-recovery.sh
systemctl --user daemon-reload
systemctl --user enable --now winecellar-logger winecellar-upload winecellar-camera winecellar-clips winecellar-control winecellar-lcd winecellar-diagnostics
```

Watchdog: checks each minute, toggles Wi-Fi after five minutes disconnected, reloads `brcmfmac` after another five minutes, then waits 30 minutes between further reloads. No Pi reboot; no reset solely because the internet or website is down. It respects a manually disabled radio. Installed code is root-owned at `/usr/local/sbin/winecellar-wifi-recovery`; later edits require rerunning its installer. **Do not re-enable the old hourly/three-hour reboot experiments.**

First LCD use runs touch calibration: tap each target once and wait for the next screen. Existing valid calibration can be restored for the same hardware. Bottle labels control dimming, period and confirmed reboot; scheduled dimming is 10pm–7am Singapore time. Motion configuration is created automatically on first camera start; optional old tuning lives in `camera/motion.json`.

## 7. Acceptance checks

```bash
cat ~/winecellar/data/status.json
cat ~/winecellar/data/upload-status.json
systemctl --user --failed
systemctl is-active winecellar-wifi-recovery.timer
python3 /usr/local/sbin/winecellar-wifi-recovery --check
/usr/sbin/iw dev wlan0 get power_save
rpicam-hello --list-cameras
journalctl _SYSTEMD_USER_UNIT=winecellar-logger.service -n 20 --no-pager
journalctl _SYSTEMD_USER_UNIT=winecellar-upload.service -n 20 --no-pager
```

Confirm both temperatures/humidity update, the LCD is legible, touch works, dashboard timestamps advance, and an actual hand-wave produces a playable private clip. Camera and pending queue each retain at most ten completed clips; a cold start needs pre-roll warmup. Log in through the existing marktan.ai owner login to check recordings, controls and diagnostic downloads.

The diagnostics service retains up to 20 reports plus approximately 30 minutes of rolling health history under `data/diagnostics/`. It uploads private reports when connectivity returns. Watchdog events are in `/var/lib/winecellar-wifi-recovery/events.json`; the website shows its latest trigger/recovery timestamps. These are evidence, not a guarantee that every electrical transient or sudden power loss is captured.

Run at least 24–48 hours on the desk, then a separate cellar test before immersion. Keep connector joints dry. Shut down from the confirmed owner control or `sudo shutdown -h now` before unplugging.

## Website and external services

The existing replacement Pi continues using `https://winecellar.marktan.ai`; it does not require redeploying the website unless changing its signing public key or code. For a full rebuild: use Node 22+, `npm ci`, `npm test`, `npm run build`; connect the main branch to a Next.js Vercel project with a **private** Vercel Blob store providing `BLOB_READ_WRITE_TOKEN`. Restore the domain/DNS and retain the shared owner-login service at `security.marktan.ai`. Public sensor data and owner-only recordings/diagnostics are deliberately separate.

The production origin and service URLs are embedded in the application and Pi files. Hosting at another domain requires reviewing those constants and the shared-cookie authentication integration. Vercel project settings, Blob contents and domain configuration are external dependencies, not restored by cloning GitHub.

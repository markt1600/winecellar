# The Cellar

Environmental journal at https://winecellar.marktan.ai. Raspberry Pi Zero 2 W reads a DS18B20 on GPIO4 and a DHT22 on GPIO22. Motion video stays in private storage. No face detection or extraction is performed.

## Running system

`pi/logger.py` writes a SQLite row every approximately 10 seconds. Timestamps are UTC; the dashboard uses Asia/Singapore. Failed readings are null with error text, never replaced with stale values. The DHT22 gets one retry after 2.5 seconds. DS18B20 CRC and range are validated, and the power-on 85°C sentinel is rejected. This is a wine-cellar application, not a high-temperature monitor.

Database: `/home/markt1600/winecellar/data/readings.sqlite3`. The companion status JSON is updated atomically. SQLite WAL and full synchronous writes improve durability but do not replace backups or proper shutdowns.

User systemd services `winecellar-logger` and `winecellar-upload` start with user lingering enabled and restart after failures. Use `systemctl --user status winecellar-logger winecellar-upload` and `journalctl --user -u winecellar-upload -n 20`.

## Cloud storage

The uploader runs once a minute. It stores raw readings in per-hour JSON objects under `cellar/v1/readings/` and a bounded dashboard snapshot at `cellar/v1/dashboard.json` in the connected **private** Vercel Blob store. Hour archives are acknowledged individually and resumable; retries do not create duplicate objects. The Pi keeps all original readings. Historical charts and selected-period min/max/mean values are calculated from local data. No cloud deletion is implemented.

The Pi signs each upload using Ed25519. Its private key lives only in `~/winecellar/keys/upload.pem`, mode 600, and is not the SSH key. The matching public key is in `lib/ingestion.mjs`. The server verifies the signature, five-minute request timestamp window, size and schema before writing. Hour identifiers cannot select arbitrary paths. Blob credentials remain in Vercel. Reimaging requires restoring the database and device key or registering a replacement public key.

`BLOB_READ_WRITE_TOKEN` is supplied by the private-store project integration. SDK access always requests `private`. Environmental dashboard readings are public. Raw Blob archives and all camera endpoints remain private. The site verifies the existing `__Secure-mt_camera` owner session through `https://security.marktan.ai/api/session`; verification fails closed if that service is unavailable. No sign-in secret is copied. The parent marktan.ai login and security service must remain available. Environmental API responses are no-store. Camera responses are private/no-store.

## Dashboard

Current bottle/ambient temperature and humidity; rolling 24h and all-time extremes; selectable 1h, 24h, one calendar month and one calendar year; exact selected-period extremes/times and sample means. Charts use 10s, 120s, 1h and 1-day buckets respectively, retaining min/max whiskers. The CSV exports these chart buckets (not every raw sample). Charts do not interpolate missing buckets; a partially populated bucket averages only its valid readings. Humidity is separate from temperature. Estimated dew point and bottle-air difference are shown. Configurable display ranges are browser-local illustrative values, not alerts or storage advice. Historical data accrues from installation onward; missing history is never fabricated.

LCD rendering, alerts and richer duration-based excursion analysis remain later integration stages. Raw sensor data is preserved to support them.

## Development

Node 22+: `npm ci`, `npm test`, `npm run build`. Deploy the connected main branch to Vercel using the Next.js framework. Do not commit readings, credentials, keys or recordings. Test Python snapshots with `python -m unittest discover -s tests -p 'test_*.py'`.

## Motion camera

Install `ffmpeg` from Raspberry Pi OS apt. The recorder uses the already-installed `rpicam-vid` native `motion_detect` stage on a 128x96 stream, comparing subsampled luminance pixels at 3 Hz. H264 is hardware encoded at 1280x720, 15 fps, target 800 kbit/s. This is pixel-change detection, not person recognition: lights, shadows and camera movement can trigger it. Adjust `~/winecellar/camera/motion.json` and restart the camera service after positioning it.

`winecellar-camera.service` records one-second, independently decodable H264 segments into the user's RAM-backed runtime directory. Only motion clips reach the SD card. Clips include at least five seconds before a trigger (once the startup buffer fills), and five seconds after motion stops. Segment boundaries may add roughly one or two seconds. Persistent activity splits into approximately 20-second overlapping clips, preserving coverage. The first eight seconds after start are an exposure/buffer warmup.

`winecellar-clips.service` packages with FFmpeg stream copy (no video re-encoding) and uploads signed binary envelopes. The server stores immutable MP4 and metadata objects in private Blob; it verifies the same device signature as sensor uploads. Video listing and playback require the shared owner login, and byte ranges are streamed through the authenticated server. Videos are not stored in GitHub. Cloud storage keeps the newest 10 recordings (including setup tests); each acknowledged upload removes older MP4s and their event metadata. The Pi spool retains at most the newest 10 completed pending clips. Older pending clips are discarded even if not uploaded; active footage is preserved. Upload preparation copies a clip under the shared queue lock so pruning cannot race its encoding. Camera health (state, queue count and update time only) is public; recordings and clip metadata remain owner-only.

Local queue: `~/winecellar/camera/spool`. Pending footage is retained across upload outages; local files are removed only after a durable server acknowledgement. At 512 MiB of spool or under 1 GiB disk free, new event recording pauses so temperature logging retains space. Camera capture stops at 78 C Pi temperature and systemd retries later. Services run at lower priority with CPU and memory caps. Interrupted partial clips are not presented as complete footage.

Install both user service files, then `systemctl --user daemon-reload` and `systemctl --user enable --now winecellar-camera winecellar-clips`. Stop with `systemctl --user stop winecellar-camera winecellar-clips`. `data/camera-status.json` and `data/camera-upload-status.json` report capture/queue/cloud health, and sensor snapshots carry these statuses to the dashboard.

A software-triggered setup clip can be requested with `touch ~/winecellar/camera/test-trigger`. These are explicitly labelled "Setup test", not motion events. A hand-wave test verifies actual motion detection. Benchmark on this Pi Zero 2 W: native detection + 720p encoder used approximately 13% of one CPU core, about 17 MiB process RSS, no swapping or throttling, while sensor logging/upload continued. This measurement excludes packaging/upload bursts; check combined service load after installation.


## Public readings and monitoring periods

The homepage and `/api/readings` expose environmental readings without login. Camera status, event listing, video playback and monitoring reset endpoints still require the shared Google owner session. Camera metadata is stripped from the environmental endpoint. Anonymous visitors see a camera login panel rather than recordings.

The owner-only control at the bottom of the page starts a new monitoring period, optionally named for a location (the name is public). It requires explicit confirmation, owner authentication and the production same-origin header. The reset writes a private Blob boundary; the signed Pi uploader polls it every minute and computes charts, rolling extrema and period extrema only from readings at or after that boundary. Raw SQLite readings and hourly archives are preserved. Older history is retained but not selectable in this initial period-reset UI. Video collection is independent.

The dashboard shows a waiting state until the Pi acknowledges the new boundary in a snapshot, so an old snapshot cannot masquerade as reset data. If offline, the Pi applies the boundary when it reconnects. Install the updated `pi/upload.py` and `pi/snapshot.py` on the Pi and restart `winecellar-upload` to enable this protocol. Adding the control does not itself reset any readings.

## Owner reboot control

The owner-only bottom-page control queues a fixed reboot action via private Blob. Requests require the shared owner session and production Origin. The Pi polls over HTTPS with its existing signed-device credentials; no inbound SSH or password is exposed to the web. Queued requests expire after two minutes, require a recent ready heartbeat, and are tied to the current boot ID. The Pi durably records handled IDs before scheduling a reboot to prevent replay loops. Rebooting pauses capture/logging briefly; it does not reset monitoring or delete data.

Install `pi/reboot_control.py` and its user service. Run `sudo sh ~/winecellar/setup-reboot.sh` once. This installs a root-owned, no-arguments helper whose only action is `/usr/sbin/shutdown -r +1`, and grants markt1600 passwordless sudo for only that helper. The setup itself does not reboot. Then enable `winecellar-control.service`. The website reports queued, scheduled and reconnected states. A full restart is not exercised during deployment; use the owner confirmation button when ready. Revoke with `sudo rm /etc/sudoers.d/winecellar-reboot` and stop/disable the user service.

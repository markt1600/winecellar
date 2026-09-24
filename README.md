# The Cellar

Private environmental journal at https://winecellar.marktan.ai. Raspberry Pi Zero 2 W reads a DS18B20 on GPIO4 and a DHT22 on GPIO22. No faces or video are collected by this version.

## Running system

`pi/logger.py` writes a SQLite row every approximately 10 seconds. Timestamps are UTC; the dashboard uses Asia/Singapore. Failed readings are null with error text, never replaced with stale values. The DHT22 gets one retry after 2.5 seconds. DS18B20 CRC and range are validated, and the power-on 85°C sentinel is rejected. This is a wine-cellar application, not a high-temperature monitor.

Database: `/home/markt1600/winecellar/data/readings.sqlite3`. The companion status JSON is updated atomically. SQLite WAL and full synchronous writes improve durability but do not replace backups or proper shutdowns.

User systemd services `winecellar-logger` and `winecellar-upload` start with user lingering enabled and restart after failures. Use `systemctl --user status winecellar-logger winecellar-upload` and `journalctl --user -u winecellar-upload -n 20`.

## Cloud storage

The uploader runs once a minute. It stores raw readings in per-hour JSON objects under `cellar/v1/readings/` and a bounded dashboard snapshot at `cellar/v1/dashboard.json` in the connected **private** Vercel Blob store. Hour archives are acknowledged individually and resumable; retries do not create duplicate objects. The Pi keeps all original readings. Historical charts and selected-period min/max/mean values are calculated from local data. No cloud deletion is implemented.

The Pi signs each upload using Ed25519. Its private key lives only in `~/winecellar/keys/upload.pem`, mode 600, and is not the SSH key. The matching public key is in `lib/ingestion.mjs`. The server verifies the signature, five-minute request timestamp window, size and schema before writing. Hour identifiers cannot select arbitrary paths. Blob credentials remain in Vercel. Reimaging requires restoring the database and device key or registering a replacement public key.

`BLOB_READ_WRITE_TOKEN` is supplied by the private-store project integration. SDK access always requests `private`. Dashboard reads and archives are not public. The site verifies the existing `__Secure-mt_camera` owner session through `https://security.marktan.ai/api/session`; verification fails closed if that service is unavailable. No sign-in secret is copied. The parent marktan.ai login and security service must remain available. All API responses with readings are private/no-store.

## Dashboard

Current bottle/ambient temperature and humidity; rolling 24h and all-time extremes; selectable 1h, 24h, one calendar month and one calendar year; exact selected-period extremes/times and sample means. Charts use 10s, 120s, 1h and 1-day buckets respectively, retaining min/max whiskers. The CSV exports these chart buckets (not every raw sample). Charts do not interpolate missing buckets; a partially populated bucket averages only its valid readings. Humidity is separate from temperature. Estimated dew point and bottle-air difference are shown. Configurable display ranges are browser-local illustrative values, not alerts or storage advice. Historical data accrues from installation onward; missing history is never fabricated.

Motion capture, LCD rendering, alerts and richer duration-based excursion analysis are later hardware/integration stages, not active in this release. Raw data is preserved to support them.

## Development

Node 22+: `npm ci`, `npm test`, `npm run build`. Deploy the connected main branch to Vercel using the Next.js framework. Do not commit readings, credentials, keys or recordings. Test Python snapshots with `python -m unittest discover -s tests -p 'test_*.py'`.

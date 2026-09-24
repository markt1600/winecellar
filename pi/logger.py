"""Wine cellar local sensor logger. UTC timestamps; SQLite values use C and %RH."""
import json
import logging
import math
import os
from pathlib import Path
import signal
import sqlite3
import time
from datetime import datetime, timezone

import adafruit_dht
import board

ROOT = Path.home() / 'winecellar'
DATA = ROOT / 'data'
PROBE = Path('/sys/bus/w1/devices/28-06900087a696/w1_slave')
INTERVAL = 10
running = True


def stop(*_):
    global running
    running = False


def read_bottle():
    lines = PROBE.read_text().splitlines()
    if len(lines) < 2 or not lines[0].strip().endswith('YES'):
        raise ValueError('Bottle sensor checksum failed')
    value = int(lines[1].split('t=')[1]) / 1000
    if not -55 <= value <= 125 or value == 85:
        raise ValueError('Bottle sensor invalid or power-on reading')
    return value


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATA / 'readings.sqlite3', timeout=10)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=FULL')
    conn.execute('''CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY,
        observed_at TEXT NOT NULL,
        bottle_c REAL,
        ambient_c REAL,
        humidity_pct REAL,
        bottle_error TEXT,
        ambient_error TEXT
    )''')
    conn.execute('CREATE INDEX IF NOT EXISTS readings_time ON readings(observed_at)')
    conn.commit()
    sensor = adafruit_dht.DHT22(board.D22, use_pulseio=False)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logging.info('Logging every %ss to %s', INTERVAL, DATA / 'readings.sqlite3')
    try:
        while running:
            started = time.monotonic()
            bottle = ambient = humidity = None
            bottle_error = ambient_error = None
            try:
                bottle = read_bottle()
            except (OSError, ValueError, IndexError) as exc:
                bottle_error = str(exc)
            # Retry transient DHT timing/checksum errors without reusing stale values.
            for attempt in range(2):
                try:
                    t, h = sensor.temperature, sensor.humidity
                    if t is None or h is None or not all(math.isfinite(v) for v in (t, h)):
                        raise ValueError('Missing or non-finite DHT reading')
                    if not -40 <= t <= 80 or not 0 <= h <= 100:
                        raise ValueError('DHT reading outside sensor range')
                    ambient, humidity = t, h
                    ambient_error = None
                    break
                except (RuntimeError, OSError, ValueError) as exc:
                    ambient_error = str(exc)
                    if attempt == 0:
                        time.sleep(2.5)
            timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
            with conn:
                conn.execute('''INSERT INTO readings
                    (observed_at,bottle_c,ambient_c,humidity_pct,bottle_error,ambient_error)
                    VALUES (?,?,?,?,?,?)''',
                    (timestamp, bottle, ambient, humidity, bottle_error, ambient_error))
            status = dict(observed_at=timestamp, bottle_c=bottle, ambient_c=ambient,
                          humidity_pct=humidity, bottle_error=bottle_error,
                          ambient_error=ambient_error, interval_seconds=INTERVAL)
            temporary = DATA / 'status.tmp'
            temporary.write_text(json.dumps(status, indent=2) + '\n')
            os.replace(temporary, DATA / 'status.json')
            if bottle_error or ambient_error:
                logging.warning('Sensor error: bottle=%s ambient=%s', bottle_error, ambient_error)
            remaining = max(0, INTERVAL - (time.monotonic() - started))
            deadline = time.monotonic() + remaining
            while running and time.monotonic() < deadline:
                time.sleep(min(0.5, max(0, deadline - time.monotonic())))
    finally:
        sensor.exit()
        conn.close()


if __name__ == '__main__':
    main()

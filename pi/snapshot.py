"""Build bounded chart snapshots from the authoritative local SQLite database."""
from datetime import datetime, timedelta, timezone
import calendar
import sqlite3

FIELDS = ('bottle_c', 'ambient_c', 'humidity_pct')


def iso(value):
    return value.isoformat(timespec='milliseconds')


def previous_month(now):
    year, month = (now.year - 1, 12) if now.month == 1 else (now.year, now.month - 1)
    return now.replace(year=year, month=month, day=min(now.day, calendar.monthrange(year, month)[1]))


def statistics(db, start, end):
    result = {}
    for field in FIELDS:
        row = db.execute(f'SELECT COUNT({field}), MIN({field}), MAX({field}), AVG({field}) FROM readings WHERE observed_at>=? AND observed_at<=?', (start, end)).fetchone()
        item = dict(count=row[0], min=row[1], max=row[2], avg=row[3], minAt=None, maxAt=None)
        if row[0]:
            for kind, order in [('min', 'ASC'), ('max', 'DESC')]:
                item[kind+'At'] = db.execute(f'SELECT observed_at FROM readings WHERE observed_at>=? AND observed_at<=? AND {field} IS NOT NULL ORDER BY {field} {order}, observed_at LIMIT 1', (start, end)).fetchone()[0]
        result[field] = item
    return result


def snapshot(db, now=None, session=None):
    now = now or datetime.now(timezone.utc)
    cutoff=iso(datetime.fromisoformat(session['startedAt'].replace('Z','+00:00'))) if session else ''
    first = db.execute('SELECT MIN(observed_at) FROM readings WHERE observed_at>=?',(cutoff,)).fetchone()[0]
    latest = db.execute('SELECT * FROM readings WHERE observed_at>=? ORDER BY id DESC LIMIT 1',(cutoff,)).fetchone()
    if not latest:
        return None
    ends = iso(now)
    last_successful = {}
    for field in FIELDS:
        row = db.execute(f'SELECT observed_at, {field} AS value FROM readings WHERE observed_at>=? AND observed_at<=? AND {field} IS NOT NULL ORDER BY observed_at DESC, id DESC LIMIT 1', (cutoff, ends)).fetchone()
        last_successful[field] = dict(row) if row else None
    starts = {'1h':now-timedelta(hours=1), '24h':now-timedelta(hours=24),
              '1mo':previous_month(now), '1y':now.replace(year=now.year-1,day=min(now.day,calendar.monthrange(now.year-1,now.month)[1]))}
    steps = {'1h':10, '24h':120, '1mo':3600, '1y':86400}
    windows = {}
    for key, start in starts.items():
        if session:start=max(start,datetime.fromisoformat(cutoff))
        step=steps[key]
        columns=', '.join(f'AVG({f}) AS {f}, MIN({f}) AS {f}_min, MAX({f}) AS {f}_max, COUNT({f}) AS {f}_count' for f in FIELDS)
        rows=db.execute(f'''SELECT CAST(unixepoch(observed_at)/? AS INTEGER)*? AS bucket,
            COUNT(*) AS samples, {columns} FROM readings
            WHERE observed_at>=? AND observed_at<=? GROUP BY bucket ORDER BY bucket''', (step,step,iso(start),ends))
        points=[]
        for row in rows:
            p=dict(row)
            bucket=p.pop('bucket')
            p['at']=iso(max(start,datetime.fromtimestamp(bucket,timezone.utc)))
            points.append(p)
        windows[key]=dict(start=iso(start),end=ends,bucketSeconds=step,points=points,
                          samples=sum(p['samples'] for p in points),stats=statistics(db,iso(start),ends))
    return dict(version=1,kind='snapshot',generatedAt=ends,recordingSince=first,monitoringSession=session,
                latest=dict(latest),lastSuccessful=last_successful,allTime=statistics(db,first,ends),windows=windows)

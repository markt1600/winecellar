"""Upload hourly archives and a dashboard snapshot using a Pi-only signing key."""
import base64
import fcntl
import json
import logging
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from snapshot import snapshot

ROOT=Path.home()/'winecellar'
DATA=ROOT/'data'
URL='https://winecellar.marktan.ai/api/ingest'


def send(payload):
    body=json.dumps(payload,separators=(',',':'),allow_nan=False).encode()
    stamp=str(int(time.time()*1000))
    # OpenSSL Ed25519 signing needs a seekable input; the temporary file holds readings, not a key.
    with tempfile.NamedTemporaryFile() as message:
        message.write(stamp.encode()+b'\n'+body)
        message.flush()
        signature=subprocess.check_output(['openssl','pkeyutl','-sign','-rawin','-inkey',
            str(ROOT/'keys/upload.pem'),'-in',message.name],stderr=subprocess.DEVNULL)
    request=urllib.request.Request(URL,data=body,method='POST',headers={
        'Content-Type':'application/json','X-Cellar-Time':stamp,
        'X-Cellar-Signature':base64.b64encode(signature).decode()})
    with urllib.request.urlopen(request,timeout=70) as response:
        if response.status!=200 or json.load(response).get('ok') is not True:
            raise RuntimeError('Upload not acknowledged')


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    lock=open(DATA/'upload.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
    state=sqlite3.connect(DATA/'upload-state.sqlite3',timeout=10)
    state.execute('CREATE TABLE IF NOT EXISTS uploaded(hour TEXT PRIMARY KEY, last_id INTEGER NOT NULL)')
    while True:
        started=time.monotonic()
        try:
            db=sqlite3.connect(f'file:{DATA / "readings.sqlite3"}?mode=ro',uri=True,timeout=10)
            db.row_factory=sqlite3.Row
            try:
                # A short read transaction makes each snapshot internally consistent.
                db.execute('BEGIN')
                payload=snapshot(db)
                pending=[]
                for hour,last_id in db.execute('SELECT substr(observed_at,1,13),MAX(id) FROM readings GROUP BY substr(observed_at,1,13) ORDER BY MIN(id)'):
                    old=state.execute('SELECT last_id FROM uploaded WHERE hour=?',(hour,)).fetchone()
                    if not old or old[0]<last_id:
                        rows=[dict(r) for r in db.execute('SELECT * FROM readings WHERE observed_at>=? AND observed_at<? ORDER BY id',(hour,hour+'~'))]
                        pending.append((hour,last_id,dict(version=1,kind='archive',hour=hour,rows=rows)))
                        if len(pending)>=24:
                            break
                db.commit()
            finally:
                db.close()
            for hour,last_id,archive in pending:
                send(archive)
                with state:
                    state.execute('INSERT OR REPLACE INTO uploaded VALUES (?,?)',(hour,last_id))
            if payload:
                send(payload)
                status=dict(last_success=datetime.now(timezone.utc).isoformat(),uploaded_through=payload['latest']['observed_at'])
                temp=DATA/'upload-status.tmp'
                temp.write_text(json.dumps(status)+'\n')
                os.replace(temp,DATA/'upload-status.json')
                logging.info('Uploaded %s archive(s) and dashboard snapshot',len(pending))
        except Exception as exc:
            # Do not log response bodies or URLs that could contain credentials.
            logging.warning('Upload delayed (%s); local readings retained',type(exc).__name__)
        time.sleep(max(5,60-(time.monotonic()-started)))


if __name__=='__main__':
    run()

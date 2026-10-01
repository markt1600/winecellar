"""Bounded persistent health history and private incident uploads; no sensor reads."""
import json, logging, os, re, shutil, subprocess, time, uuid
from pathlib import Path
from datetime import datetime, timezone
from wifi_status import wifi_status
from board_temperature import board_temperature

ROOT=Path.home()/'winecellar'
DATA=ROOT/'data'
BOX=DATA/'diagnostics'
SERVICES=['logger','upload','camera','clips','lcd','control']

def read(path):
    try: return json.loads(path.read_text())
    except (OSError,ValueError): return None

def atomic(path,value):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,separators=(',',':')))
    temp.replace(path)

def command(args,limit=16000):
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=5)
        text=r.stdout[-limit:]
        return re.sub(r'https?://\S+|Bearer\s+\S+|vercel_blob_\S+', '[redacted]',text)
    except (OSError,subprocess.SubprocessError): return 'unavailable'

def reasons(sample):
    status=sample.get('sensors') or {}
    result=[]
    for key in ('bottle_error','ambient_error'):
        if status.get(key): result.append(key)
    try:
        if time.time()-datetime.fromisoformat(status['observed_at']).timestamp()>60: result.append('logger_stale')
    except (KeyError,ValueError,TypeError): result.append('logger_unavailable')
    if sample['wifi'].get('state')!='connected': result.append('wifi_unavailable')
    try:
        stamp=(sample.get('upload') or {})['last_success']
        if time.time()-datetime.fromisoformat(stamp).timestamp()>300: result.append('upload_stale')
    except (KeyError,ValueError,TypeError): result.append('upload_unavailable')
    return result

def sample():
    return dict(at=datetime.now(timezone.utc).isoformat(),
        sensors=read(DATA/'status.json'),sensorEvent=read(DATA/'sensor-event.json'),upload=read(DATA/'upload-status.json'),
        camera=read(DATA/'camera-status.json'),wifi=wifi_status(),board=board_temperature(),
        bootId=command(['cat','/proc/sys/kernel/random/boot_id']),
        uptime=command(['cat','/proc/uptime']),memory=command(['free','-m']),
        diskFreeBytes=shutil.disk_usage(DATA).free,
        throttled=command(['vcgencmd','get_throttled']),
        probeDevices=[p.name for p in Path('/sys/bus/w1/devices').glob('28-*')])

def capture(reason,history):
    report=dict(version=1,id=f'{int(time.time()*1000):013d}-{uuid.uuid4().hex}',
        createdAt=datetime.now(timezone.utc).isoformat(),reason=reason,history=history,
        services=command(['systemctl','--user','show',*[f'winecellar-{s}.service' for s in SERVICES],
            '-p','Id','-p','ActiveState','-p','SubState','-p','NRestarts','-p','ExecMainStatus']),
        serviceLogs={s:command(['journalctl',f'_SYSTEMD_USER_UNIT=winecellar-{s}.service','--since','-10min','-n','40','--no-pager','-o','short-iso'],6000) for s in SERVICES},
        kernel=command(['journalctl','-k','--since','-10min','-n','60','--no-pager'],10000),
        networkLogs=command(['journalctl','-u','NetworkManager','--since','-10min','-n','40','--no-pager'],6000),
        ioTrace=read(Path(f'/run/user/{os.getuid()}/winecellar-io/recent.json')))
    # Never let unexpectedly large status files create unbounded reports.
    while len(json.dumps(report).encode())>450000 and len(report['history'])>1:
        report['history']=report['history'][1:]
    if len(json.dumps(report).encode())>450000: raise ValueError('Diagnostic report too large')
    atomic(BOX/(report['id']+'.json'),report)
    for path in sorted(BOX.glob('[0-9]*.json'))[:-20]: path.unlink()

def run():
    from upload import send
    logging.basicConfig(level=logging.INFO)
    BOX.mkdir(parents=True,exist_ok=True)
    history=read(BOX/'history.json') or []
    previous=None;previous_event=None;last_capture=0;last_upload=0
    while True:
        started=time.monotonic()
        try:
            current=sample();history=(history+[current])[-60:]
            atomic(BOX/'history.json',history)
            state=reasons(current)
            event=(current.get('sensorEvent') or {}).get('observed_at')
            if previous is None or state!=previous or event!=previous_event or (state and started-last_capture>=1800):
                capture('startup' if previous is None else ', '.join(state) or 'recovered / sensor transition',history)
                previous=state;last_capture=started
                previous_event=event
            # One bounded upload attempt per minute; collection continues offline.
            if started-last_upload>=60:
                last_upload=started
                for path in sorted(BOX.glob('[0-9]*.json')):
                    ack=path.with_suffix('.sent')
                    if ack.exists(): continue
                    send(read(path),'https://winecellar.marktan.ai/api/diagnostics',timeout=10)
                    ack.touch();break
                for ack in BOX.glob('*.sent'):
                    if not ack.with_suffix('.json').exists(): ack.unlink()
        except Exception as exc: logging.warning('Diagnostics delayed: %s',type(exc).__name__)
        time.sleep(max(1,30-(time.monotonic()-started)))

if __name__=='__main__': run()

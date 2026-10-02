"""Root-owned, timer-driven Wi-Fi recovery; never reboots the Pi."""
import json, os, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone

STATE=Path('/var/lib/winecellar-wifi-recovery/state.json')
LOG=STATE.with_name('events.json')
PROFILE='netplan-wlan0-markt1600'

def run(*args,timeout=15):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout,
            env={**os.environ,'LC_ALL':'C'})
        return p.returncode,p.stdout.strip()
    except (OSError,subprocess.SubprocessError): return -1,''

def write(path,data):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data));tmp.replace(path)

def event(action,**details):
    try: entries=json.loads(LOG.read_text())
    except (OSError,ValueError): entries=[]
    entries.append(dict(at=datetime.now(timezone.utc).isoformat(),action=action,**details))
    write(LOG,entries[-100:])
    print(action,details,flush=True)

def decision(state,now,connected):
    if connected:
        return {},'recovered' if state.get('since') is not None else None
    state=dict(state)
    state.setdefault('since',now)
    if now-state['since']<300 or now<state.get('next',0): return state,None
    action='radio_reset' if not state.get('stage') else 'driver_reload'
    state.update(stage=1,next=now+(300 if action=='radio_reset' else 1800))
    return state,action

def recover(action):
    # A radio toggle is a soft reset. Reloading brcmfmac recreates the Wi-Fi
    # interface and reprobes the chip; neither is a full board power cycle.
    try:
        off,_=run('/usr/bin/nmcli','radio','wifi','off')
        event('radio_off',result=off)
        if action=='driver_reload':
            code,_=run('/usr/sbin/modprobe','-r','brcmfmac',timeout=20)
            event('driver_unload',result=code)
        time.sleep(2)
    finally:
        if action=='driver_reload':
            code,_=run('/usr/sbin/modprobe','brcmfmac',timeout=20)
            event('driver_load',result=code)
        code,_=run('/usr/bin/nmcli','radio','wifi','on')
        event('radio_on',result=code)
    code,_=run('/usr/bin/nmcli','--wait','25','connection','up',PROFILE,'ifname','wlan0',timeout=30)
    event('connection_attempt',result=code)

def main():
    code,raw=run('/usr/bin/nmcli','-g','GENERAL.STATE','device','show','wlan0')
    connected=code==0 and raw.split(' ',1)[0]=='100'
    radio_code,radio=run('/usr/bin/nmcli','radio','wifi')
    if '--check' in sys.argv:
        print(json.dumps(dict(connected=connected,state=raw,radio=radio)));return
    STATE.parent.mkdir(parents=True,exist_ok=True)
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    try: old=json.loads(STATE.read_text())
    except (OSError,ValueError): old={}
    if old.get('boot')!=boot: old={}
    # Respect an intentionally disabled radio; no changes for mere internet outages.
    if radio_code!=0 or radio!='enabled':
        write(STATE,dict(boot=boot));return
    state,action=decision(old,time.monotonic(),connected)
    state['boot']=boot;write(STATE,state)
    if action:
        event(action,networkState=raw or 'interface unavailable')
        if action!='recovered': recover(action)

if __name__=='__main__': main()

"""Poll owner-authorized reboot requests; never execute arbitrary cloud commands."""
import json,os,time,subprocess,logging
from pathlib import Path
from datetime import datetime,timezone
from upload import send
ROOT=Path.home()/'winecellar'
STATE=ROOT/'data/reboot-handled.json'
HELPER='/usr/local/sbin/winecellar-reboot'
URL='https://winecellar.marktan.ai/api/reboot/device'
def eligible(command,handled,boot_id,now=None):
 if not command or command.get('status')!='queued' or command.get('bootId')!=boot_id:return False
 if handled and handled.get('id')==command.get('id'):return False
 return datetime.fromisoformat(command['expiresAt'].replace('Z','+00:00'))>(now or datetime.now(timezone.utc))
def persist(value):
 STATE.parent.mkdir(parents=True,exist_ok=True)
 temp=STATE.with_suffix('.tmp')
 with temp.open('w') as f:
  json.dump(value,f);f.flush();os.fsync(f.fileno())
 os.replace(temp,STATE)
 fd=os.open(str(STATE.parent),os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
def run():
 logging.basicConfig(level=logging.INFO)
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 try:handled=json.loads(STATE.read_text())
 except FileNotFoundError:handled=None
 while True:
  try:
   ready=Path(HELPER).exists() and subprocess.run(['/usr/bin/sudo','-n','-l',HELPER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
   command=send(dict(bootId=boot,ready=ready,handled=handled),URL).get('command')
   if ready and eligible(command,handled,boot):
    # Persist before invoking the helper: the same request can never trigger a reboot loop.
    handled=dict(id=command['id'],status='accepted');persist(handled)
    result=subprocess.run(['/usr/bin/sudo','-n',HELPER],capture_output=True,timeout=15)
    handled['status']='scheduled' if result.returncode==0 else 'failed';persist(handled)
    send(dict(bootId=boot,ready=ready,handled=handled),URL)
  except Exception as e:logging.warning('Reboot control delayed (%s)',type(e).__name__)
  time.sleep(15)
if __name__=='__main__':run()

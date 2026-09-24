"""RAM-backed H264 segments plus the Raspberry Pi native low-resolution motion stage."""
import collections,json,logging,os,queue,shutil,signal,subprocess,threading,time,uuid
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/'winecellar'
SPOOL=ROOT/'camera/spool'
BUFFER=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))/'winecellar-buffer'
STATUS=ROOT/'data/camera-status.json'
PRE=5.0
POST=5.0
MAX=20.0
FPS=15

def utc(t): return datetime.fromtimestamp(t,timezone.utc).isoformat(timespec='milliseconds')
def atomic(path,data):
 temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data));os.replace(temp,path)

def command(config):
 return ['rpicam-vid','--nopreview','--timeout','0','--width','1280','--height','720','--framerate',str(FPS),'--bitrate','800000','--codec','h264','--inline','--intra',str(FPS),'--segment','1000','--lores-width','128','--lores-height','96','--post-process-file',str(config),'-o',str(BUFFER/'segment%09d.h264')]

def main():
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
 SPOOL.mkdir(parents=True,exist_ok=True);BUFFER.mkdir(parents=True,exist_ok=True)
 for p in BUFFER.glob('segment*.h264'):p.unlink()
 config=ROOT/'camera/motion.json'
 if not config.exists():atomic(config,{'motion_detect':{'roi_x':0.05,'roi_y':0.05,'roi_width':0.9,'roi_height':0.9,'difference_m':0.1,'difference_c':15,'region_threshold':0.02,'frame_period':5,'hskip':2,'vskip':2,'verbose':1}})
 events=queue.Queue();motion=False;last_motion=0;active=None;ring=collections.deque();seen=set();last_status=0;last_frame=time.monotonic();start=last_frame;offset=time.time()-start;blocked=False;closing=False;last_saved=None
 process=subprocess.Popen(command(config),stderr=subprocess.PIPE,stdout=subprocess.DEVNULL,text=True,bufsize=1)
 def reader():
  for line in process.stderr:
   if 'Motion detected' in line:events.put((time.monotonic(),True))
   elif 'Motion stopped' in line:events.put((time.monotonic(),False))
   elif 'ERROR' in line:logging.warning('Camera: %s',line.strip())
 threading.Thread(target=reader,daemon=True).start()
 def stop(*args):
  nonlocal closing
  closing=True
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 def begin(trigger,kind='motion'):
  if not ring:return None
  selected=[s for s in ring if s[2]>=trigger-PRE]
  if not selected:return None
  epoch=offset+trigger;ident=f'{9999999999999-int(epoch*1000):013d}-{uuid.uuid4().hex}'
  partial=SPOOL/(ident+'.part');stream=partial.open('wb')
  for s in selected:stream.write(s[3])
  return dict(id=ident,file=stream,partial=partial,start=selected[0][1],end=selected[-1][2],last=selected[-1][0],trigger=trigger,kind=kind)
 def finish(continued=False):
  nonlocal active,last_saved
  if not active:return
  a=active;a['file'].flush();os.fsync(a['file'].fileno());a['file'].close()
  raw=SPOOL/(a['id']+'.h264');os.replace(a['partial'],raw)
  atomic(SPOOL/(a['id']+'.json'),dict(version=1,id=a['id'],kind=a['kind'],startedAt=utc(offset+a['start']),endedAt=utc(offset+a['end']),triggeredAt=utc(offset+min(a['trigger'],a['end'])),continued=continued))
  last_saved=utc(time.time());logging.info('Saved %s clip, %.1fs',a['kind'],a['end']-a['start']);active=None
 try:
  while not closing:
   now=time.monotonic()
   if process.poll() is not None:raise RuntimeError('Camera process exited')
   while not events.empty():
    stamp,state=events.get();motion=state
    if state:last_motion=stamp
   if motion:last_motion=now
   paths=sorted(BUFFER.glob('segment*.h264'))
   # Only consume closed segments; the final file is still being encoded.
   for path in paths[:-1]:
    if path.name in seen:continue
    ended=path.stat().st_mtime-offset
    began=ring[-1][2] if ring else ended-1.0
    data=path.read_bytes();segment=(path.name,began,ended,data)
    ring.append(segment);seen.add(path.name);last_frame=now
    if active and path.name>active['last']:
     active['file'].write(data);active['end']=ended;active['last']=path.name
    path.unlink()
   while ring and ring[0][2]<now-PRE-2:ring.popleft()
   # Bound bookkeeping independently of runtime length.
   if len(seen)>100:seen={s[0] for s in ring}
   if now-last_frame>12:raise RuntimeError('Camera stopped producing frames')
   if now-last_status>=10:
    free=shutil.disk_usage(SPOOL).free;spool_bytes=sum(p.stat().st_size for p in SPOOL.iterdir() if p.is_file())
    blocked=free<1024**3 or spool_bytes>512*1024**2
    temp=int(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000
    atomic(STATUS,dict(observedAt=utc(time.time()),state='storage_full' if blocked else 'recording' if active else 'watching',motion=motion,queuedClips=len(list(SPOOL.glob('*.json'))),lastSavedAt=last_saved,temperatureC=temp,width=1280,height=720,fps=FPS,preRollSeconds=PRE,postRollSeconds=POST))
    last_status=now
    if temp>=78:raise RuntimeError('Camera paused due to high Pi temperature')
   if now-start<8:
    time.sleep(.1);continue # Allow exposure to settle and fill the pre-roll buffer.
   test=ROOT/'camera/test-trigger'
   if test.exists() and not active and not blocked:
    test.unlink();active=begin(now,'test');last_motion=now
   if not active and motion and not blocked:active=begin(now)
   if active:
    if active['end']-active['start']>=MAX:
     finish(continued=motion or now-last_motion<POST)
     if not blocked and (motion or now-last_motion<POST):active=begin(now)
    elif not motion and active['end']>=last_motion+POST:finish()
   time.sleep(.1)
 finally:
  process.terminate()
  try:process.wait(timeout=8)
  except subprocess.TimeoutExpired:process.kill();process.wait()
  if active:finish()
  atomic(STATUS,dict(observedAt=utc(time.time()),state='stopped'))
  for path in BUFFER.glob('segment*.h264'):path.unlink()

if __name__=='__main__':main()

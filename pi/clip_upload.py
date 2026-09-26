"""Remux (without re-encoding), sign and upload queued clips. No Blob key on Pi."""
import base64,json,logging,os,struct,subprocess,tempfile,time,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from clip_queue import queue_lock,prune_locked,records,remove_clip
ROOT=Path.home()/'winecellar'
SPOOL=ROOT/'camera/spool'
STATUS=ROOT/'data/camera-upload-status.json'

def once():
 # Take a private copy before releasing the queue lock. Retention may then remove
 # this clip while a slow network upload is in flight without racing ffmpeg.
 with queue_lock(SPOOL):
  prune_locked(SPOOL)
  pending=records(SPOOL)
  if not pending:return
  record=pending[0]
  meta=json.loads(record.read_text());raw=record.with_suffix('.h264');mp4=record.with_suffix('.mp4')
  chosen=mp4 if mp4.exists() else raw
  duration=(datetime.fromisoformat(meta['endedAt'].replace('Z','+00:00'))-datetime.fromisoformat(meta['startedAt'].replace('Z','+00:00'))).total_seconds()
  if chosen.stat().st_size>3850000 or not 0<duration<=35:
   remove_clip(SPOOL,record.stem);logging.warning('Discarded oversized or invalid-duration clip %s',record.stem);return
  media=mp4.read_bytes() if mp4.exists() else None
  source=raw.read_bytes() if media is None else None
 with tempfile.TemporaryDirectory(prefix='winecellar-upload-') as scratch:
  if media is None:
   source_path=Path(scratch)/'source.h264';source_path.write_bytes(source)
   output=Path(scratch)/'clip.mp4'
   subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-fflags','+genpts','-r','15','-i',str(source_path),'-c:v','copy','-an','-movflags','+faststart',str(output)],check=True,timeout=60)
   if output.stat().st_size>3850000:
    with queue_lock(SPOOL):remove_clip(SPOOL,record.stem)
    logging.warning('Discarded oversized remuxed clip %s',record.stem);return
   media=output.read_bytes()
  if len(media)>3850000:raise RuntimeError('Clip exceeds upload size limit')
  info=json.dumps(meta,separators=(',',':')).encode();body=struct.pack('>I',len(info))+info+media
  stamp=str(int(time.time()*1000))
  with tempfile.NamedTemporaryFile() as message:
   message.write(stamp.encode()+b'\n'+body);message.flush()
   sig=subprocess.check_output(['openssl','pkeyutl','-sign','-rawin','-inkey',str(ROOT/'keys/upload.pem'),'-in',message.name],stderr=subprocess.DEVNULL)
  req=urllib.request.Request('https://winecellar.marktan.ai/api/clips',data=body,method='POST',headers={'Content-Type':'application/octet-stream','X-Cellar-Time':stamp,'X-Cellar-Signature':base64.b64encode(sig).decode()})
  with urllib.request.urlopen(req,timeout=90) as response:
   result=json.load(response)
   if response.status!=200 or result.get('ok') is not True or result.get('id')!=meta['id']:raise RuntimeError('No acknowledgement')
  status=dict(lastSuccess=datetime.now(timezone.utc).isoformat(),lastClipId=meta['id'],lastClipKind=meta['kind'])
  temp=STATUS.with_suffix('.tmp');temp.write_text(json.dumps(status));os.replace(temp,STATUS)
  # Acknowledged uploads or queue retention can remove a completed clip.
  with queue_lock(SPOOL):remove_clip(SPOOL,record.stem)
  logging.info('Uploaded %s clip %s',meta['kind'],meta['id'])

def main():
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s');SPOOL.mkdir(parents=True,exist_ok=True)
 while True:
  try:once();time.sleep(5)
  except Exception as exc:logging.warning('Clip upload delayed (%s%s); newest 10 clips retained',type(exc).__name__,f' HTTP {exc.code}' if isinstance(exc,urllib.error.HTTPError) else '');time.sleep(30)
if __name__=='__main__':main()

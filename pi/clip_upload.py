"""Remux (without re-encoding), sign and upload queued clips. No Blob key on Pi."""
import base64,json,logging,os,struct,subprocess,tempfile,time,urllib.request
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path.home()/'winecellar'
SPOOL=ROOT/'camera/spool'
STATUS=ROOT/'data/camera-upload-status.json'

def once():
 for record in sorted(SPOOL.glob('*.json'),reverse=True):
  meta=json.loads(record.read_text());raw=record.with_suffix('.h264');mp4=record.with_suffix('.mp4')
  if not mp4.exists():
   temp=record.with_suffix('.encoding.mp4')
   subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-fflags','+genpts','-r','15','-i',str(raw),'-c:v','copy','-an','-movflags','+faststart',str(temp)],check=True,timeout=60)
   os.replace(temp,mp4)
  if mp4.stat().st_size>3850000:raise RuntimeError('Clip exceeds upload size limit; retained locally')
  info=json.dumps(meta,separators=(',',':')).encode();body=struct.pack('>I',len(info))+info+mp4.read_bytes()
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
  # Remove local queue only after the server confirms durable private storage.
  record.unlink();raw.unlink(missing_ok=True);mp4.unlink()
  logging.info('Uploaded %s clip %s',meta['kind'],meta['id'])

def main():
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s');SPOOL.mkdir(parents=True,exist_ok=True)
 while True:
  try:once();time.sleep(5)
  except Exception as exc:logging.warning('Clip upload delayed (%s); queued files retained',type(exc).__name__);time.sleep(30)
if __name__=='__main__':main()

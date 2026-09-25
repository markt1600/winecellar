"""A shared, bounded completed-clip queue. In-progress .part files are untouched."""
import fcntl,re
from contextlib import contextmanager
from pathlib import Path
LIMIT=10
ID=re.compile(r'^\d{13}-[a-f0-9]{32}$')
@contextmanager
def queue_lock(spool):
 spool.mkdir(parents=True,exist_ok=True)
 with (spool/'.queue.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  try:yield
  finally:fcntl.flock(lock,fcntl.LOCK_UN)
def records(spool):
 # Inverted timestamp IDs sort newest first, independent of file modification time.
 return sorted(p for p in spool.glob('*.json') if ID.fullmatch(p.stem))
def remove_clip(spool,ident):
 if not ID.fullmatch(ident):raise ValueError('Invalid clip ID')
 for suffix in ('.json','.h264','.mp4','.encoding.mp4'):
  (spool/(ident+suffix)).unlink(missing_ok=True)
def prune_locked(spool):
 pending=records(spool);expired=pending[LIMIT:]
 for p in expired:remove_clip(spool,p.stem)
 # Recover leftover completed media from interrupted upload/deletion, never active footage.
 live={p.stem for p in pending[:LIMIT]}
 for p in list(spool.iterdir()):
  for suffix in ('.encoding.mp4','.mp4','.h264'):
   if not p.name.endswith(suffix):continue
   ident=p.name[:-len(suffix)]
   if ID.fullmatch(ident) and ident not in live and not (spool/(ident+'.part')).exists():p.unlink(missing_ok=True)
   break
 return len(expired)
def prune_queue(spool):
 with queue_lock(spool):return prune_locked(spool)

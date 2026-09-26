"""Serialize application sensor reads and LCD writes across processes."""
from contextlib import contextmanager
import fcntl,json,os,time
from pathlib import Path
RUNTIME=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))/'winecellar-io'
# Conservative drain window for this 480x320 LCD at the configured 1 MHz.
# Framebuffer writes are deferred; returning from write() is not completion.
LCD_DRAIN_SECONDS=6.0

def trace(directory,phase,event):
 path=directory/'recent.json'
 try:entries=json.loads(path.read_text())
 except (OSError,ValueError):entries=[]
 entries.append(dict(phase=phase,event=event,pid=os.getpid(),monotonic=time.monotonic(),epoch=time.time()))
 temp=path.with_suffix('.tmp');temp.write_text(json.dumps(entries[-128:]));temp.replace(path)

@contextmanager
def hardware_access(phase,directory=None,drain_seconds=0):
 directory=Path(directory) if directory is not None else RUNTIME
 directory.mkdir(parents=True,exist_ok=True)
 with (directory/'hardware.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  try:
   trace(directory,phase,'start')
   yield
  finally:
   # Retain exclusion while an asynchronous LCD transfer drains, even on write errors.
   if drain_seconds:time.sleep(drain_seconds)
   try:trace(directory,phase,'end')
   finally:fcntl.flock(lock,fcntl.LOCK_UN)

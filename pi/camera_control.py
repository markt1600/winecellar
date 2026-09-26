"""Fixed user-service camera controls, independent of temperature logging."""
import json,subprocess,os
from datetime import datetime,timezone
UNIT='winecellar-camera.service'
def camera_state(run=subprocess.run):
 result=run(['systemctl','--user','is-enabled',UNIT],capture_output=True,text=True,timeout=10)
 state=result.stdout.strip()
 return dict(cameraReady=state in ('enabled','disabled'),cameraPaused=state=='disabled')
def set_camera_paused(paused,run=subprocess.run):
 # Disabling the camera also preserves the pause across power cycles.
 run(['systemctl','--user','disable' if paused else 'enable','--now',UNIT],check=True,capture_output=True,timeout=45)
def refresh_paused_status(root,state):
 if not state.get('cameraPaused'):return
 path=root/'data/camera-status.json'
 try:previous=json.loads(path.read_text())
 except (OSError,ValueError):previous={}
 previous.update(observedAt=datetime.now(timezone.utc).isoformat(),state='paused',motion=False)
 path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_suffix('.control.tmp');temp.write_text(json.dumps(previous));os.replace(temp,path)

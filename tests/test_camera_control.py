import sys,unittest,types,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from camera_control import camera_state,set_camera_paused,refresh_paused_status
class CameraControlTest(unittest.TestCase):
 def test_only_camera_unit_is_changed(self):
  calls=[]
  def run(args,**kwargs):calls.append(args)
  set_camera_paused(True,run);set_camera_paused(False,run)
  self.assertEqual(calls,[['systemctl','--user','disable','--now','winecellar-camera.service'],['systemctl','--user','enable','--now','winecellar-camera.service']])
 def test_paused_state_and_unknown_unit(self):
  for value,expected in [('enabled',(True,False)),('disabled',(True,True)),('not-found',(False,False))]:
   state=camera_state(lambda *a,**k:types.SimpleNamespace(stdout=value))
   self.assertEqual((state['cameraReady'],state['cameraPaused']),expected)
 def test_pause_status_retains_last_motion(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'data').mkdir();path=root/'data/camera-status.json'
   path.write_text(json.dumps(dict(lastMotionAt='before',state='watching')))
   refresh_paused_status(root,dict(cameraPaused=True))
   value=json.loads(path.read_text());self.assertEqual(value['state'],'paused');self.assertEqual(value['lastMotionAt'],'before')
if __name__=='__main__':unittest.main()

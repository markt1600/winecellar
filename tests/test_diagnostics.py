import json,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
import diagnostics as d

class DiagnosticsTests(unittest.TestCase):
 def test_failure_and_recovery(self):
  stamp=datetime.now(timezone.utc).isoformat()
  s=dict(sensors=dict(observed_at=stamp,bottle_error='missing',ambient_error=None),wifi=dict(state='connected'),upload=dict(last_success=stamp))
  self.assertEqual(d.reasons(s),['bottle_error'])
  s['sensors']['bottle_error']=None
  self.assertEqual(d.reasons(s),[])
  s['wifi']['state']='disconnected'
  s['upload']['last_success']='2020-01-01T00:00:00+00:00'
  self.assertEqual(d.reasons(s),['wifi_unavailable','upload_stale'])
 def test_reports_survive_locally_and_are_bounded(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(d,'command',return_value='test'),patch.object(d,'read',return_value=None):
   with patch.object(d,'BOX',Path(tmp)),patch.object(d.os,'getuid',return_value=1000,create=True):
    for i in range(23): d.capture('bottle_error',[dict(at=str(i))])
    files=list(Path(tmp).glob('*.json'))
    self.assertEqual(len(files),20)
    report=json.loads(files[-1].read_text())
    self.assertEqual(report['reason'],'bottle_error')
    self.assertIn('kernel',report)
    self.assertIn('networkLogs',report)

if __name__=='__main__': unittest.main()

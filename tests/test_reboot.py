import sys,types,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
# No network or privileged commands are used in these decision tests.
sys.modules.setdefault('upload',types.SimpleNamespace(send=lambda *_:None))
from reboot_control import eligible
class RebootTest(unittest.TestCase):
 def test_no_replay_expiry_or_previous_boot(self):
  now=datetime.now(timezone.utc)
  cmd=dict(id='request',bootId='boot',status='queued',expiresAt=(now+timedelta(seconds=120)).isoformat())
  self.assertTrue(eligible(cmd,None,'boot',now))
  self.assertTrue(eligible({**cmd,'action':'shutdown'},None,'boot',now))
  self.assertFalse(eligible({**cmd,'action':'arbitrary-command'},None,'boot',now))
  self.assertFalse(eligible({**cmd,'action':'shutdown'},dict(id='request'),'boot',now))
  self.assertFalse(eligible(cmd,dict(id='request',status='accepted'),'boot',now))
  self.assertFalse(eligible(cmd,None,'different-boot',now))
  self.assertFalse(eligible(cmd,None,'boot',now+timedelta(seconds=121)))
  self.assertFalse(eligible({**cmd,'status':'completed'},None,'boot',now))
if __name__=='__main__':unittest.main()

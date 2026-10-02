import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from wifi_recovery import decision

class RecoveryTests(unittest.TestCase):
 def test_escalation_and_cooldown(self):
  s,a=decision({},10,False);self.assertIsNone(a)
  s,a=decision(s,309,False);self.assertIsNone(a)
  s,a=decision(s,310,False);self.assertEqual(a,'radio_reset')
  s,a=decision(s,609,False);self.assertIsNone(a)
  s,a=decision(s,610,False);self.assertEqual(a,'driver_reload')
  s,a=decision(s,2409,False);self.assertIsNone(a)
  s,a=decision(s,2410,False);self.assertEqual(a,'driver_reload')
 def test_recovery_clears_stale_failure(self):
  s,a=decision(dict(since=1,stage=1,next=900),100,True)
  self.assertEqual((s,a),({},'recovered'))
  s,a=decision(s,200,False);self.assertIsNone(a)
  self.assertEqual(s['since'],200)
 def test_healthy_no_action(self):
  self.assertEqual(decision({},100,True),({},None))

if __name__=='__main__':unittest.main()

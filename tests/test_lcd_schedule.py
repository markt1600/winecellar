import sys,unittest
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from lcd import dim_schedule,effective_dim
class ScheduleTest(unittest.TestCase):
 def test_boundaries_in_singapore(self):
  for stamp,expected in [('2026-09-26T21:59:59+08:00',False),('2026-09-26T22:00:00+08:00',True),('2026-09-27T06:59:59+08:00',True),('2026-09-27T07:00:00+08:00',False),('2026-09-26T14:00:00+00:00',True)]:
   self.assertEqual(dim_schedule(datetime.fromisoformat(stamp))[0],expected)
 def test_override_expires_at_next_boundary_not_midnight(self):
  at=lambda s:datetime.fromisoformat(s)
  night=at('2026-09-26T23:00:00+08:00')
  saved=dict(dim=False,dimOverrideWindow=dim_schedule(night)[1])
  self.assertFalse(effective_dim(saved,at('2026-09-27T02:00:00+08:00')))
  self.assertTrue(effective_dim(saved,at('2026-09-27T22:00:00+08:00')))
  saved=dict(dim=True,dimOverrideWindow=dim_schedule(at('2026-09-26T12:00:00+08:00'))[1])
  self.assertTrue(effective_dim(saved,at('2026-09-26T13:00:00+08:00')))
  self.assertFalse(effective_dim(saved,at('2026-09-27T07:00:00+08:00')))
 def test_old_setting_does_not_disable_schedule(self):
  self.assertTrue(effective_dim(dict(dim=False),datetime.fromisoformat('2026-09-26T23:00:00+08:00')))
if __name__=='__main__':unittest.main()

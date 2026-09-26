import sys,unittest
from pathlib import Path
from collections import deque
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from recording_limits import *
class LimitsTest(unittest.TestCase):
 def test_future_timestamps_cannot_grow_ring_unbounded(self):
  ring=deque()
  for i in range(1000):
   ring.append((str(i),100000+i,100001+i,b'x'*200000));trim_ring(ring,100)
   self.assertLessEqual(len(ring),MAX_RING_SEGMENTS)
   self.assertLessEqual(sum(len(s[3]) for s in ring),MAX_RING_BYTES)
 def test_append_checks_duration_and_bytes_before_writing(self):
  a=dict(start=100,end=110,bytes=3400000,born=105)
  self.assertFalse(can_append(a,('next',110,111,b'x'*100001)))
  self.assertFalse(can_append(a,('next',120,121,b'x')))
  self.assertTrue(can_append(a,('next',110,111,b'x'*100000)))
 def test_elapsed_watchdog_survives_bad_segment_time(self):
  a=dict(start=100000,end=100001,bytes=10,born=100)
  self.assertFalse(deadline_reached(a,119));self.assertTrue(deadline_reached(a,120))
if __name__=='__main__':unittest.main()

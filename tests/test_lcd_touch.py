import sys,unittest,tempfile,json
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from lcd_touch import calibrate,transform,hit,TARGETS,Touch,CHECK
from lcd import period_start
class TouchTest(unittest.TestCase):
 def test_rotated_and_reversed_sensor_axes(self):
  raw=[(4000-y*10,200+x*7) for x,y in TARGETS]
  matrix=calibrate(raw)
  for x,y in [(63,290),(248,280),(414,290),(240,160)]:
   actual=transform(matrix,4000-y*10,200+x*7)
   self.assertAlmostEqual(actual[0],x);self.assertAlmostEqual(actual[1],y)
 def test_fourth_tap_retry_preserves_calibration_and_saves_on_success(self):
  with tempfile.TemporaryDirectory() as directory:
   touch=Touch.__new__(Touch);touch.path=Path(directory)/'calibration.json'
   touch.matrix=None;touch.points=[];touch.feedback=None;touch.error=None
   raw=lambda p:(4000-p[1]*10,200+p[0]*7)
   for target in TARGETS:self.assertFalse(touch.calibration_tap(raw(target)))
   self.assertFalse(touch.calibration_tap(raw((50,50))))
   self.assertEqual(len(touch.points),3);self.assertIsNone(touch.matrix)
   self.assertTrue(touch.calibration_tap(raw(CHECK)))
   self.assertEqual(json.loads(touch.path.read_text()),list(touch.matrix))
 def test_bad_calibration(self):
  with self.assertRaises(ValueError):calibrate([(1,1),(2,2),(3,3)])
 def test_only_bottle_targets(self):
  self.assertEqual(hit(63,290),'dim');self.assertEqual(hit(248,280),'period');self.assertEqual(hit(414,290),'reboot')
  self.assertIsNone(hit(414,180));self.assertIsNone(hit(330,290))
 def test_calendar_windows(self):
  now=datetime(2024,2,29,tzinfo=timezone.utc)
  self.assertEqual(period_start(now,'1y'),datetime(2023,2,28,tzinfo=timezone.utc))
  self.assertEqual(period_start(datetime(2026,3,31,tzinfo=timezone.utc),'1mo'),datetime(2026,2,28,tzinfo=timezone.utc))
if __name__=='__main__':unittest.main()

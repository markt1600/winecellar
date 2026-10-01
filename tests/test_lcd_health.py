import sqlite3, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pi'))
from lcd_health import failed_readings, wifi_label

class HealthTests(unittest.TestCase):
 def test_failed_samples_and_empty_window(self):
  db=sqlite3.connect(':memory:')
  db.execute('CREATE TABLE readings(observed_at TEXT,bottle_c REAL,ambient_c REAL,humidity_pct REAL,bottle_error TEXT,ambient_error TEXT)')
  db.executemany('INSERT INTO readings VALUES(?,?,?,?,?,?)', [('2026-10-01T00:00',None,16,50,'missing',None),('2026-10-01T00:10',13,None,None,None,'checksum'),('2026-09-30T20:00',None,None,None,'old','old')])
  self.assertEqual(failed_readings(db,'2026-10-01','2026-10-02'),dict(bottle_c=1,ambient_c=1,humidity_pct=1))
  self.assertIsNone(failed_readings(db,'2026-10-02','2026-10-03')['bottle_c'])
  db.close()
 def test_wifi_states(self):
  self.assertEqual(wifi_label({'state':'disconnected'}),'Wi-Fi: Disconnected')
  self.assertEqual(wifi_label(None),'Wi-Fi: Status unavailable')
  self.assertIn('44% (-76 dBm)',wifi_label(dict(state='connected',signalPercent=44,signalDbm=-76,ssid='cellar')))

if __name__=='__main__': unittest.main()

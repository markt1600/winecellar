import sys
import sqlite3
import unittest
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from snapshot import snapshot

class SnapshotTest(unittest.TestCase):
    def test_failed_readings_do_not_distort_extremes_and_windows(self):
        db=sqlite3.connect(':memory:')
        db.row_factory=sqlite3.Row
        db.execute('CREATE TABLE readings (id INTEGER PRIMARY KEY, observed_at TEXT, bottle_c REAL, ambient_c REAL, humidity_pct REAL, bottle_error TEXT, ambient_error TEXT)')
        rows=[(1,'2026-09-22T11:00:00.000+00:00',4,5,40,None,None),
              (2,'2026-09-24T10:30:00.000+00:00',12,13,60,None,None),
              (3,'2026-09-24T10:30:10.000+00:00',14,None,None,None,'checksum'),
              (4,'2026-09-24T10:30:20.000+00:00',None,15,70,'missing',None)]
        db.executemany('INSERT INTO readings VALUES (?,?,?,?,?,?,?)',rows)
        result=snapshot(db,datetime(2026,9,24,11,tzinfo=timezone.utc))
        s=result['windows']['1h']['stats']
        self.assertEqual(s['bottle_c']['min'],12)
        self.assertEqual(s['bottle_c']['max'],14)
        self.assertEqual(s['bottle_c']['avg'],13)
        self.assertEqual(s['ambient_c']['count'],2)
        self.assertEqual(s['ambient_c']['maxAt'],rows[3][1])
        self.assertEqual(result['allTime']['bottle_c']['min'],4)
        self.assertIsNone(result['latest']['bottle_c'])
        self.assertEqual(result['windows']['1h']['samples'],3)
        self.assertEqual(result['windows']['1mo']['stats']['bottle_c']['count'],3)
        self.assertLessEqual(len(result['windows']['1y']['points']),367)

if __name__=='__main__':
    unittest.main()

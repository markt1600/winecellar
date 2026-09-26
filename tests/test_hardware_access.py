import json,multiprocessing,sys,tempfile,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from hardware_access import hardware_access

def worker(directory,name,drain):
 for _ in range(3):
  with hardware_access(name,directory,drain):time.sleep(.015)

class AccessTest(unittest.TestCase):
 def test_processes_never_overlap_including_drain(self):
  with tempfile.TemporaryDirectory() as directory:
   jobs=[multiprocessing.Process(target=worker,args=(directory,name,drain)) for name,drain in [('sensors',0),('lcd',.08)]]
   for job in jobs:job.start()
   for job in jobs:job.join(5);self.assertEqual(job.exitcode,0)
   events=json.loads((Path(directory)/'recent.json').read_text());self.assertEqual(len(events),12)
   for start,end in zip(events[::2],events[1::2]):
    self.assertEqual(start['event'],'start');self.assertEqual(end['event'],'end');self.assertEqual(start['phase'],end['phase'])
    if start['phase']=='lcd':self.assertGreaterEqual(end['monotonic']-start['monotonic'],.08)
 def test_exception_releases_lock(self):
  with tempfile.TemporaryDirectory() as directory:
   with self.assertRaises(RuntimeError):
    with hardware_access('failure',directory):raise RuntimeError('test')
   with hardware_access('next',directory):pass
if __name__=='__main__':unittest.main()

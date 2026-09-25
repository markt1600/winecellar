import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from clip_queue import prune_queue,records,queue_lock,remove_clip
class ClipQueueTest(unittest.TestCase):
 def test_newest_ten_and_active_clip_preserved(self):
  with tempfile.TemporaryDirectory() as tmp:
   spool=Path(tmp)
   def ident(i):return str(8200000000000+i)+'-'+'a'*32
   for i in range(12):
    for suffix in ('.json','.h264','.mp4','.encoding.mp4'):(spool/(ident(i)+suffix)).write_text('data')
   active=ident(20);(spool/(active+'.part')).write_text('active')
   (spool/'unrelated.txt').write_text('keep')
   (spool/(ident(30)+'.mp4')).write_text('orphan')
   self.assertEqual(prune_queue(spool),2)
   self.assertEqual([p.stem for p in records(spool)],[ident(i) for i in range(10)])
   for i in (10,11,30):self.assertFalse((spool/(ident(i)+'.mp4')).exists())
   self.assertTrue((spool/(active+'.part')).exists());self.assertTrue((spool/'unrelated.txt').exists())
   self.assertEqual(prune_queue(spool),0)
   with queue_lock(spool):remove_clip(spool,ident(0));remove_clip(spool,ident(0))
   self.assertEqual(len(records(spool)),9)
   self.assertRaises(ValueError,remove_clip,spool,'../outside')
if __name__=='__main__':unittest.main()

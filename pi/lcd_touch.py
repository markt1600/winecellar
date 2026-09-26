"""Raw Linux touchscreen input and a saved three-point affine calibration."""
import json,logging,os,select,statistics,struct,threading
from pathlib import Path
EVENT=struct.Struct('@llHHi')
TARGETS=((40,50),(440,50),(240,270))
CHECK=(240,160)

def transform(matrix,x,y):
 return (matrix[0]*x+matrix[1]*y+matrix[2],matrix[3]*x+matrix[4]*y+matrix[5])

def calibrate(points):
 (x1,y1),(x2,y2),(x3,y3)=points
 det=x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2)
 if abs(det)<1000:raise ValueError('Calibration points too close')
 def solve(z):
  a=(z[0]*(y2-y3)+z[1]*(y3-y1)+z[2]*(y1-y2))/det
  b=(z[0]*(x3-x2)+z[1]*(x1-x3)+z[2]*(x2-x1))/det
  c=(z[0]*(x2*y3-x3*y2)+z[1]*(x3*y1-x1*y3)+z[2]*(x1*y2-x2*y1))/det
  return a,b,c
 return (*solve([p[0] for p in TARGETS]),*solve([p[1] for p in TARGETS]))

class Touch:
 def __init__(self,queue,path):
  self.queue=queue;self.path=path;self.matrix=None;self.points=[];self.error=None
  try:
   matrix=json.loads(path.read_text())
   if len(matrix)==6 and all(isinstance(v,(int,float)) for v in matrix):self.matrix=matrix
  except (OSError,ValueError,TypeError):pass
  devices=[p for p in Path('/sys/class/input').glob('event*') if 'ADS7846' in (p/'device/name').read_text()]
  if not devices:self.error='Touchscreen not found';return
  try:self.fd=os.open('/dev/input/'+devices[0].name,os.O_RDONLY|os.O_NONBLOCK)
  except OSError:self.error='Touch input unavailable';return
  threading.Thread(target=self.read,daemon=True).start()
 def read(self):
  x=y=None;down=False;samples=[];buffer=b''
  try:
   while True:
    if not select.select([self.fd],[],[],1)[0]:continue
    buffer+=os.read(self.fd,EVENT.size*64)
    while len(buffer)>=EVENT.size:
     _,_,kind,code,value=EVENT.unpack(buffer[:EVENT.size]);buffer=buffer[EVENT.size:]
     if kind==3 and code==0:x=value
     elif kind==3 and code==1:y=value
     elif kind==1 and code==330:
      if value:down=True;samples=[]
      else:
       if down and samples:self.queue.put((statistics.median(p[0] for p in samples),statistics.median(p[1] for p in samples)))
       down=False;samples=[]
     elif kind==0 and code==0 and down and x is not None and y is not None:samples.append((x,y))
  except OSError:logging.exception('Touch input stopped')
  finally:os.close(self.fd)
 def calibration_tap(self,point):
  if len(self.points)<3:
   self.points.append(point);return False
  try:
   matrix=calibrate(self.points);x,y=transform(matrix,*point)
   if abs(x-CHECK[0])>35 or abs(y-CHECK[1])>35:raise ValueError('Check missed')
   self.path.parent.mkdir(parents=True,exist_ok=True)
   temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(matrix));temp.replace(self.path)
   self.matrix=matrix;return True
  except (ValueError,OSError):self.points=[];return False

def hit(x,y):
 if not 215<=y<=319:return None
 for name,left,right in [('dim',45,96),('period',224,275),('reboot',390,440)]:
  if left<=x<=right:return name
 return None

"""Low-overhead local LCD dashboard; reads the existing SQLite log."""
import json,time,sqlite3,struct,queue,subprocess,logging,calendar
from pathlib import Path
from datetime import datetime,timezone,timedelta
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
from snapshot import statistics,iso,previous_month
from lcd_touch import Touch,transform,hit,TARGETS,CHECK
PERIODS=("1h","24h","1mo","1y")
LABELS={"1h":"1H","24h":"24H","1mo":"1 MONTH","1y":"1 YEAR"}
ROOT=Path.home()/'winecellar';DATA=ROOT/'data'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(n):return ImageFont.truetype(FONT,n)
def fmt(v):return '--' if v is None else f'{v:.1f}'
def draw_dashboard(row, day, alltime, session=None, now=None, period="24h"):
 now=now or datetime.now(timezone.utc)
 im=Image.new('RGB',(480,320),'#111a20');d=ImageDraw.Draw(im)
 def text(x,y,s,size=14,color='#edf2f4'):d.text((x,y),s,font=font(size),fill=color)
 def center(x,y,s,size=14,color='#edf2f4'):
  f=font(size);d.text((x-d.textlength(s,font=f)/2,y),s,font=f,fill=color)
 text(12,7,'Cellar @ BH',17,'#e6c699')
 stamp=now.astimezone().strftime('%d %b  %H:%M')
 text(480-12-d.textlength(stamp,font=font(13)),10,stamp,13,'#a5b1b7')
 d.line((12,32,468,32),fill='#4b493d')
 # The photographic asset is cached and resized once, not processed every refresh.
 art=bottle_art()
 if art:im.paste(art,((480-art.width)//2,320-art.height))
 if row is None:
  center(240,80,'Waiting for new readings',21)
  center(240,118,'Monitoring starts with the next sample',13,'#a5b1b7')
  return im
 for x,k,title,unit,color in [(80,'bottle_c','IN BOTTLE','°C','#e6c699'),(240,'ambient_c','AMBIENT','°C','#9edbd7'),(400,'humidity_pct','HUMIDITY','% RH','#c7cfe7')]:
  center(x,42,title,13,color)
  center(x,59,fmt(row[k])+unit,30)
  center(x,102,LABELS[period]+' LOW / HIGH',10,'#a5b1b7')
  center(x,117,fmt(day[k]['min'])+' / '+fmt(day[k]['max']),15,color)
  center(x,141,'PERIOD LOW / HIGH' if session else 'ALL-TIME LOW / HIGH',10,'#a5b1b7')
  center(x,155,fmt(alltime[k]['min'])+' / '+fmt(alltime[k]['max']),15,color)
 for x in (160,320):d.line((x,43,x,172),fill='#2b3b43')
 age=(now-datetime.fromisoformat(row['observed_at'])).total_seconds()
 health='READINGS STALE' if age>30 else 'CHECK SENSORS' if row['bottle_error'] or row['ambient_error'] else 'LIVE'
 color='#ffb27d' if health!='LIVE' else '#9bd6b0'
 d.ellipse((12,183,17,188),fill=color);text(23,177,health,11,color)
 if session and session.get('location'):
  label=session['location']
  while d.textlength(label,font=font(11))>290:label=label[:-2]+'…'
  text(468-d.textlength(label,font=font(11)),177,label,11,'#a5b1b7')
 return im

from functools import lru_cache
@lru_cache(maxsize=1)
def bottle_art():
 path=Path(__file__).parent/'assets'/'bottles.png'
 if not path.exists():return None
 with Image.open(path) as source:
  art=source.convert('RGB');art.thumbnail((480,128),Image.Resampling.LANCZOS)
 return art

def render(period="24h"):
 db=sqlite3.connect(f'file:{DATA / "readings.sqlite3"}?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  try:session=json.loads((DATA/'monitoring-session.json').read_text())
  except (OSError,ValueError):session=None
  cutoff=iso(datetime.fromisoformat(session['startedAt'].replace('Z','+00:00'))) if session else ''
  row=db.execute('SELECT * FROM readings WHERE observed_at>=? ORDER BY id DESC LIMIT 1',(cutoff,)).fetchone()
  if not row:return draw_dashboard(None,None,None,session)
  now=datetime.now(timezone.utc);end=iso(now);start=max(cutoff,iso(period_start(now,period)))
  return draw_dashboard(row,statistics(db,start,end),statistics(db,cutoff,end),session,now,period)
 finally:db.close()

def framebuffer():
 for p in Path('/sys/class/graphics').glob('fb*'):
  if 'ili9486' in (p/'name').read_text().lower():return p
 raise RuntimeError('LCD framebuffer not found')
def period_start(now,period):
 if period=='1h':return now-timedelta(hours=1)
 if period=='24h':return now-timedelta(days=1)
 if period=='1mo':return previous_month(now)
 return now.replace(year=now.year-1,day=min(now.day,calendar.monthrange(now.year-1,now.month)[1]))

def controls(im,period,dim):
 d=ImageDraw.Draw(im)
 # Small paper labels replace only the three selected bottles' labels.
 for x,y,lines in [(63,280,('DIM','ON' if dim else 'OFF')),(248,270,('PERIOD',period.upper())),(414,279,('RE','BOOT'))]:
  d.rounded_rectangle((x-12,y,x+12,y+25),radius=2,fill='#e9d7ad',outline='#806b45')
  for i,line in enumerate(lines):
   f=font(6 if len(line)>4 else 8)
   d.text((x-d.textlength(line,font=f)/2,y+2+i*11),line,font=f,fill='#30271d')
 return im

def overlay(im,title,detail,buttons=False):
 d=ImageDraw.Draw(im);d.rounded_rectangle((30,65,450,195),radius=8,fill='#111a20',outline='#e6c699',width=2)
 for y,line,size in [(78,title,18),(108,detail,12)]:
  f=font(size);d.text((240-d.textlength(line,font=f)/2,y),line,font=f,fill='#edf2f4')
 if buttons:
  for x,label,color in [(60,'Cancel','#34444c'),(260,'Confirm reboot','#713e32')]:
   d.rounded_rectangle((x,145,x+160,184),radius=5,fill=color)
   f=font(14);d.text((x+80-d.textlength(label,font=f)/2,155),label,font=f,fill='white')
 return im

def main():
 logging.basicConfig(level=logging.INFO)
 fb=framebuffer();w,h=map(int,(fb/'virtual_size').read_text().strip().split(','));bpp=int((fb/'bits_per_pixel').read_text())
 if (w,h,bpp)!=(480,320,16):raise RuntimeError(f'Unexpected LCD format {w}x{h} {bpp}bpp')
 events=queue.Queue();touch=Touch(events,DATA/'touch-calibration.json')
 settings=DATA/'lcd-controls.json'
 try:saved=json.loads(settings.read_text())
 except (OSError,ValueError):saved={}
 period=saved.get('period','24h');period=period if period in PERIODS else '24h';dim=saved.get('dim') is True
 confirm=False;confirm_until=0;notice='';notice_until=0;next_refresh=0
 while True:
  now=time.monotonic()
  if confirm and now>confirm_until:confirm=False;next_refresh=0
  if notice and now>notice_until:notice='';next_refresh=0
  if now>=next_refresh:
   im=controls(render(period),period,dim)
   if not touch.matrix and not touch.error:
    im=Image.new('RGB',(480,320),'#111a20');d=ImageDraw.Draw(im)
    d.text((70,100),'Touch calibration',font=font(22),fill='#e6c699')
    d.text((55,135),'Tap once, then wait for the next cross',font=font(17),fill='white')
    d.text((130,185),f'Step {len(touch.points)+1} of 4',font=font(16),fill='#a5b1b7')
    if touch.feedback:d.text((35,215),touch.feedback,font=font(13),fill='#ffb27d')
    x,y=TARGETS[len(touch.points)] if len(touch.points)<3 else CHECK
    d.ellipse((x-13,y-13,x+13,y+13),outline='#e6c699',width=2)
    d.line((x-20,y,x+20,y),fill='white',width=2);d.line((x,y-20,x,y+20),fill='white',width=2)
   elif confirm:overlay(im,'Reboot the Pi?','Readings pause; restart begins in one minute.',True)
   elif notice:overlay(im,notice,'Saved readings are retained.')
   elif touch.error:
    ImageDraw.Draw(im).text((24,202),touch.error,font=font(12),fill='#ffb27d')
   if dim and touch.matrix and not confirm and not notice:im=ImageEnhance.Brightness(im).enhance(0.30)
   pixels=bytearray()
   for r,g,b in im.getdata():pixels.extend(struct.pack('<H',((r>>3)<<11)|((g>>2)<<5)|(b>>3)))
   with open('/dev/'+fb.name,'r+b',buffering=0) as output:output.write(pixels)
   # At 1 MHz a full LCD SPI transfer takes about 2.5 seconds after the write.
   # Do not accept a tap against the preceding target while the panel catches up.
   if not touch.matrix or confirm:time.sleep(3)
   # Ignore taps made before the newly drawn confirmation/calibration screen was visible.
   while not events.empty():events.get_nowait()
   next_refresh=time.monotonic()+10 if touch.matrix else float('inf')
  try:point=events.get(timeout=0.2)
  except queue.Empty:continue
  if not touch.matrix:
   touch.calibration_tap(point);next_refresh=0;continue
  x,y=transform(touch.matrix,*point)
  if confirm:
   if 145<=y<=184 and 60<=x<=220:confirm=False;next_refresh=0
   elif 145<=y<=184 and 260<=x<=420:
    confirm=False
    try:
     result=subprocess.run(['/usr/bin/sudo','-n','/usr/local/sbin/winecellar-reboot'],capture_output=True,timeout=15)
     notice='Reboot scheduled' if result.returncode==0 else 'Reboot unavailable'
    except (OSError,subprocess.TimeoutExpired):notice='Reboot unavailable'
    notice_until=time.monotonic()+65;next_refresh=0
   continue
  if notice:continue
  action=hit(x,y)
  if action=='reboot':confirm=True;confirm_until=time.monotonic()+30
  elif action=='dim':dim=not dim
  elif action=='period':period=PERIODS[(PERIODS.index(period)+1)%len(PERIODS)]
  else:continue
  if action in ('dim','period'):
   settings.parent.mkdir(parents=True,exist_ok=True)
   temp=settings.with_suffix('.tmp');temp.write_text(json.dumps(dict(period=period,dim=dim)));temp.replace(settings)
  next_refresh=0
if __name__=='__main__':main()

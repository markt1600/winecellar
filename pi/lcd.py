"""Low-overhead local LCD dashboard; reads the existing SQLite log."""
import json,time,sqlite3,struct
from pathlib import Path
from datetime import datetime,timezone,timedelta
from PIL import Image,ImageDraw,ImageFont
from snapshot import statistics,iso
ROOT=Path.home()/'winecellar';DATA=ROOT/'data'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(n):return ImageFont.truetype(FONT,n)
def fmt(v):return '--' if v is None else f'{v:.1f}'
def draw_dashboard(row, day, alltime, session=None, now=None):
 now=now or datetime.now(timezone.utc)
 im=Image.new('RGB',(480,320),'#111a20');d=ImageDraw.Draw(im)
 def text(x,y,s,size=14,color='#edf2f4'):d.text((x,y),s,font=font(size),fill=color)
 def center(x,y,s,size=14,color='#edf2f4'):
  f=font(size);d.text((x-d.textlength(s,font=f)/2,y),s,font=f,fill=color)
 text(12,7,'THE WINE CELLAR',17,'#e6c699')
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
  center(x,102,'24H LOW / HIGH',10,'#a5b1b7')
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

def render():
 db=sqlite3.connect(f'file:{DATA / "readings.sqlite3"}?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  try:session=json.loads((DATA/'monitoring-session.json').read_text())
  except (OSError,ValueError):session=None
  cutoff=iso(datetime.fromisoformat(session['startedAt'].replace('Z','+00:00'))) if session else ''
  row=db.execute('SELECT * FROM readings WHERE observed_at>=? ORDER BY id DESC LIMIT 1',(cutoff,)).fetchone()
  if not row:return draw_dashboard(None,None,None,session)
  now=datetime.now(timezone.utc);end=iso(now);start=max(cutoff,iso(now-timedelta(days=1)))
  return draw_dashboard(row,statistics(db,start,end),statistics(db,cutoff,end),session,now)
 finally:db.close()

def framebuffer():
 for p in Path('/sys/class/graphics').glob('fb*'):
  if 'ili9486' in (p/'name').read_text().lower():return p
 raise RuntimeError('LCD framebuffer not found')
def main():
 fb=framebuffer();w,h=map(int,(fb/'virtual_size').read_text().strip().split(','));bpp=int((fb/'bits_per_pixel').read_text())
 if (w,h,bpp)!=(480,320,16):raise RuntimeError(f'Unexpected LCD format {w}x{h} {bpp}bpp')
 while True:
  im=render();pixels=bytearray()
  for r,g,b in im.getdata():pixels.extend(struct.pack('<H',((r>>3)<<11)|((g>>2)<<5)|(b>>3)))
  with open('/dev/'+fb.name,'r+b',buffering=0) as output:output.write(pixels)
  time.sleep(10)
if __name__=='__main__':main()

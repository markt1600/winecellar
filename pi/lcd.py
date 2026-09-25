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
def render():
 im=Image.new('RGB',(480,320),'#111a20');d=ImageDraw.Draw(im)
 def text(x,y,s,size=18,color='#edf2f4'):d.text((x,y),s,font=font(size),fill=color)
 text(14,8,'WINE CELLAR',22);text(300,13,datetime.now().strftime('%d %b %H:%M'),15)
 db=sqlite3.connect(f'file:{DATA / "readings.sqlite3"}?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  try:session=json.loads((DATA/'monitoring-session.json').read_text())
  except (OSError,ValueError):session=None
  cutoff=iso(datetime.fromisoformat(session['startedAt'].replace('Z','+00:00'))) if session else ''
  row=db.execute('SELECT * FROM readings WHERE observed_at>=? ORDER BY id DESC LIMIT 1',(cutoff,)).fetchone()
  if not row:text(14,100,'Waiting for new readings...',22);return im
  end=iso(datetime.now(timezone.utc));start=max(cutoff,iso(datetime.now(timezone.utc)-timedelta(days=1)))
  day=statistics(db,start,end);alltime=statistics(db,cutoff,end)
  text(160,53,'BOTTLE',18,'#f1bb83');text(322,53,'AMBIENT',18,'#85d4df')
  for x,k in [(160,'bottle_c'),(322,'ambient_c')]:
   text(x,80,fmt(row[k])+' C',30)
   text(x,155,fmt(day[k]['min'])+' / '+fmt(day[k]['max']),20)
   text(x,196,fmt(alltime[k]['min'])+' / '+fmt(alltime[k]['max']),20)
  text(14,115,'Humidity: '+fmt(row['humidity_pct'])+' % RH',21)
  text(14,156,'24h low/high',16)
  text(14,197,'Period low/high' if session else 'All-time low/high',15)
  d.line((14,235,466,235),fill='#49606c')
  age=(datetime.now(timezone.utc)-datetime.fromisoformat(row['observed_at'])).total_seconds()
  health='STALE READINGS' if age>30 else 'Check sensor wiring' if row['bottle_error'] or row['ambient_error'] else 'Sensors recording'
  text(14,249,health,18,'#ffb27d' if age>30 or row['bottle_error'] or row['ambient_error'] else '#95dfb1')
  text(14,281,(session.get('location') or 'New monitoring period')[:42] if session else 'Local readings - cloud sync runs separately',14)
  return im
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

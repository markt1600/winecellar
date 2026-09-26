"""Read the Pi's internal SoC temperature independently of camera state."""
from pathlib import Path
from datetime import datetime,timezone
import math

def board_temperature():
 value=None
 try:
  reading=float(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000
  if math.isfinite(reading) and -40<=reading<=150:value=reading
 except (OSError,ValueError):pass
 return dict(temperatureC=value,observedAt=datetime.now(timezone.utc).isoformat())

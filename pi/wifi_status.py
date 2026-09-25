"""Read active Wi-Fi status without rescanning or exposing network credentials."""
import os,subprocess
from pathlib import Path
from datetime import datetime,timezone

def active_network(output):
 for line in output.splitlines():
  if not line.startswith('*:'):continue
  name,sep,strength=line[2:].rpartition(':')
  if not sep:continue
  signal=int(strength)
  if not 0<=signal<=100:raise ValueError('Invalid signal')
  # nmcli terse output escapes colons and backslashes in SSIDs.
  chars=[];escape=False
  for ch in name:
   if escape:chars.append(ch);escape=False
   elif ch=='\\':escape=True
   else:chars.append(ch)
  if escape:chars.append('\\')
  return dict(ssid=''.join(chars),signalPercent=signal)
 return None

def wifi_status():
 result=dict(observedAt=datetime.now(timezone.utc).isoformat(),state='unavailable')
 try:
  output=subprocess.check_output(['/usr/bin/nmcli','-t','-e','yes','-f','IN-USE,SSID,SIGNAL','device','wifi','list','ifname','wlan0','--rescan','no'],text=True,timeout=3,stderr=subprocess.DEVNULL,env={**os.environ,'LC_ALL':'C'})
  active=active_network(output)
  if not active:return {**result,'state':'disconnected'}
  result.update(active,state='connected')
  try:
   for line in Path('/proc/net/wireless').read_text().splitlines():
    if line.split(':')[0].strip()=='wlan0':
     dbm=float(line.split(':',1)[1].split()[2].rstrip('.'))
     if -150<dbm<0:result['signalDbm']=round(dbm)
  except (OSError,ValueError,IndexError):pass
 except (OSError,ValueError,subprocess.SubprocessError):pass
 return result

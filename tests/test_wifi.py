import sys,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pi'))
from wifi_status import active_network,wifi_status
class WifiTest(unittest.TestCase):
 def test_active_only_and_escaped_name(self):
  self.assertEqual(active_network(' :other:99\n*:Cellar\\: BH\\\\Main:77'),{'ssid':'Cellar: BH\\Main','signalPercent':77})
  self.assertIsNone(active_network(' :other:99'))
  self.assertRaises(ValueError,active_network,'*:bad:101')
 def test_wifi_failure_does_not_block_sensor_upload(self):
  with patch('wifi_status.subprocess.check_output',side_effect=subprocess.TimeoutExpired('nmcli',3)):
   self.assertEqual(wifi_status()['state'],'unavailable')
if __name__=='__main__':unittest.main()

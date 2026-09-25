export default function WifiStatus({wifi,now}){
 if(!wifi)return <div className="wifi-status">🛜 Wi-Fi status awaiting the next Pi upload</div>;
 const stale=!Number.isFinite(Date.parse(wifi.observedAt))||now-Date.parse(wifi.observedAt)>180000;
 const signal=Number.isFinite(wifi.signalPercent)?wifi.signalPercent:null;
 const quality=signal===null?'':signal>=75?'Excellent':signal>=50?'Good':signal>=25?'Fair':'Weak';
 const at=new Date(wifi.observedAt).toLocaleString('en-SG',{timeZone:'Asia/Singapore',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'});
 return <div className={'wifi-status'+(stale?' warning':'')}><span aria-hidden="true">🛜</span>{' '}<span>{stale?'Last reported Wi-Fi':'Pi Wi-Fi'}: <strong>{wifi.state==='connected'?(wifi.ssid||'Hidden network'):wifi.state==='disconnected'?'Not connected':'Status unavailable'}</strong></span>{wifi.state==='connected'&&signal!==null&&<span> · {signal}% · {quality}{Number.isFinite(wifi.signalDbm)?` (${wifi.signalDbm} dBm)`:''}</span>}<span className="wifi-time">{stale?'Stale report · ':''}Updated {at} SGT</span></div>;
}

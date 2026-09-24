'use client';
import {useState} from 'react';
export default function MonitoringReset(){
 const [open,setOpen]=useState(false),[location,setLocation]=useState(''),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[id,setId]=useState(null);
 async function reset(){
  setBusy(true);setMessage('');const requestId=id||crypto.randomUUID();setId(requestId);
  try{const r=await fetch('/api/monitoring',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:requestId,location})});const d=await r.json();if(!r.ok)throw Error(d.error||'Unable to reset monitoring.');window.location.reload();}
  catch(e){setMessage(e.message);setBusy(false);}
 }
 return <section className="monitoring-reset"><h2>Start a new monitoring period</h2><p>Moving the sensors to a new location? Restart temperature and humidity charts, 24-hour highs/lows and monitoring-period highs/lows. Earlier readings stay saved. Camera recordings continue unchanged.</p>{!open?<button onClick={()=>{setOpen(true);setId(null);}}>Reset monitoring…</button>:<div><label>New location (optional; shown publicly)<input maxLength={80} value={location} disabled={busy} onChange={e=>setLocation(e.target.value)}/></label><p>Start from now? The Pi usually applies this within a minute. If it is offline, the reset waits until it reconnects.</p><button disabled={busy} onClick={reset}>{busy?'Starting…':'Confirm new period'}</button>{' '}<button disabled={busy} onClick={()=>setOpen(false)}>Cancel</button></div>}{message&&<p className="error" role="alert">{message}</p>}</section>;
}

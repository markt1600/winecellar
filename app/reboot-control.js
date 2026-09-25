'use client';
import {useEffect,useState} from 'react';
export default function RebootControl(){
 const [state,setState]=useState(null),[confirm,setConfirm]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[id,setId]=useState(null);
 async function load(){try{const r=await fetch('/api/reboot',{cache:'no-store'});if(!r.ok)throw Error('Device status unavailable.');setState(await r.json());}catch(e){setState(null);setError(e.message);}}
 useEffect(()=>{load();const t=setInterval(load,15000);return()=>clearInterval(t);},[]);
 async function reboot(){setBusy(true);setError('');const requestId=id||crypto.randomUUID();setId(requestId);try{const r=await fetch('/api/reboot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:requestId})});const d=await r.json();if(!r.ok)throw Error(d.error);setConfirm(false);await load();}catch(e){setError(e.message);}finally{setBusy(false);}}
 const c=state?.command;const expired=c?.status==='queued'&&Date.parse(c.expiresAt)<Date.now();
 const message=expired?'Request expired; the Pi did not act on it.':({queued:'Reboot requested. Waiting for the Pi…',scheduled:'Restart scheduled. The Pi will reboot shortly, then reconnect.',completed:'Pi restarted and reconnected.',failed:'The Pi could not schedule the restart. Check its reboot setup.'}[c?.status]);
 const pending=c&&['queued','scheduled'].includes(c.status)&&Date.now()-Date.parse(c.createdAt)<180000;
 return <section className="monitoring-reset"><h2>Pi controls</h2><p>Restart the cellar Pi. Readings and camera recording pause briefly while it reboots. Saved history is retained.</p>{message&&<p role="status">{message}</p>}{!state?.ready&&!pending&&<p className="muted">Reboot unavailable: the Pi is offline or its one-time setup is incomplete.</p>}{confirm?<div><p>Reboot now? The Pi schedules a restart in one minute after receiving the request.</p><button disabled={busy} onClick={reboot}>{busy?'Requesting…':'Confirm reboot'}</button>{' '}<button disabled={busy} onClick={()=>setConfirm(false)}>Cancel</button></div>:<button disabled={!state?.ready||pending} onClick={()=>{setConfirm(true);setId(null);setError('');}}>Reboot Pi…</button>}{error&&<p className="error" role="alert">{error}</p>}</section>;
}

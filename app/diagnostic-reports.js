'use client';
import {useState} from 'react';
export default function DiagnosticReports(){
 const [reports,setReports]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 async function load(){setBusy(true);setError('');try{const r=await fetch('/api/diagnostics',{cache:'no-store'});if(!r.ok)throw Error(r.status===401?'Sign in to view private diagnostics.':'Diagnostics unavailable.');setReports((await r.json()).reports);}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <div><p><button onClick={load} disabled={busy}>{busy?'Loading…':'View diagnostic reports'}</button></p>{error&&<p role="alert">{error}</p>}{reports&&<><p>Latest 20 private reports. Downloads include recent sensor, Wi-Fi and service health. Reports upload after connectivity returns.</p>{reports.length===0?<p>No reports uploaded yet. The diagnostic recorder must be installed on the Pi.</p>:<ul>{reports.map(r=><li key={r.id}><a href={`/api/diagnostics?id=${encodeURIComponent(r.id)}`}>Download report — {new Date(Number(r.id.slice(0,13))).toLocaleString()}</a></li>)}</ul>}</>}</div>;
}

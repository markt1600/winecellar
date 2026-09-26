'use client';
import {useEffect,useState} from 'react';
import ClipPlayer from './clip-player';
const date=v=>v?new Date(v).toLocaleString('en-SG',{timeZone:'Asia/Singapore'}):'—';
export default function Activity(){
 const [camera,setCamera]=useState(null),[upload,setUpload]=useState(null);
 useEffect(()=>{let alive=true;async function check(){try{const r=await fetch('/api/camera-status',{cache:'no-store'});if(!r.ok)return;const d=await r.json();if(alive){setCamera(d.camera);setUpload(d.upload);}}catch{}}check();const timer=setInterval(check,30000);return()=>{alive=false;clearInterval(timer);};},[]);

 const [clips,setClips]=useState([]),[cursor,setCursor]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 async function load(next){setBusy(true);try{const r=await fetch('/api/clips'+(next?'?cursor='+encodeURIComponent(next):''),{cache:'no-store'});if(!r.ok)throw Error('Recordings are temporarily unavailable.');const d=await r.json();setClips(old=>next?[...old,...d.clips]:d.clips);setCursor(d.cursor);setError('');}catch(e){setError(e.message);}finally{setBusy(false);}}
 useEffect(()=>{load();},[]);
 const stale=!camera?.observedAt||Date.now()-Date.parse(camera.observedAt)>180000;
 const state=stale?'Waiting for camera status':({paused:'Paused by you',watching:'Watching for motion',recording:'Recording motion',storage_full:'Recording paused: local storage is full',stopped:'Camera stopped'}[camera.state]||'Camera unavailable');
 return <section className="camera"><div className="toolbar"><h2>Cellar activity</h2><button disabled={busy} onClick={()=>load()}>Refresh recordings</button></div><p><strong>{state}</strong>{!stale&&' · 720p / 15 fps · 5 seconds before and after motion'}</p><p className="muted">Only the newest 10 recordings are kept; older videos are automatically deleted.</p><p className="muted">{camera?.queuedClips??0} clips queued locally · Last upload {date(upload?.lastSuccess)}. Continuous activity is split into overlapping clips. Buffer boundaries may add up to two extra seconds.</p>{error&&<p className="error">{error}</p>}{!clips.length&&!error&&<p>No uploaded recordings yet.</p>}<div className="clips">{clips.map(c=><article key={c.id}><h3>{date(c.triggeredAt)}</h3><p>{c.kind==='test'?'Setup test':'Motion detected'} · {c.durationSeconds.toFixed(1)} seconds{c.continued?' · Activity continues':''}</p><ClipPlayer clip={c}/></article>)}</div>{cursor&&<button disabled={busy} onClick={()=>load(cursor)}>Older recordings</button>}</section>;
}

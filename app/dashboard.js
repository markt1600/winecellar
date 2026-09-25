'use client';
import {useEffect,useState} from 'react';
import {readingHealth,targetStatus} from '../lib/reading-health.mjs';

const fields=[['bottle_c','Bottle','°C','#9b382b'],['ambient_c','Ambient','°C','#35767e'],['humidity_pct','Humidity','% RH','#6c6442']];
const fmt=v=>typeof v==='number'&&Number.isFinite(v)?v.toFixed(1):'—';
const time=v=>v?new Date(v).toLocaleString('en-SG',{timeZone:'Asia/Singapore',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'—';
const readingTime=v=>v?new Date(v).toLocaleString('en-SG',{timeZone:'Asia/Singapore',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'})+' SGT':'No successful reading in this period';
function Chart({points,keys,start,end,range,bucketSeconds}){
  const values=points.flatMap(p=>keys.flatMap(k=>[p[k],p[k+'_min'],p[k+'_max']])).filter(Number.isFinite);
  if(!values.length)return <p className="empty">No valid readings for this period.</p>;
  const min=Math.min(...values,...(range||[]))-1,max=Math.max(...values,...(range||[]))+1;
  const x=t=>50+(Date.parse(t)-Date.parse(start))/(Date.parse(end)-Date.parse(start))*900;
  const y=v=>225-(v-min)/(max-min)*190;
  const step=bucketSeconds*1000;
  return <svg viewBox="0 0 980 270" role="img" aria-label={`${keys.includes('humidity_pct')?'Humidity':'Temperature'} history`}>
    {range&&<rect x="50" y={y(range[1])} width="900" height={y(range[0])-y(range[1])} fill="#6a8053" opacity=".10"/>}
    {[0,.25,.5,.75,1].map(f=><g key={f}><line x1="50" x2="950" y1={225-f*190} y2={225-f*190} stroke="#d1c6b1"/><text x="42" y={230-f*190} textAnchor="end">{(min+(max-min)*f).toFixed(1)}</text></g>)}
    {keys.map(k=>{let prev=null;const d=points.map(p=>{const v=p[k];if(!Number.isFinite(v)){prev=null;return '';}const connected=prev!==null&&Date.parse(p.at)-prev<=step*1.8;prev=Date.parse(p.at);return `${connected?'L':'M'}${x(p.at).toFixed(1)},${y(v).toFixed(1)}`;}).join(' ');const color=fields.find(f=>f[0]===k)[3];return <g key={k}><path d={d} fill="none" stroke={color} strokeWidth="2.5"/>{points.map((p,i)=>Number.isFinite(p[k])?<g key={i}><line x1={x(p.at)} x2={x(p.at)} y1={y(p[k+'_min']??p[k])} y2={y(p[k+'_max']??p[k])} stroke={color} opacity=".4"/><circle cx={x(p.at)} cy={y(p[k])} r={points.length<15?3:1} fill={color}><title>{`${time(p.at)} · ${fmt(p[k])}`}</title></circle></g>:null)}</g>;})}
    <text x="50" y="255">{time(start)}</text><text x="950" y="255" textAnchor="end">{time(end)}</text>
  </svg>;
}
export default function Dashboard({initialData=null,refresh=true}){
 const [data,setData]=useState(initialData),[error,setError]=useState(''),[period,setPeriod]=useState('24h');
 const [now,setNow]=useState(()=>Date.now());
 useEffect(()=>{const id=setInterval(()=>setNow(Date.now()),10000);return()=>clearInterval(id);},[]);
 const [targets,setTargets]=useState({low:12,high:16,humidityLow:50,humidityHigh:75});
 useEffect(()=>{try{const saved=JSON.parse(localStorage.getItem('cellar-targets'));if(saved&&Object.values(saved).every(Number.isFinite))setTargets(saved);}catch{}},[]);
 useEffect(()=>{if(!refresh)return;let live=true;async function load(){try{const r=await fetch('/api/readings',{cache:'no-store'});if(!r.ok)throw Error(r.status===401?'Your session has expired. Sign in at marktan.ai, then reload.':'Cloud readings are temporarily unavailable.');const d=await r.json();if(live){setData(d);setError('');}}catch(e){if(live)setError(e.message);}}load();const id=setInterval(load,30000);return()=>{live=false;clearInterval(id);};},[refresh]);
 function target(k,value){const next={...targets,[k]:Number(value)};setTargets(next);localStorage.setItem('cellar-targets',JSON.stringify(next));}
 if(!data||data.empty)return <section className="gate"><h2>{error?'Connection unavailable':data?.resetPending?'Starting a new monitoring period':data?.empty?'Waiting for the first upload':'Loading your cellar…'}</h2><p>{error||(data?.resetPending?'Waiting for the Pi to upload readings from the new period. Previous readings remain saved.':'Readings appear here after the Pi uploads them.')}</p></section>;
 const w=data.windows[period],latest=data.latest,age=now-Date.parse(latest.observed_at),stale=age>180000;
 const t=latest.ambient_c,h=latest.humidity_pct;
 const a=Number.isFinite(t)&&Number.isFinite(h)&&h>0?Math.log(h/100)+17.62*t/(243.12+t):null;
 const dew=a!==null?243.12*a/(17.62-a):null;
 const validTargets=targets.low<targets.high&&targets.humidityLow<targets.humidityHigh;
 function exportCsv(){const names=['at',...fields.flatMap(([k])=>[k,k+'_min',k+'_max'])];const csv=[names.join(','),...w.points.map(p=>names.map(k=>p[k]??'').join(','))].join('\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));const link=document.createElement('a');link.href=url;link.download=`winecellar-${period}-chart.csv`;link.click();URL.revokeObjectURL(url);}
 return <><div className="journal"><span className={stale?'warning':''}>{stale?'● LOGGER DATA STALE':fields.some(([k])=>!Number.isFinite(latest[k]))?'● LOGGER ONLINE · SENSOR ISSUE':'● RECENT READINGS'} · {time(latest.observed_at)}</span><span>Cloud sync · {time(data.generatedAt)}</span></div>{error&&<p className="error">{error}</p>}
 <section className="current">{fields.map(([k,label,unit,color])=>{const health=readingHealth(data,k,now);const range=k==='humidity_pct'?[targets.humidityLow,targets.humidityHigh]:[targets.low,targets.high];const outside=targetStatus(latest[k],...range);return <article key={k}><h2 style={{color}}>{label}</h2><strong className={outside?'outside-target':undefined}>{fmt(latest[k])}<small>{unit}</small></strong><p className={health.status==='Current reading'?'':'warning'}>{health.status}</p>{outside&&<p className="warning target-note">{outside} · {range[0]}–{range[1]} {unit}</p>}<div className="reading-times"><span>Last successful reading</span><time dateTime={health.lastAt||undefined}>{readingTime(health.lastAt)}</time><span>Latest attempt: {readingTime(latest.observed_at)}</span></div><dl><dt>24h low / high</dt><dd>{fmt(data.windows['24h'].stats[k]?.min)} / {fmt(data.windows['24h'].stats[k]?.max)}</dd><dt>{data.monitoringSession?'Period low / high':'All-time low / high'}</dt><dd>{fmt(data.allTime[k]?.min)} / {fmt(data.allTime[k]?.max)}</dd></dl></article>;})}</section>
 {data.monitoringSession&&<p className="muted">Monitoring period: {data.monitoringSession.location||'New location'} · Started {time(data.monitoringSession.startedAt)}</p>}<div className="toolbar"><h2>Cellar history</h2><nav aria-label="History period">{[['1h','1 hour'],['24h','24 hours'],['1mo','1 month'],['1y','1 year']].map(([k,label])=><button key={k} aria-pressed={period===k} onClick={()=>setPeriod(k)}>{label}</button>)}</nav><button onClick={exportCsv}>Export chart CSV</button></div>
 <p className="muted">{time(w.start)} — {time(w.end)} · {w.samples.toLocaleString()} samples · {w.bucketSeconds}s chart intervals. Longer intervals show averages with min–max whiskers. Gaps are not interpolated.</p>
 <div className="legend"><span style={{color:fields[0][3]}}>● Bottle</span><span style={{color:fields[1][3]}}>● Ambient</span></div><Chart points={w.points} keys={['bottle_c','ambient_c']} start={w.start} end={w.end} bucketSeconds={w.bucketSeconds} range={validTargets?[targets.low,targets.high]:null}/>
 <div className="stats">{fields.map(([k,label,unit])=>{const s=w.stats[k]||{};return <article key={k}><h3>{label} · selected period</h3><div><span>Minimum</span><b>{fmt(s.min)} {unit}</b><small>{time(s.minAt)}</small></div><div><span>Maximum</span><b>{fmt(s.max)} {unit}</b><small>{time(s.maxAt)}</small></div><div><span>Average / spread</span><b>{fmt(s.avg)} / {fmt(s.max===null?null:s.max-s.min)}</b><small>{s.count??0} valid readings</small></div></article>;})}</div>
 <h2>Humidity</h2><Chart points={w.points} keys={['humidity_pct']} start={w.start} end={w.end} bucketSeconds={w.bucketSeconds} range={validTargets?[targets.humidityLow,targets.humidityHigh]:null}/>
 <section className="insights"><article><h3>Bottle − air</h3><strong>{fmt(Number.isFinite(latest.bottle_c)&&Number.isFinite(t)?latest.bottle_c-t:null)} °C</strong><p>Shows the bottle’s lag behind air changes.</p></article><article><h3>Estimated dew point</h3><strong>{fmt(dew)} °C</strong><p>Surfaces at or below this temperature may collect condensation.</p></article><article><h3>Recording health</h3><strong>{latest.bottle_error||latest.ambient_error?'Check sensors':stale?'Stale':'Recording'}</strong><p>Logging began {time(data.recordingSince)}. Missing values are excluded from statistics.</p></article></section>
 <details><summary>Display target ranges</summary><p>Illustrative starting ranges; adjust for your cellar. Values outside these ranges turn red. Saved in this browser; no notifications are sent.</p><div className="targets">{[['low','Temperature low °C'],['high','Temperature high °C'],['humidityLow','Humidity low %'],['humidityHigh','Humidity high %']].map(([k,label])=><label key={k}>{label}<input type="number" value={targets[k]} onChange={e=>target(k,e.target.value)}/></label>)}</div>{!validTargets&&<p className="error">Each low must be below its high.</p>}</details>
 </>;
}

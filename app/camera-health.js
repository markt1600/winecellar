export default function CameraHealth({camera,now}){
 const stale=!camera?.observedAt||now-Date.parse(camera.observedAt)>180000||!Number.isFinite(Date.parse(camera.observedAt));
 const labels={watching:'Watching for motion',recording:'Recording',storage_full:'Paused - storage limit',stopped:'Stopped',unavailable:'Unavailable'};
 const label=camera?(labels[camera.state]||'Unavailable'):'Waiting for status';
 const motionAt=camera?.lastMotionAt&&Number.isFinite(Date.parse(camera.lastMotionAt))?new Date(camera.lastMotionAt).toLocaleString('en-SG',{timeZone:'Asia/Singapore',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'}):null;
 const at=camera?.observedAt?new Date(camera.observedAt).toLocaleString('en-SG',{timeZone:'Asia/Singapore',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'}):null;
 return <div className={'wifi-status'+(stale||['stopped','storage_full','unavailable'].includes(camera?.state)?' warning':'')}><span aria-hidden="true">📷</span>{' '}Camera: <strong>{stale&&camera?'Last reported: ':''}{label}</strong>{Number.isSafeInteger(camera?.queuedClips)&&<span> · {camera.queuedClips} / 10 clips queued</span>}<span className="wifi-time">Last motion detected: {motionAt?`${motionAt} SGT`:"No detection recorded yet"}</span><span className="wifi-time">{stale?'Awaiting fresh status. ':''}{at?`Updated ${at} SGT`:'Status appears after the next Pi upload.'}</span></div>;
}

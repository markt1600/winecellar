// Preview extraction runs only in the signed-in viewer's browser.
export function previewTime(clip,duration){
 const offset=(Date.parse(clip.triggeredAt)-Date.parse(clip.startedAt))/1000;
 const end=Number.isFinite(duration)?Math.max(0,duration-0.1):0;
 return Math.min(end,Math.max(0,Number.isFinite(offset)?offset:0));
}
export function extractPoster(source,clip,signal){
 return new Promise((resolve,reject)=>{
  if(signal.aborted){reject(new DOMException('Cancelled','AbortError'));return;}
  const video=document.createElement('video');let settled=false,timer;
  const cleanup=()=>{clearTimeout(timer);signal.removeEventListener('abort',abort);video.onloadedmetadata=video.onloadeddata=video.onseeked=video.onerror=null;video.removeAttribute('src');video.load();};
  const finish=(error,value)=>{if(settled)return;settled=true;cleanup();error?reject(error):resolve(value);};
  const abort=()=>finish(new DOMException('Cancelled','AbortError'));
  const capture=()=>{
   try{
    if(!video.videoWidth||!video.videoHeight)throw Error('No video frame');
    const canvas=document.createElement('canvas');canvas.width=Math.min(640,video.videoWidth);canvas.height=Math.round(canvas.width*video.videoHeight/video.videoWidth);
    canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);
    finish(null,canvas.toDataURL('image/jpeg',0.82));
   }catch(e){finish(e);}
  };
  video.muted=true;video.playsInline=true;video.preload='auto';
  video.onloadedmetadata=()=>{const target=previewTime(clip,video.duration);if(target>0){video.onseeked=capture;video.currentTime=target;}else if(video.readyState>=2)capture();else video.onloadeddata=capture;};
  video.onerror=()=>finish(Error('Preview unavailable'));
  signal.addEventListener('abort',abort,{once:true});
  timer=setTimeout(()=>finish(Error('Preview timed out')),25000);
  video.src=source;video.load();
 });
}
// Decode at most two previews at once; do not download all ten videos together.
let running=0;const queue=[];
function drain(){while(running<2&&queue.length){const job=queue.shift();running++;Promise.resolve().then(job.run).then(job.resolve,job.reject).finally(()=>{running--;drain();});}}
export function queuePoster(source,clip,signal){return new Promise((resolve,reject)=>{queue.push({run:()=>extractPoster(source,clip,signal),resolve,reject});drain();});}

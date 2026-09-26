'use client';
import {useEffect,useRef,useState} from 'react';
import {savedPoster} from '../lib/saved-poster.mjs';
export default function ClipPlayer({clip}){
 const container=useRef(null);const [poster,setPoster]=useState(null),[status,setStatus]=useState('loading');
 const source='/api/clips/'+clip.id;
 useEffect(()=>{
  const controller=new AbortController();let started=false,objectUrl;
  setPoster(null);setStatus('loading');
  const start=()=>{if(started)return;started=true;savedPoster(source,clip,controller.signal).then(image=>{if(!controller.signal.aborted){objectUrl=URL.createObjectURL(image);setPoster(objectUrl);setStatus('ready');}},()=>{if(!controller.signal.aborted)setStatus('failed');});};
  let observer;
  if('IntersectionObserver' in window){observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){observer.disconnect();start();}},{rootMargin:'200px'});observer.observe(container.current);}else start();
  return()=>{observer?.disconnect();controller.abort();if(objectUrl)URL.revokeObjectURL(objectUrl);};
 },[source,clip.startedAt,clip.triggeredAt]);
 return <div ref={container} className="clip-player"><video controls preload="none" playsInline poster={poster||undefined} src={source} aria-label={clip.kind==='test'?'Setup test recording':'Motion recording'} onPlay={()=>setStatus('playing')}/>{status==='loading'&&<span className="clip-preview-note">Loading motion preview…</span>}{status==='failed'&&<span className="clip-preview-note">Preview unavailable · Press play to view recording</span>}</div>;
}

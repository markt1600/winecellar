import test from 'node:test';
import assert from 'node:assert/strict';
import {previewTime,extractPoster} from '../lib/video-preview.mjs';
const clip={startedAt:'2026-09-26T00:00:00Z',triggeredAt:'2026-09-26T00:00:05.500Z'};
test('preview uses actual trigger offset, clamps to playable bounds',()=>{
 assert.equal(previewTime(clip,20),5.5);
 assert.equal(previewTime(clip,4),3.9);
 assert.equal(previewTime({...clip,triggeredAt:'invalid'},20),0);
 assert.equal(previewTime(clip,Infinity),0);
});
test('extract a trigger frame without playing; release media after capture',async()=>{
 let seek,drawn=false,released=false,played=false;
 const video={duration:20,videoWidth:1280,videoHeight:720,readyState:2,removeAttribute(){released=true;},load(){if(this.src&&!released)queueMicrotask(()=>this.onloadedmetadata?.());},set currentTime(v){seek=v;queueMicrotask(()=>this.onseeked?.());},play(){played=true;}};
 const old=global.document;
 global.document={createElement:tag=>tag==='video'?video:{getContext:()=>({drawImage:()=>{drawn=true;}}),toDataURL:()=> 'data:image/jpeg;base64,preview'}};
 try{assert.equal(await extractPoster('/api/clips/example',clip,new AbortController().signal),'data:image/jpeg;base64,preview');assert.equal(seek,5.5);assert.ok(drawn);assert.ok(released);assert.equal(played,false);}finally{global.document=old;}
});
test('aborted previews do not create or load video',async()=>{
 const c=new AbortController();c.abort();await assert.rejects(extractPoster('/private',clip,c.signal),{name:'AbortError'});
});

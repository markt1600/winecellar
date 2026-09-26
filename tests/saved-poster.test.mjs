import test from 'node:test';
import assert from 'node:assert/strict';
import {savedPoster} from '../lib/saved-poster.mjs';
import {retentionPlan} from '../lib/clip-retention.mjs';
test('existing JPEG is reused without decoding video or uploading',async()=>{
 const calls=[];
 const blob=await savedPoster('/clip',{},new AbortController().signal,{fetcher:async(url)=>{calls.push(url);return new Response('jpeg');},generate:()=>assert.fail('must not decode')});
 assert.equal(await blob.text(),'jpeg');assert.deepEqual(calls,['/clip/poster']);
});
test('missing preview generates once and saves JPEG for later visits',async()=>{
 const calls=[];let generated=0;
 const blob=await savedPoster('/clip',{},new AbortController().signal,{generate:async()=>{generated++;return 'data:image/jpeg;base64,eA==';},fetcher:async(url,options)=>{
  calls.push(url);
  if(url.startsWith('data:'))return new Response('jpeg');
  if(options.method==='POST'){assert.equal(await options.body.text(),'jpeg');assert.equal(options.headers['Content-Type'],'image/jpeg');return new Response('Saved',{status:201});}
  return new Response(null,{status:404});
 }});
 assert.equal(generated,1);assert.equal(await blob.text(),'jpeg');assert.equal(calls.length,3);
});
test('authentication and storage failures never trigger video decoding',async()=>{
 for(const status of [401,503])await assert.rejects(savedPoster('/clip',{},new AbortController().signal,{fetcher:async()=>new Response(null,{status}),generate:()=>assert.fail('must not decode')}));
});
test('old thumbnails are pruned with old clips, current thumbnails remain',()=>{
 const ids=Array.from({length:12},(_,i)=>String(8200000000000+i)+'-'+'a'.repeat(32));
 const events=ids.map(id=>({pathname:`cellar/v1/events/${id}.json`}));
 const posters=ids.map(id=>({pathname:`cellar/v1/posters/${id}.jpg`}));
 assert.deepEqual(retentionPlan(events,[],posters).thumbnails,posters.slice(10).map(p=>p.pathname));
});

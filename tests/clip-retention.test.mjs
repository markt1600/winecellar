import test from 'node:test';
import assert from 'node:assert/strict';
import {retentionPlan,pruneClips} from '../lib/clip-retention.mjs';
const id=i=>String(8200000000000+i)+'-'+'a'.repeat(32);
const event=i=>({pathname:`cellar/v1/events/${id(i)}.json`});
const video=i=>({pathname:`cellar/v1/clips/${id(i)}-${'b'.repeat(64)}.mp4`});
test('keep newest ten irrespective of list order; remove old media and orphans only',()=>{
 const p=retentionPlan(Array.from({length:12},(_,i)=>event(11-i)),[...Array.from({length:12},(_,i)=>video(i)),video(99),video(-1),{pathname:'cellar/v1/dashboard.json'}]);
 assert.deepEqual(p.kept.map(b=>b.pathname),Array.from({length:10},(_,i)=>event(i).pathname));
 assert.deepEqual(p.expired,[event(10).pathname,event(11).pathname]);
 assert.deepEqual(p.media,[video(10).pathname,video(11).pathname,video(99).pathname]);
 assert.equal(retentionPlan([event(0)],[video(0)]).media.length,0);
});
test('cleanup paginates and deletes media before metadata, retry is safe',async()=>{
 const deletes=[];
 const api={list:async({prefix,cursor})=>prefix.endsWith('events/')?cursor?{blobs:[event(10)],hasMore:false}:{blobs:Array.from({length:10},(_,i)=>event(i)),hasMore:true,cursor:'next'}:{blobs:[video(10)],hasMore:false},del:async paths=>deletes.push(paths)};
 const result=await pruneClips(api);assert.equal(result.kept,10);assert.equal(result.deletedRecords,1);assert.deepEqual(deletes,[[video(10).pathname],[event(10).pathname]]);
 const failed=[];await assert.rejects(pruneClips({...api,del:async paths=>{failed.push(paths);throw Error('storage');}}));assert.equal(failed.length,1);
});

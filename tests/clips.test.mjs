import test from 'node:test';
import assert from 'node:assert/strict';
import {decodeClip,validClipId,MAX_CLIP_BYTES} from '../lib/clips.mjs';
const metadata={version:1,id:'8230000000000-'+'a'.repeat(32),kind:'motion',startedAt:'2026-09-24T10:00:00Z',triggeredAt:'2026-09-24T10:00:05Z',endedAt:'2026-09-24T10:00:12Z'};
function packet(m=metadata,video=Buffer.from([0,0,0,20,...Buffer.from('ftypisom'),0,0,0,0])){const json=Buffer.from(JSON.stringify(m));const size=Buffer.alloc(4);size.writeUInt32BE(json.length);return Buffer.concat([size,json,video]);}
test('signed clip envelope retains times, strips extraneous fields and fingerprints media',()=>{
 const {metadata:m}=decodeClip(packet({...metadata,path:'evil',continued:true}));assert.equal(m.durationSeconds,12);assert.equal(m.path,undefined);assert.match(m.sha256,/^[a-f0-9]{64}$/);assert.equal(m.continued,true);
});
test('clip validation rejects traversal, oversize, invalid time, oversized duration and non-MP4',()=>{
 assert.equal(validClipId('../secret'),false);assert.throws(()=>decodeClip(packet({...metadata,id:'../secret'})));
 assert.throws(()=>decodeClip(Buffer.alloc(MAX_CLIP_BYTES+1)));assert.throws(()=>decodeClip(packet({...metadata,triggeredAt:'2026-09-24T09:00:00Z'})));
 assert.throws(()=>decodeClip(packet({...metadata,endedAt:'2026-09-24T11:00:00Z'})));assert.throws(()=>decodeClip(packet(metadata,Buffer.alloc(20))));
});

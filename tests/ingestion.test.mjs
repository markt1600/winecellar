import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,sign} from 'node:crypto';
import {authentic,validatePayload} from '../lib/ingestion.mjs';
test('device signatures reject changed data, wrong key and stale requests',()=>{
 const {privateKey,publicKey}=generateKeyPairSync('ed25519');
 const body=Buffer.from('{"reading":12}'),now=Date.now(),ts=String(now);
 const sig=sign(null,Buffer.concat([Buffer.from(ts+'\n'),body]),privateKey).toString('base64');
 assert.equal(authentic(body,ts,sig,now,publicKey),true);
 assert.equal(authentic(Buffer.from('{}'),ts,sig,now,publicKey),false);
 assert.equal(authentic(body,ts,sig,now+300001,publicKey),false);
 assert.equal(authentic(body,ts,sig,now,generateKeyPairSync('ed25519').publicKey),false);
});
test('archives reject path traversal, foreign hour and impossible values; null errors permitted',()=>{
 const p={version:1,kind:'archive',hour:'2026-09-24T10',rows:[{id:1,observed_at:'2026-09-24T10:00:00.000+00:00',bottle_c:12,ambient_c:null,humidity_pct:null}]};
 assert.equal(validatePayload(p),p);
 assert.throws(()=>validatePayload({...p,hour:'../../secret'}));
 assert.throws(()=>validatePayload({...p,rows:[{...p.rows[0],humidity_pct:101}]}));
 assert.throws(()=>validatePayload({...p,rows:[{...p.rows[0],observed_at:'2026-09-23T10:00:00Z'}]}));
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {readingHealth} from '../lib/reading-health.mjs';
const now=Date.parse('2026-09-25T02:00:00Z');
test('failed samples retain the successful time without making the value current',()=>{
 const data={latest:{observed_at:'2026-09-25T02:00:00Z',bottle_c:null,ambient_c:30},lastSuccessful:{bottle_c:{observed_at:'2026-09-25T01:14:51Z',value:25.4}}};
 assert.deepEqual(readingHealth(data,'bottle_c',now),{lastAt:'2026-09-25T01:14:51Z',status:'Sensor reading unavailable'});
 assert.equal(readingHealth(data,'ambient_c',now).status,'Current reading');
 assert.equal(readingHealth(data,'ambient_c',now+181000).status,'Stale reading - Pi has not updated');
 assert.equal(readingHealth({...data,lastSuccessful:{}},'bottle_c',now).lastAt,null);
});
import {targetStatus} from '../lib/reading-health.mjs';
test('target warnings exclude missing values and invalid ranges, with inclusive boundaries',()=>{
 assert.equal(targetStatus(11.9,12,16),'Below target');
 assert.equal(targetStatus(16.1,12,16),'Above target');
 for(const v of [12,14,16,null,undefined,NaN])assert.equal(targetStatus(v,12,16),null);
 assert.equal(targetStatus(80,50,75),'Above target');
 assert.equal(targetStatus(20,16,12),null);
 assert.equal(targetStatus(20,12,12),null);
});

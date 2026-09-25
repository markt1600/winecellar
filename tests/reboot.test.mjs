import test from 'node:test';
import assert from 'node:assert/strict';
import {uuid,online,pending,executable} from '../lib/reboot.mjs';
const now=Date.parse('2026-09-25T02:00:00Z');
test('reboot requires recent ready heartbeat and rejects expired commands',()=>{
 assert.equal(online({ready:true,seenAt:new Date(now-44000).toISOString()},now),true);
 assert.equal(online({ready:true,seenAt:new Date(now-46000).toISOString()},now),false);
 assert.equal(online({ready:false,seenAt:new Date(now).toISOString()},now),false);
 assert.equal(executable({status:'queued',expiresAt:new Date(now-1).toISOString()},now),false);
 assert.equal(executable({status:'completed',expiresAt:new Date(now+1000).toISOString()},now),false);
 assert.equal(pending({status:'scheduled',createdAt:new Date(now-60000).toISOString()},now),true);
 assert.equal(uuid('../reboot'),false);
});

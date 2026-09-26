import test from 'node:test';
import assert from 'node:assert/strict';
import {newestCameraHealth,publicCameraHealth} from '../lib/camera-health.mjs';
test('fresh resumed camera status replaces older paused snapshot in either order',()=>{
 const old={state:'paused',observedAt:'2026-09-26T03:00:00Z'},fresh={state:'watching',observedAt:'2026-09-26T03:00:10Z'};
 assert.equal(newestCameraHealth(old,fresh).state,'watching');assert.equal(newestCameraHealth(fresh,old).state,'watching');
 assert.equal(newestCameraHealth(fresh,{state:'paused',observedAt:'invalid'}).state,'watching');
});
test('public camera health strips private fields and validates state',()=>{
 const value=publicCameraHealth({state:'recording',observedAt:'2026-09-26T03:00:00Z',path:'private',lastClipId:'secret',queuedClips:2});
 assert.equal(value.path,undefined);assert.equal(value.lastClipId,undefined);assert.equal(value.queuedClips,2);
});

const states=['watching','recording','storage_full','stopped','paused','starting'];
export function publicCameraHealth(value){
 if(!value||!Number.isFinite(Date.parse(value.observedAt)))return null;
 return {observedAt:value.observedAt,state:states.includes(value.state)?value.state:'unavailable',lastMotionAt:Number.isFinite(Date.parse(value.lastMotionAt))?value.lastMotionAt:null,queuedClips:Number.isSafeInteger(value.queuedClips)&&value.queuedClips>=0?value.queuedClips:null};
}
export function newestCameraHealth(first,second){
 const a=publicCameraHealth(first),b=publicCameraHealth(second);
 return !a?b:!b?a:Date.parse(b.observedAt)>Date.parse(a.observedAt)?b:a;
}

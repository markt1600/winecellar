import {createHash} from 'node:crypto';
export const MAX_CLIP_BYTES=3900000;
export const validClipId=id=>typeof id==='string'&&/^\d{13}-[a-f0-9]{32}$/.test(id);
export function decodeClip(body){
  if(body.length<12||body.length>MAX_CLIP_BYTES)throw Error('Invalid size');
  const length=body.readUInt32BE(0);
  if(length<2||length>4096||length+12>=body.length)throw Error('Invalid envelope');
  const m=JSON.parse(body.subarray(4,length+4).toString());
  const video=body.subarray(length+4);
  if(!validClipId(m.id)||m.version!==1||!['motion','test'].includes(m.kind))throw Error('Invalid clip');
  for(const k of ['startedAt','endedAt','triggeredAt'])if(!Number.isFinite(Date.parse(m[k])))throw Error('Invalid time');
  const duration=(Date.parse(m.endedAt)-Date.parse(m.startedAt))/1000;
  if(duration<=0||duration>35||Date.parse(m.triggeredAt)<Date.parse(m.startedAt)||Date.parse(m.triggeredAt)>Date.parse(m.endedAt))throw Error('Invalid duration');
  if(video.subarray(4,8).toString()!=='ftyp')throw Error('Expected MP4');
  return {metadata:{version:1,id:m.id,kind:m.kind,startedAt:m.startedAt,endedAt:m.endedAt,triggeredAt:m.triggeredAt,durationSeconds:duration,continued:m.continued===true,bytes:video.length,sha256:createHash('sha256').update(video).digest('hex')},video};
}

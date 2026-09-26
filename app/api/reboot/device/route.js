import {publicCameraHealth} from '../../../../lib/camera-health.mjs';
import {authentic} from '../../../../lib/ingestion.mjs';
import {commandPath,devicePath,readState,writeState,uuid,executable} from '../../../../lib/reboot.mjs';
export const dynamic='force-dynamic';
export async function POST(request){
 const raw=Buffer.from(await request.arrayBuffer());
 if(raw.length>1024||!authentic(raw,request.headers.get('x-cellar-time'),request.headers.get('x-cellar-signature')))return new Response('Unauthorized',{status:401});
 let b;try{b=JSON.parse(raw);if(!uuid(b.bootId)||typeof b.ready!=='boolean'||(b.handled&&(!uuid(b.handled.id)||!['accepted','scheduled','failed','completed'].includes(b.handled.status))))throw Error();}catch{return new Response('Invalid request',{status:400});}
 try{
  const d=await readState(devicePath);await writeState(devicePath,{bootId:b.bootId,ready:b.ready,cameraHealth:publicCameraHealth(b.cameraHealth),cameraReady:b.cameraReady===true,cameraPaused:b.cameraPaused===true,shutdownReady:b.shutdownReady===true,seenAt:new Date().toISOString()},d.etag);
  const c=await readState(commandPath);let command=c.value;
  if(command&&b.handled?.id===command.id&&!['completed','failed'].includes(command.status)){
   const status=command.bootId!==b.bootId?'completed':b.handled.status==='accepted'?command.status:b.handled.status;
   if(status!==command.status){command={...command,status,updatedAt:new Date().toISOString()};await writeState(commandPath,command,c.etag);}
  }
  return Response.json({ok:true,command:b.ready&&(!['pause_camera','resume_camera'].includes(command?.action)||b.cameraReady===true)&&(command?.action!=='shutdown'||b.shutdownReady===true)&&executable(command)&&command.bootId===b.bootId?command:null},{headers:{'Cache-Control':'no-store'}});
 }catch{return new Response('Unavailable',{status:503});}
}

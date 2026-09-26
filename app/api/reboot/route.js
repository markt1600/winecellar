import {isOwner,headers} from '../../../lib/auth.mjs';
import {commandPath,devicePath,readState,writeState,uuid,online,pending} from '../../../lib/reboot.mjs';
export const dynamic='force-dynamic';
export async function GET(){
 if(!await isOwner())return Response.json({error:'Please sign in.'},{status:401,headers});
 try{const [d,c]=await Promise.all([readState(devicePath),readState(commandPath)]);return Response.json({device:d.value,command:c.value,ready:online(d.value),cameraReady:online(d.value)&&d.value.cameraReady===true,cameraPaused:d.value?.cameraPaused===true,shutdownReady:online(d.value)&&d.value.shutdownReady===true},{headers});}
 catch{return Response.json({error:'Device control unavailable.'},{status:503,headers});}
}
export async function POST(request){
 if(!await isOwner())return Response.json({error:'Please sign in.'},{status:401,headers});
 if(request.headers.get('origin')!=='https://winecellar.marktan.ai')return Response.json({error:'Forbidden'},{status:403,headers});
 let b;try{const s=await request.text();if(s.length>256)throw Error();b=JSON.parse(s);if(!uuid(b.id)||![undefined,"reboot","shutdown","pause_camera","resume_camera"].includes(b.action))throw Error();}catch{return Response.json({error:'Invalid request'},{status:400,headers});}
 try{
  const c=await readState(commandPath);
  if(c.value?.id===b.id)return Response.json({ok:true,command:c.value},{headers});
  if(pending(c.value))return Response.json({error:'A device command is already in progress.'},{status:409,headers});
  const d=await readState(devicePath);
  if(!online(d.value))return Response.json({error:'Pi is offline or reboot setup is not complete.'},{status:409,headers});
  if(b.action==="shutdown"&&!d.value.shutdownReady)return Response.json({error:"Shutdown setup is not complete."},{status:409,headers});
  if(["pause_camera","resume_camera"].includes(b.action)&&!d.value.cameraReady)return Response.json({error:"Camera control unavailable."},{status:409,headers});
  const now=Date.now();const command={id:b.id,action:b.action||"reboot",status:'queued',createdAt:new Date(now).toISOString(),expiresAt:new Date(now+120000).toISOString(),bootId:d.value.bootId};
  await writeState(commandPath,command,c.etag);
  return Response.json({ok:true,command},{headers});
 }catch{return Response.json({error:'Request could not be saved. Please retry.'},{status:503,headers});}
}

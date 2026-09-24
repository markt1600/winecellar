import {head,put,BlobNotFoundError} from '@vercel/blob';
import {isOwner,headers} from '../../../lib/auth.mjs';
import {currentMonitoring,monitoringPath} from '../../../lib/monitoring.mjs';
export const dynamic='force-dynamic';
export async function GET(){
 if(!await isOwner())return Response.json({error:'Please sign in.'},{status:401,headers});
 try{return Response.json({session:await currentMonitoring()},{headers});}
 catch{return Response.json({error:'Monitoring settings unavailable.'},{status:503,headers});}
}
export async function POST(request){
 if(!await isOwner())return Response.json({error:'Please sign in.'},{status:401,headers});
 if(request.headers.get('origin')!=='https://winecellar.marktan.ai')return new Response('Forbidden',{status:403,headers});
 let body;try{const text=await request.text();if(text.length>1024)throw Error();body=JSON.parse(text);}catch{return new Response('Invalid request',{status:400,headers});}
 if(!/^[a-f0-9-]{36}$/.test(body.id||'')||typeof body.location!=='string'||body.location.trim().length>80)return new Response('Invalid request',{status:400,headers});
 try{
  let metadata;try{metadata=await head(monitoringPath);}catch(e){if(!(e instanceof BlobNotFoundError))throw e;}
  const old=await currentMonitoring();
  if(old?.id===body.id)return Response.json({ok:true,session:old},{headers});
  const session={id:body.id,location:body.location.trim(),startedAt:new Date().toISOString()};
  await put(monitoringPath,JSON.stringify(session),{access:'private',addRandomSuffix:false,allowOverwrite:!!metadata,...(metadata?{ifMatch:metadata.etag}:{}),contentType:'application/json'});
  return Response.json({ok:true,session},{headers});
 }catch{return Response.json({error:'Could not start a new period. Please retry.'},{status:503,headers});}
}

import {get,put,del} from '@vercel/blob';
import {isOwner,headers} from '../../../../../lib/auth.mjs';
import {validClipId} from '../../../../../lib/clips.mjs';
export const dynamic='force-dynamic';
export const runtime='nodejs';
const reply=(text,status)=>new Response(text,{status,headers});
async function exists(id){
 const record=await get(`cellar/v1/events/${id}.json`,{access:'private',useCache:false});
 if(!record)return false;
 await record.stream.cancel();return true;
}
export async function GET(request,{params}){
 if(!await isOwner())return reply('Unauthorized',401);
 const {id}=await params;if(!validClipId(id))return reply('Not found',404);
 try{
  if(!await exists(id))return reply('Not found',404);
  const poster=await get(`cellar/v1/posters/${id}.jpg`,{access:'private',useCache:false});
  if(!poster)return reply('Not found',404);
  return new Response(poster.stream,{headers:{...headers,'Content-Type':'image/jpeg','X-Content-Type-Options':'nosniff'}});
 }catch{return reply('Preview unavailable',503);}
}
export async function POST(request,{params}){
 if(!await isOwner())return reply('Unauthorized',401);
 if(request.headers.get('origin')!=='https://winecellar.marktan.ai')return reply('Forbidden',403);
 const {id}=await params;if(!validClipId(id))return reply('Not found',404);
 if(request.headers.get('content-type')!=='image/jpeg'||!request.body)return reply('Expected JPEG',415);
 const chunks=[];let size=0;
 for await(const chunk of request.body){size+=chunk.length;if(size>300000)return reply('Too large',413);chunks.push(chunk);}
 const body=Buffer.concat(chunks);
 if(body.length<4||body[0]!==255||body[1]!==216||body[2]!==255||body.at(-2)!==255||body.at(-1)!==217)return reply('Invalid JPEG',400);
 const path=`cellar/v1/posters/${id}.jpg`;
 try{
  if(!await exists(id))return reply('Not found',404);
  const old=await get(path,{access:'private',useCache:false});
  if(old){await old.stream.cancel();return reply('Saved',200);}
  try{await put(path,body,{access:'private',addRandomSuffix:false,contentType:'image/jpeg'});}
  catch(error){const concurrent=await get(path,{access:'private',useCache:false});if(!concurrent)throw error;await concurrent.stream.cancel();}
  if(!await exists(id)){await del(path);return reply('Not found',404);}
  return reply('Saved',201);
 }catch{return reply('Preview storage unavailable',503);}
}

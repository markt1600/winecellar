import {get,put,head,BlobNotFoundError} from '@vercel/blob';
import {authentic} from '../../../lib/ingestion.mjs';
import {decodeClip,MAX_CLIP_BYTES} from '../../../lib/clips.mjs';
import {pruneClips,allBlobs,retentionPlan,CLIP_LIMIT} from '../../../lib/clip-retention.mjs';
import {isOwner,headers} from '../../../lib/auth.mjs';
export const runtime='nodejs';
export const dynamic='force-dynamic';
export const maxDuration=60;
export async function POST(request){
  const chunks=[];let size=0;
  for await(const chunk of request.body){size+=chunk.length;if(size>MAX_CLIP_BYTES)return new Response('Too large',{status:413});chunks.push(chunk);}
  const body=Buffer.concat(chunks);
  if(!authentic(body,request.headers.get('x-cellar-time'),request.headers.get('x-cellar-signature')))return new Response('Unauthorized',{status:401});
  let clip;try{clip=decodeClip(body);}catch{return new Response('Invalid clip',{status:400});}
  const base=`cellar/v1/clips/${clip.metadata.id}`;
  try{
    // Unique immutable names make device retries safe, including a lost acknowledgement.
    const path=`${base}-${clip.metadata.sha256}.mp4`;
    try{await head(path);}catch(error){if(!(error instanceof BlobNotFoundError))throw error;await put(path,clip.video,{access:'private',addRandomSuffix:false,contentType:'video/mp4'});}
    const recordPath=`cellar/v1/events/${clip.metadata.id}.json`;
    const existing=await get(recordPath,{access:'private',useCache:false});
    if(existing){const old=await new Response(existing.stream).json();if(old.sha256!==clip.metadata.sha256)return new Response('Clip identity conflict',{status:409});}
    else await put(recordPath,JSON.stringify({...clip.metadata,path}),{access:'private',addRandomSuffix:false,contentType:'application/json'});
    await pruneClips();
    return Response.json({ok:true,id:clip.metadata.id});
  }catch{return new Response('Storage unavailable',{status:503});}
}
export async function GET(request){
  if(!await isOwner())return Response.json({error:'Please sign in.'},{status:401,headers});
  try{
    const page={blobs:retentionPlan(await allBlobs('cellar/v1/events/'),[]).kept};
    const clips=await Promise.all(page.blobs.map(async b=>{const r=await get(b.pathname,{access:'private'});if(!r||r.statusCode!==200)throw Error('Unavailable');const {path,sha256,...m}=await new Response(r.stream).json();return m;}));
    return Response.json({clips,cursor:null,retentionLimit:CLIP_LIMIT},{headers});
  }catch{return Response.json({error:'Clips are temporarily unavailable.'},{status:503,headers});}
}

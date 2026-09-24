import {get} from '@vercel/blob';
import {isOwner,headers} from '../../../../lib/auth.mjs';
import {validClipId} from '../../../../lib/clips.mjs';
export const dynamic='force-dynamic';
export const maxDuration=60;
export async function GET(request,{params}){
  if(!await isOwner())return new Response('Unauthorized',{status:401,headers});
  const {id}=await params;
  if(!validClipId(id))return new Response('Not found',{status:404,headers});
  try{
    const record=await get(`cellar/v1/events/${id}.json`,{access:'private'});
    if(!record)return new Response('Not found',{status:404,headers});
    const m=await new Response(record.stream).json();
    const range=request.headers.get('range');
    if(range&&!/^bytes=\d*-\d*$/.test(range))return new Response('Invalid range',{status:416,headers});
    const video=await get(m.path,{access:'private',...(range?{headers:{Range:range}}:{})});
    if(!video)return new Response('Not found',{status:404,headers});
    const responseHeaders={...headers,'Content-Type':'video/mp4','Accept-Ranges':'bytes','X-Content-Type-Options':'nosniff'};
    for(const name of ['content-length','content-range']){const value=video.headers.get(name);if(value)responseHeaders[name]=value;}
    return new Response(video.stream,{status:video.headers.has('content-range')?206:200,headers:responseHeaders});
  }catch{return new Response('Video unavailable',{status:503,headers});}
}

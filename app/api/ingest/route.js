import {get,put} from '@vercel/blob';
import {authentic,validatePayload} from '../../../lib/ingestion.mjs';
export const runtime='nodejs';
export const maxDuration=60;
export async function POST(request) {
  const chunks=[]; let size=0;
  if (Number(request.headers.get('content-length'))>2000000) return new Response('Too large',{status:413});
  for await (const chunk of request.body) {size+=chunk.length;if(size>2000000)return new Response('Too large',{status:413});chunks.push(chunk);}
  const body=Buffer.concat(chunks);
  if (!authentic(body,request.headers.get('x-cellar-time'),request.headers.get('x-cellar-signature'))) return new Response('Unauthorized',{status:401});
  let p;try{p=validatePayload(JSON.parse(body));}catch{return new Response('Invalid data',{status:400});}
  const path=p.kind==='snapshot'?'cellar/v1/dashboard.json':`cellar/v1/readings/${p.hour}.json`;
  try {
    // Version checks + conditional writes make retries idempotent and prevent older uploads winning.
    const existing=await get(path,{access:'private',useCache:false});
    let etag;
    if(existing){
      if(existing.statusCode!==200)throw Error('Read failed');
      const old=await new Response(existing.stream).json();
      const oldVersion=p.kind==='snapshot'?Date.parse(old.generatedAt):Math.max(...old.rows.map(r=>r.id));
      const version=p.kind==='snapshot'?Date.parse(p.generatedAt):Math.max(...p.rows.map(r=>r.id));
      if(oldVersion>=version)return Response.json({ok:true,unchanged:true});
      etag=existing.blob.etag;
    }
    await put(path,body,{access:'private',addRandomSuffix:false,allowOverwrite:!!existing,
      ...(etag?{ifMatch:etag}:{}),contentType:'application/json',cacheControlMaxAge:60});
    return Response.json({ok:true});
  }catch(error){console.error('Blob update failed',error?.name);return new Response('Storage unavailable; retry later',{status:503});}
}

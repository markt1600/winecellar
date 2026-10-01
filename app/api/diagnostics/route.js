import {get,put,del} from '@vercel/blob';
import {authentic} from '../../../lib/ingestion.mjs';
import {isOwner,headers} from '../../../lib/auth.mjs';
import {allBlobs} from '../../../lib/clip-retention.mjs';
export const runtime='nodejs';
export const maxDuration=60;
const prefix='cellar/v1/diagnostics/';
const validId=id=>/^\d{13}-[a-f0-9]{32}$/.test(id||'');
export async function GET(request){
  if(!await isOwner())return Response.json({error:'Sign in required'},{status:401,headers});
  try{
    const id=new URL(request.url).searchParams.get('id');
    if(id){
      if(!validId(id))return new Response('Invalid ID',{status:400,headers});
      const report=await get(`${prefix}${id}.json`,{access:'private',useCache:false});
      if(!report||report.statusCode!==200)return new Response('Not found',{status:404,headers});
      return new Response(report.stream,{headers:{...headers,'Content-Type':'application/json','Content-Disposition':`attachment; filename="cellar-diagnostic-${id}.json"`}});
    }
    const reports=(await allBlobs(prefix)).sort((a,b)=>b.pathname.localeCompare(a.pathname)).slice(0,20)
      .map(b=>({id:b.pathname.slice(prefix.length,-5),uploadedAt:b.uploadedAt,size:b.size}));
    return Response.json({reports},{headers});
  }catch{return Response.json({error:'Diagnostics unavailable'},{status:503,headers});}
}
export async function POST(request){
  let size=0;const chunks=[];
  if(!request.body)return new Response('Missing body',{status:400});
  for await(const chunk of request.body){size+=chunk.length;if(size>450000)return new Response('Too large',{status:413});chunks.push(chunk);}
  const body=Buffer.concat(chunks);
  if(!authentic(body,request.headers.get('x-cellar-time'),request.headers.get('x-cellar-signature')))return new Response('Unauthorized',{status:401});
  let report;
  try{
    report=JSON.parse(body);
    if(report.version!==1||!validId(report.id)||!Number.isFinite(Date.parse(report.createdAt))||typeof report.reason!=='string'||report.reason.length>500||!Array.isArray(report.history)||report.history.length>60)throw Error();
  }catch{return new Response('Invalid report',{status:400});}
  try{
    await put(`${prefix}${report.id}.json`,body,{access:'private',addRandomSuffix:false,allowOverwrite:true,contentType:'application/json',cacheControlMaxAge:60});
    const reports=(await allBlobs(prefix)).sort((a,b)=>b.pathname.localeCompare(a.pathname));
    const expired=reports.slice(20).map(b=>b.pathname);
    if(expired.length)await del(expired);
    return Response.json({ok:true});
  }catch{return new Response('Storage unavailable; retry later',{status:503});}
}

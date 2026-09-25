import {authentic} from '../../../../lib/ingestion.mjs';
import {pruneClips} from '../../../../lib/clip-retention.mjs';
export const dynamic='force-dynamic';
export const maxDuration=60;
export async function POST(request){
 const body=Buffer.from(await request.arrayBuffer());
 if(body.length>256||!authentic(body,request.headers.get('x-cellar-time'),request.headers.get('x-cellar-signature')))return new Response('Unauthorized',{status:401});
 try{if(JSON.parse(body).kind!=='clip-retention')return new Response('Invalid request',{status:400});}catch{return new Response('Invalid request',{status:400});}
 try{return Response.json({ok:true,...await pruneClips()},{headers:{'Cache-Control':'no-store'}});}catch{return new Response('Cleanup unavailable',{status:503});}
}

import {authentic} from '../../../../lib/ingestion.mjs';
import {currentMonitoring} from '../../../../lib/monitoring.mjs';
export const dynamic='force-dynamic';
export async function POST(request){
 const body=Buffer.from(await request.arrayBuffer());
 if(body.length>1024||!authentic(body,request.headers.get('x-cellar-time'),request.headers.get('x-cellar-signature')))return new Response('Unauthorized',{status:401});
 try{return Response.json({ok:true,session:await currentMonitoring()},{headers:{'Cache-Control':'no-store'}});}
 catch{return new Response('Unavailable',{status:503});}
}

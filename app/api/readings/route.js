import {get} from '@vercel/blob';
import {headers} from '../../../lib/auth.mjs';
import {currentMonitoring} from '../../../lib/monitoring.mjs';
export const dynamic='force-dynamic';
export async function GET(){
  try{
    const result=await get('cellar/v1/dashboard.json',{access:'private',useCache:false});
    if(!result)return Response.json({empty:true},{headers});
    if(result.statusCode!==200)throw Error('Read failed');
    const data=await new Response(result.stream).json();
    const session=await currentMonitoring();
    if(session&&data.monitoringSession?.id!==session.id)return Response.json({empty:true,resetPending:true,monitoringSession:session},{headers});
    // Environmental readings are public. Camera status and upload identifiers remain private.
    const {camera,cameraUpload,...environment}=data;
    return Response.json(environment,{headers});
  }catch{return Response.json({error:'Readings are temporarily unavailable.'},{status:503,headers});}
}

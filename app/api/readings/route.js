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
    // Expose only basic camera health; recordings and upload identifiers remain private.
    const {camera,cameraUpload,...environment}=data;
    const states=['watching','recording','storage_full','stopped'];
    const cameraHealth=camera?{lastMotionAt:Number.isFinite(Date.parse(camera.lastMotionAt))?camera.lastMotionAt:null,observedAt:camera.observedAt,state:states.includes(camera.state)?camera.state:'unavailable',queuedClips:Number.isSafeInteger(camera.queuedClips)&&camera.queuedClips>=0?camera.queuedClips:null}:null;
    return Response.json({...environment,cameraHealth},{headers});
  }catch{return Response.json({error:'Readings are temporarily unavailable.'},{status:503,headers});}
}

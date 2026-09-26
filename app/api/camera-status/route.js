import {readState,devicePath} from '../../../lib/reboot.mjs';
import {newestCameraHealth} from '../../../lib/camera-health.mjs';
import {get} from '@vercel/blob';
import {isOwner,headers} from '../../../lib/auth.mjs';
export const dynamic='force-dynamic';
export async function GET(){
 if(!await isOwner())return Response.json({error:'Please sign in.'},{status:401,headers});
 try{const r=await get('cellar/v1/dashboard.json',{access:'private',useCache:false});const d=r?await new Response(r.stream).json():{};let live=null;try{live=(await readState(devicePath)).value?.cameraHealth;}catch{}const health=newestCameraHealth(d.camera,live);return Response.json({camera:health?{...d.camera,...health}:null,upload:d.cameraUpload||null},{headers});}
 catch{return Response.json({error:'Camera status unavailable.'},{status:503,headers});}
}

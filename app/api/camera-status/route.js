import {get} from '@vercel/blob';
import {isOwner,headers} from '../../../lib/auth.mjs';
export const dynamic='force-dynamic';
export async function GET(){
 if(!await isOwner())return Response.json({error:'Please sign in.'},{status:401,headers});
 try{const r=await get('cellar/v1/dashboard.json',{access:'private',useCache:false});const d=r?await new Response(r.stream).json():{};return Response.json({camera:d.camera||null,upload:d.cameraUpload||null},{headers});}
 catch{return Response.json({error:'Camera status unavailable.'},{status:503,headers});}
}

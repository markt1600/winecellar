import {get} from '@vercel/blob';
import {headers,isOwner} from '../../../lib/auth.mjs';
export const dynamic='force-dynamic';
export async function GET(){
  if(!await isOwner())return Response.json({error:'Please sign in.'},{status:401,headers});
  try{
    const result=await get('cellar/v1/dashboard.json',{access:'private',useCache:false});
    if(!result)return Response.json({empty:true},{headers});
    if(result.statusCode!==200)throw Error('Read failed');
    return Response.json(await new Response(result.stream).json(),{headers});
  }catch{return Response.json({error:'Readings are temporarily unavailable.'},{status:503,headers});}
}

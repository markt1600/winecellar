import {isOwner,headers} from '../../../lib/auth.mjs';
export const dynamic='force-dynamic';
export async function GET(){
  const ok=await isOwner();
  return Response.json({ok},{status:ok?200:401,headers});
}

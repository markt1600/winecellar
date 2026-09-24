import {get} from '@vercel/blob';
export const monitoringPath='cellar/v1/monitoring/current.json';
export async function currentMonitoring(){
 const r=await get(monitoringPath,{access:'private',useCache:false});
 if(!r)return null;
 if(r.statusCode!==200)throw Error('Monitoring configuration unavailable');
 return new Response(r.stream).json();
}

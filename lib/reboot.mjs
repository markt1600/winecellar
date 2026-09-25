import {get,head,put,BlobNotFoundError} from '@vercel/blob';
export const commandPath='cellar/v1/control/reboot.json';
export const devicePath='cellar/v1/control/device.json';
export const uuid=v=>typeof v==='string'&&/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(v);
export const online=(d,now=Date.now())=>!!d?.ready&&now-Date.parse(d.seenAt)<45000;
export const pending=(c,now=Date.now())=>!!c&&['queued','scheduled'].includes(c.status)&&now-Date.parse(c.createdAt)<180000;
export const executable=(c,now=Date.now())=>c?.status==='queued'&&Date.parse(c.expiresAt)>now;
export async function readState(path){
 let meta;try{meta=await head(path);}catch(e){if(e instanceof BlobNotFoundError)return {value:null,etag:null};throw e;}
 const r=await get(path,{access:'private',useCache:false});
 if(!r||r.statusCode!==200)throw Error('State unavailable');
 return {value:await new Response(r.stream).json(),etag:meta.etag};
}
export async function writeState(path,value,etag){
 await put(path,JSON.stringify(value),{access:'private',addRandomSuffix:false,allowOverwrite:!!etag,...(etag?{ifMatch:etag}:{}),contentType:'application/json'});
}

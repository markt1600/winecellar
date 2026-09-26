import {queuePoster} from './video-preview.mjs';
export async function savedPoster(source,clip,signal,{fetcher=fetch,generate=queuePoster}={}){
 const url=source+'/poster';
 const existing=await fetcher(url,{signal,cache:'no-store'});
 if(existing.ok)return existing.blob();
 if(existing.status!==404)throw Error('Preview storage unavailable');
 const image=await generate(source,clip,signal);
 const blob=await (await fetcher(image,{signal})).blob();
 const saved=await fetcher(url,{method:'POST',body:blob,headers:{'Content-Type':'image/jpeg'},signal});
 if(!saved.ok)throw Error('Preview could not be saved');
 return blob;
}

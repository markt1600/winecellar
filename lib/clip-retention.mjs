import {list,del} from '@vercel/blob';
export const CLIP_LIMIT=10;
const eventId=path=>/^cellar\/v1\/events\/(\d{13}-[a-f0-9]{32})\.json$/.exec(path)?.[1];
const videoId=path=>/^cellar\/v1\/clips\/(\d{13}-[a-f0-9]{32})-[a-f0-9]{64}\.mp4$/.exec(path)?.[1];
const posterId=path=>/^cellar\/v1\/posters\/(\d{13}-[a-f0-9]{32})\.jpg$/.exec(path)?.[1];
// Device IDs begin with an inverted millisecond timestamp: ascending IDs are newest first.
export function retentionPlan(events,videos,posters=[]){
 const sorted=events.filter(b=>eventId(b.pathname)).sort((a,b)=>a.pathname.localeCompare(b.pathname));
 const kept=sorted.slice(0,CLIP_LIMIT);const cutoff=kept.length===CLIP_LIMIT?eventId(kept.at(-1).pathname):null;
 const expired=sorted.slice(CLIP_LIMIT).map(b=>b.pathname);
 // Also collect old orphan MP4s after a previous interrupted metadata deletion.
 const media=cutoff?videos.filter(b=>{const id=videoId(b.pathname);return id&&id>cutoff;}).map(b=>b.pathname):[];
 const thumbnails=cutoff?posters.filter(b=>{const id=posterId(b.pathname);return id&&id>cutoff;}).map(b=>b.pathname):[];
 return {kept,expired,media,thumbnails};
}
export async function allBlobs(prefix,api={list}){
 const blobs=[];let cursor;
 do{const page=await api.list({prefix,limit:1000,...(cursor?{cursor}:{})});blobs.push(...page.blobs);cursor=page.hasMore?page.cursor:null;if(page.hasMore&&!cursor)throw Error('Missing cursor');}while(cursor);
 return blobs;
}
export async function pruneClips(api={list,del}){
 const [events,videos,posters]=await Promise.all([allBlobs('cellar/v1/events/',api),allBlobs('cellar/v1/clips/',api),allBlobs('cellar/v1/posters/',api)]);
 const plan=retentionPlan(events,videos,posters);
 // Delete media first; failed deletions leave records discoverable for a retry.
 for(let i=0;i<plan.media.length;i+=100)await api.del(plan.media.slice(i,i+100));
 for(let i=0;i<plan.thumbnails.length;i+=100)await api.del(plan.thumbnails.slice(i,i+100));
 for(let i=0;i<plan.expired.length;i+=100)await api.del(plan.expired.slice(i,i+100));
 return {kept:plan.kept.length,deletedRecords:plan.expired.length,deletedVideos:plan.media.length};
}

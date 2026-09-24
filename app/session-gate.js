'use client';
import {useEffect} from 'react';
import {useRouter} from 'next/navigation';

export default function SessionGate(){
  const router=useRouter();
  useEffect(()=>{
    let disposed=false,pending=false;
    const controller=new AbortController();
    async function check(){
      if(disposed||pending||document.visibilityState==='hidden')return;
      pending=true;
      try{
        const response=await fetch('/api/session',{cache:'no-store',signal:controller.signal});
        if(response.ok&&(await response.json()).ok===true&&!disposed)router.refresh();
      }catch{/* Keep the gate closed if verification is unavailable. */}
      finally{pending=false;}
    }
    check();
    window.addEventListener('focus',check);
    document.addEventListener('visibilitychange',check);
    const timer=setInterval(check,15000);
    return()=>{disposed=true;controller.abort();clearInterval(timer);window.removeEventListener('focus',check);document.removeEventListener('visibilitychange',check);};
  },[router]);
  return <section className="gate"><h2>Your cellar, privately.</h2><p>Your marktan.ai owner login also unlocks this dashboard. No separate account or password is needed.</p><a className="button" href="https://marktan.ai" target="_blank" rel="noopener">Continue at marktan.ai ↗</a><p className="muted">Already signed in? Open marktan.ai in this same browser to refresh your shared session, then return here. This page checks automatically.</p></section>;
}

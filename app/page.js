import {isOwner} from '../lib/auth.mjs';
import Dashboard from './dashboard';
import SessionGate from './session-gate';
import MonitoringReset from './monitoring-reset';
import Activity from './activity';
export const dynamic='force-dynamic';
export default async function Page(){const owner=await isOwner();return <main><header><a href="https://marktan.ai">mark<span>tan</span>.ai</a><span>CELLAR JOURNAL</span></header><div className="masthead"><p>ENVIRONMENT & CONDITION</p><h1>The <em>Cellar.</em></h1></div><Dashboard/>{owner?<><Activity/><MonitoringReset/></>:<SessionGate/>}<footer><span>MARKTAN.AI · THE CELLAR</span><span>Times shown in Singapore · °C / % RH</span></footer></main>;}

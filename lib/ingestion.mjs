import {verify} from 'node:crypto';
export const deviceKey = `-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAHSuq0tg6LYIjkgOnkf4Vjx1qntrJzf0Nzgjo6ibWMkw=
-----END PUBLIC KEY-----`;
export function authentic(body, timestamp, signature, now = Date.now(), key = deviceKey) {
  if (!/^\d{13}$/.test(timestamp || '') || Math.abs(now-Number(timestamp))>300000) return false;
  if (!/^[A-Za-z0-9+/]{86}==$/.test(signature || '')) return false;
  try { return verify(null, Buffer.concat([Buffer.from(`${timestamp}\n`),body]),key,Buffer.from(signature,'base64')); }
  catch { return false; }
}
export function validatePayload(p) {
  if (!p || p.version!==1 || !['archive','snapshot'].includes(p.kind)) throw Error('Invalid payload');
  if (p.kind==='snapshot') {
    if (!Number.isFinite(Date.parse(p.generatedAt)) || !p.windows || !p.latest || !p.allTime) throw Error('Invalid snapshot');
    for (const key of ['1h','24h','1mo','1y']) {
      const w=p.windows[key];
      if (!w || !Array.isArray(w.points) || w.points.length>900 || !w.stats) throw Error('Invalid window');
    }
  } else {
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}$/.test(p.hour) || !Array.isArray(p.rows) || !p.rows.length || p.rows.length>720) throw Error('Invalid archive');
    for (const r of p.rows) {
      if (!Number.isSafeInteger(r.id) || r.id<1 || typeof r.observed_at!=='string' || !r.observed_at.startsWith(p.hour) || !Number.isFinite(Date.parse(r.observed_at))) throw Error('Invalid reading');
      for (const [k,min,max] of [['bottle_c',-55,125],['ambient_c',-40,80],['humidity_pct',0,100]]) {
        if (r[k]!==null && (!Number.isFinite(r[k]) || r[k]<min || r[k]>max)) throw Error('Invalid sensor value');
      }
    }
  }
  return p;
}

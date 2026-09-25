export function readingHealth(data,field,now=Date.now()) {
  const latest=data.latest;
  const valid=Number.isFinite(latest[field]);
  const recorded=data.lastSuccessful?.[field];
  const lastAt=recorded?.observed_at||(valid?latest.observed_at:null);
  const stale=now-Date.parse(latest.observed_at)>180000;
  return {lastAt,status:!valid?'Sensor reading unavailable':stale?'Stale reading - Pi has not updated':'Current reading'};
}

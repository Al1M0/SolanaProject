import type {Segment} from "./types";

export const auditSeries = [
  {key:"strategy",label:"Wallet hypothesis",color:"#8befc4"},
  {key:"buy_and_hold",label:"Buy-and-hold",color:"#b9a2ff"},
  {key:"momentum",label:"Simple momentum",color:"#efd195"},
] as const;

export type AuditCurvePoint = {ts:number;strategy:number|null;buy_and_hold:number|null;momentum:number|null};

// Join exact observation timestamps. Never carry a future or stale value into a gap.
export function buildAuditCurve(results:Record<string,Pick<Segment,"valid"|"equity_curve">>):AuditCurvePoint[]{
  const timeline = new Map<number,AuditCurvePoint>();
  for(const {key} of auditSeries){
    const result = results[key];
    if(!result?.valid) continue;
    for(const point of result.equity_curve){
      if(!Number.isFinite(point.ts)) continue;
      const row = timeline.get(point.ts) || {ts:point.ts,strategy:null,buy_and_hold:null,momentum:null};
      row[key] = Number.isFinite(point.net_equity) ? point.net_equity : null;
      timeline.set(point.ts,row);
    }
  }
  return [...timeline.values()].sort((a,b)=>a.ts-b.ts);
}

"use client";
import {Area,AreaChart,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis} from "recharts";
import {Empty} from "./workspace";
export const money=(n:number|null|undefined,digits=2)=>n==null?"N/A":new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:digits}).format(n);
export const quantity=(n:number|null|undefined,digits=4)=>n==null?"N/A":new Intl.NumberFormat("en-US",{maximumFractionDigits:digits}).format(n);
export const change=(n:number|null|undefined)=>n==null?"N/A":`${n>0?"+":""}${n.toFixed(2)}%`;
export const utc=(ts:number|null|undefined)=>ts==null?"N/A":new Date(ts*1000).toLocaleString("en-GB",{timeZone:"UTC",month:"short",day:"2-digit",hour:"2-digit",minute:"2-digit"})+" UTC";
export function RealChart({points,field="price_usd",resolution=0,label="USD price"}:{points:Record<string,number|null>[];field?:string;resolution?:number;label?:string}){
  if(points.filter(p=>p[field]!=null).length<2)return <Empty title="Insufficient historical data">At least two real observations are required. No placeholder chart is shown.</Empty>;
  const rows:Record<string,number|null>[]=[];points.forEach((p,i)=>{const prior=points[i-1];if(resolution&&prior&&Number(p.ts)-Number(prior.ts)>resolution*1.5)rows.push({ts:Number(prior.ts)+resolution,[field]:null});rows.push(p);});
  return <div className="chart" aria-label={label}><ResponsiveContainer width="100%" height="100%"><AreaChart data={rows} margin={{left:10,right:15,top:10}}><CartesianGrid stroke="#2a3033" vertical={false} strokeDasharray="3 4"/><XAxis dataKey="ts" type="number" domain={["dataMin","dataMax"]} tickFormatter={v=>new Date(v*1000).toLocaleDateString("en-GB",{timeZone:"UTC",month:"short",day:"2-digit"})} tick={{fill:"#929cae",fontSize:12}} minTickGap={65}/><YAxis domain={["auto","auto"]} width={85} tickFormatter={v=>money(v,Number(v)<1?5:2)} tick={{fill:"#929cae",fontSize:12}}/><Tooltip contentStyle={{background:"#171c27",border:"1px solid #323a49",fontSize:14,color:"#e9edf5"}} labelFormatter={v=>utc(Number(v))} formatter={v=>[money(Number(v),Number(v)<1?8:2),label]}/><Area dataKey={field} type="linear" stroke="#60dfb4" fill="#60dfb4" fillOpacity={.08} strokeWidth={2} connectNulls={false} dot={false} isAnimationActive={false}/></AreaChart></ResponsiveContainer></div>;
}

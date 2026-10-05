import {chainRequest,RawHistory} from "./chain";
import {researchCompute,saveImportedDataset} from "./api";
import type {Dataset} from "./types";
export type WalletAnalysis={wallet:string;observed_trades:number;buys:number;sells:number;closed_sales:number;partial_matched_sales:number;unmatched_sales:number;win_rate_pct:number|null;average_return_pct:number|null;median_return_pct:number|null;observed_matched_pnl_by_quote:Record<string,number>;realized_pnl_usd:number|null;trades_per_observed_day:number|null;tokens_traded:number;coverage_complete:boolean;minimum_sample:number;evidence_status:string;recent_activity:Swap[]};
export type Swap={id:string;signature:string;type:string;token:string;wallet:string;ts:number;side:string;quantity:number;quote_mint:string;quote_quantity:number;network_fee_lamports:number|null};
export type Analysis={kind:"REAL";wallets:WalletAnalysis[];events:Swap[];provenance:Record<string,unknown>;limitations:string[]};
export type AccumulationEvent={token:string;ts:number;wallets:string[];wallet_count:number;window_seconds:number;prior_similar_events:number;score_basis:string;liquidity_usd:number|null;eligible_for_backtest:boolean};
export type Detections={kind:"REAL";events:AccumulationEvent[];observed_swaps:number;provenance:Record<string,unknown>;size_rejections:number;limitations:string[]};
export const analyze=(histories:RawHistory[],minimum_sample=10)=>researchCompute<Analysis>("analytics",{histories,minimum_sample});
export class StudyBudget {
  usedUpperBound=0;
  constructor(public limit=240,public signal?:AbortSignal){}
  beforeRequest=()=>{this.signal?.throwIfAborted();if(this.usedUpperBound+2>this.limit)throw new Error(`Provider-attempt budget exhausted (${this.usedUpperBound}/${this.limit}). Each proxy call reserves two attempts including its retry. Narrow the study or explicitly raise the budget.`);this.usedUpperBound+=2;};
}
export async function importStudy(histories:RawHistory[],includeMarkets:boolean,progress:(s:string)=>void,budget=new StudyBudget()):Promise<Dataset>{
  const analysis=await analyze(histories),start=histories[0].requested_start,end=histories[0].requested_end;
  const tokens=[...new Set(analysis.events.map(e=>e.token))];if(tokens.length>20)throw new Error("More than 20 tokens were observed. Narrow the historical window.");if(!tokens.length)throw new Error("No supported swaps were observed; a research dataset cannot be fabricated.");
  const markets:Record<string,{prices:Record<string,number|null>[];liquidity:Record<string,number|null>[]}>={};
  if(includeMarkets){if(tokens.length>5)throw new Error("Hosted historical backfill is limited to 5 tokens per study. Narrow the window, or use the full FastAPI ingestion for up to 20 tokens.");for(let i=0;i<tokens.length;i++){
    const mint=tokens[i],prices:Record<string,number|null>[]=[],liquidity:Record<string,number|null>[]=[];
    for(let left=start-300;left<end;left+=300*98){progress(`Token ${i+1}/${tokens.length}: historical USD prices · budget ≤${budget.usedUpperBound}/${budget.limit}`);const right=Math.min(left+300*98,end-300);if(right<=left)continue;budget.beforeRequest();const d=await chainRequest<{prices:Record<string,number|null>[]}>(`/api/markets/${mint}/research-prices?start=${left}&end=${right}`,{signal:budget.signal});prices.push(...d.prices);}
    let anchor=end;for(let page=0;page<220;page++){progress(`Token ${i+1}/${tokens.length}: historical liquidity · page ${page+1} · budget ≤${budget.usedUpperBound}/${budget.limit}`);budget.beforeRequest();const d=await chainRequest<{items:Record<string,number|null>[];next_time:number|null}>(`/api/markets/${mint}/research-liquidity?time=${anchor}`,{signal:budget.signal});liquidity.push(...d.items);if(!d.next_time||d.next_time>=anchor||d.next_time<start)break;anchor=d.next_time;}
    markets[mint]={prices,liquidity};
  }}
  progress("Validating coverage and saving the REAL research dataset…");
  const dataset=await researchCompute<Dataset>("build_real",{id:"real_"+crypto.randomUUID().replaceAll("-","").slice(0,20),name:"Solana wallet study · "+new Date().toISOString().slice(0,16)+" UTC",histories,markets,start_ts:start,end_ts:end,retrieved_at:new Date().toISOString()});
  budget.signal?.throwIfAborted();
  dataset.provenance.request_budget={limit:budget.limit,used_upper_bound:budget.usedUpperBound,includes_retries:true};
  dataset.provenance.redistribution="not_confirmed; provider observations excluded from public bundles by default";
  const normalized=await researchCompute<Dataset>("dataset_quality",dataset);await saveImportedDataset(normalized);return normalized;
}

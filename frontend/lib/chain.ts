import type {Dataset} from "./types";
export const chainBase = process.env.NEXT_PUBLIC_CHAIN_API_URL || (process.env.NEXT_PUBLIC_EXECUTION_MODE === "browser" ? "" : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");
export type TokenMarket = {mint:string;symbol:string|null;name:string|null;price_usd:number|null;change_24h_pct:number|null;volume_24h_usd:number|null;liquidity_usd:number|null;market_cap_usd:number|null;fdv_usd:number|null;pair_address:string|null;dex:string|null;provider:string;retrieved_at:string;limitations:string[]};
export type Holding = {mint:string;decimals:number;raw_amount:string;amount:string;symbol:string|null;name:string|null;valuation_supported:boolean;price_usd:number|null;value_usd:number|null};
export type WalletSnapshot = {wallet:string;kind:"REAL";network:string;sol_balance:number;balance_lamports:number;slot:number|null;tokens:Holding[];sol_price_usd:number|null;sol_value_usd:number|null;valued_subtotal_usd:number|null;portfolio_complete:boolean;unpriced_tokens:number;warnings:string[];limitations:string[];retrieved_at:string};
export type Tx = {signature:string;ts:number|null;slot:number;status:string;type:string|null;fee_lamports:number|null;fee_sol:number|null;explorer_url:string;solscan_url:string};
export type Transactions = {wallet:string;kind:"REAL";transactions:Tx[];next_cursor:string|null;warning:string|null;provider:string;retrieved_at:string;limitations:string[]};
export type PriceHistory = {mint:string;kind:"REAL";points:{ts:number;price_usd:number}[];provider:string;resolution_seconds:number;retrieved_at:string;limitations:string[]};
export type PortfolioHistory = {wallet:string;kind:"REAL";points:{ts:number;sol_balance:number;valued_usd:number|null;complete:number}[];limitations:string[]};
export type Session = {wallet:string;expires_at:number};
export type LiveStatus = {network:string;rpc:boolean;rpc_provider:string;helius:boolean;birdeye:boolean;authentication:boolean;history_provider:string;engine:string};
export type RawHistory = {wallet:string;transactions:Record<string,unknown>[];next_cursor:string|null;coverage_complete:boolean;provider:string;retrieved_at:string;requested_start:number;requested_end:number};
const inFlight = new Map<string,Promise<unknown>>(), cached = new Map<string,{value:unknown;until:number}>();
export class ChainError extends Error {constructor(message:string,public status:number){super(message);}}
export async function chainRequest<T>(path:string, options:{body?:unknown;method?:string;signal?:AbortSignal;ttl?:number}={}):Promise<T>{
  const method=options.method||(options.body===undefined?"GET":"POST"),key=chainBase+path;
  const work=async()=>{
    let response:Response;
    try{response=await fetch(key,{method,credentials:"include",headers:options.body===undefined?{}:{"Content-Type":"application/json"},body:options.body===undefined?undefined:JSON.stringify(options.body),signal:options.signal||AbortSignal.timeout(45000)});}
    catch(e){if(e instanceof Error&&e.name==="AbortError")throw e;throw new ChainError("The Solana data service could not be reached. Check the connection and retry.",503);}
    const data=await response.json().catch(()=>({detail:"The server returned an invalid response."}));
    if(!response.ok)throw new ChainError(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail),response.status);
    if(method==="GET"&&options.ttl){if(cached.size>128)cached.delete(cached.keys().next().value!);cached.set(key,{value:data,until:Date.now()+options.ttl*1000});}return data as T;
  };
  if(method!=="GET"||options.signal)return work();
  const hit=cached.get(key);if(hit&&hit.until>Date.now())return hit.value as T;
  if(inFlight.has(key))return inFlight.get(key) as Promise<T>;
  const promise=work().finally(()=>inFlight.delete(key));inFlight.set(key,promise);return promise;
}
export const shortAddress=(s:string)=>s.slice(0,5)+"…"+s.slice(-4);
export const SOL_MINT="So11111111111111111111111111111111111111112";
export async function walletHistory(wallet:string,start:number,end:number,maxPages=10,onProgress?:(page:number)=>void,control?:{signal?:AbortSignal;beforeRequest?:()=>void}):Promise<RawHistory>{
  const seen=new Map<string,Record<string,unknown>>();let cursor:string|null=null,complete=false,meta:RawHistory|undefined;
  for(let page=0;page<maxPages;page++){
    control?.beforeRequest?.();
    const r:RawHistory=await chainRequest(`/api/wallets/${encodeURIComponent(wallet)}/history?start=${start}&end=${end}${cursor?"&before="+cursor:""}`,{signal:control?.signal});
    meta=r;for(const tx of r.transactions)if(typeof tx.signature==="string"&&!seen.has(tx.signature))seen.set(tx.signature,tx);
    onProgress?.(page+1);
    if(r.coverage_complete){complete=true;break;}if(!r.next_cursor||r.next_cursor===cursor)break;cursor=r.next_cursor;
  }
  if(!meta)throw new Error("No historical requests were made.");return {...meta,transactions:[...seen.values()],coverage_complete:complete,next_cursor:complete?null:cursor};
}
export function mergeHistory(previous:RawHistory,update:RawHistory,start:number,end:number,limit=1000):RawHistory{
  if(previous.wallet!==update.wallet)throw new Error("Historical updates must belong to the same wallet.");
  const rows=[...new Map([...previous.transactions,...update.transactions].filter(t=>typeof t.signature==="string"&&(typeof t.timestamp!=="number"||t.timestamp>=start&&t.timestamp<=end)).map(t=>[t.signature,t])).values()].sort((a,b)=>Number(b.timestamp||0)-Number(a.timestamp||0));
  const complete=previous.coverage_complete&&update.coverage_complete&&rows.length<=limit;
  return {...update,transactions:rows.slice(0,limit),requested_start:start,requested_end:end,coverage_complete:complete,next_cursor:complete?null:update.next_cursor};
}
export type ImportedDataset=Omit<Dataset,"quality"|"content_hash">;

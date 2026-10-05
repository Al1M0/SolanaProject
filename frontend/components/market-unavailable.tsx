"use client";
import Link from "next/link";
import {ShieldAlert,RefreshCw} from "lucide-react";

export default function MarketUnavailable({message,history=false,busy=false,onRetry}:{message:string;history?:boolean;busy?:boolean;onRetry?:()=>void}) {
  const denied=/HTTP (401|403)\b/.test(message),limited=/HTTP 429\b|rate limit/i.test(message);
  return <div className="provider-unavailable" role="alert"><ShieldAlert size={23} aria-hidden="true"/><div className="grow"><h3>{history?"Price history is unavailable":"Live prices are unavailable"}</h3>
    <p>{denied?"The data provider refused this server's request. Its response does not tell us whether the cause is account access, the plan or a network restriction.":limited?"The data provider is limiting requests. Wait before trying again.":"The data service could not return usable observations. The actual error is retained below."}</p>
    <p>{history?"The chart stays empty until real observations are returned.":"Prices stay unavailable until an actual source responds."} You can still inspect the clearly labeled synthetic audit.</p>
    <div className="button-row">{onRetry&&<button type="button" className="button" disabled={busy} onClick={onRetry}><RefreshCw size={16}/>Retry this page</button>}<Link className="button" href="/audit/">Open audit workflow</Link></div>
    <details><summary>Provider response</summary><p className="mono">{message}</p></details>
  </div></div>;
}

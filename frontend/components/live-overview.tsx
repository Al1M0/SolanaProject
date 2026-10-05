"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {Wallet,Radio} from "lucide-react";
import {useWallet} from "./wallet-provider";
import {chainRequest,shortAddress,TokenMarket} from "@/lib/chain";
import {Badge,Notice} from "./workspace";
import {money,quantity,change} from "./chain-chart";
export default function LiveOverview(){const w=useWallet(),[market,setMarket]=useState<TokenMarket|null>(null),[error,setError]=useState("");useEffect(()=>{let active=true;chainRequest<TokenMarket>("/api/markets/sol",{ttl:60}).then(r=>{if(active)setMarket(r);}).catch(e=>{if(active)setError(String(e.message));});return()=>{active=false;};},[]);
  return <section className="panel live-overview"><div className="panel-heading"><h2><Wallet size={18}/>Mainnet workspace</h2><Badge kind="REAL"/></div><div className="stat-grid"><div className="stat"><span>Connected wallet</span><strong className="address-stat">{w.address?shortAddress(w.address):"Disconnected"}</strong><small>{w.address?<Link href="/wallet/">Inspect balances and activity</Link>:"Use Connect Wallet to approve Phantom"}</small></div><div className="stat"><span>SOL balance</span><strong>{quantity(w.snapshot?.sol_balance,6)}</strong><small>{w.loading?"Reading mainnet…":"Connected wallet, confirmed RPC"}</small></div><div className="stat"><span>{w.snapshot?.portfolio_complete?"Estimated portfolio":"Valued subtotal"}</span><strong>{money(w.snapshot?.valued_subtotal_usd)}</strong><small>{w.snapshot?`${w.snapshot.unpriced_tokens} unpriced token holdings`:"Connect a wallet to read holdings"}</small></div><div className="stat"><span>SOL market</span><strong>{money(market?.price_usd)}</strong><small>{market?`${change(market.change_24h_pct)} · 24h · ${market.provider}`:"Market data unavailable"}</small></div></div>{error&&<Notice>{error}</Notice>}<div className="button-row"><Link className="button" href="/markets/">Markets</Link><Link className="button" href="/research/">Research wallets</Link><Link className="button" href="/live/"><Radio size={16}/>Monitor accumulation</Link></div></section>;
}

"use client";
import Link from "next/link";
import {ArrowUpRight,ArrowRight,Database,FlaskConical,Check,Layers,Clock,Activity,Wallet,ShieldCheck} from "lucide-react";
import {useWorkspace,Badge} from "./workspace";
import {num,pct,day} from "@/lib/format";
import LiveOverview from "./live-overview";

export default function Dashboard(){
  const {datasets,strategies,runs}=useWorkspace();
  const strategy=strategies.find(s=>s.id==="strategy-demo")||strategies[0];
  const dataset=datasets.find(d=>d.id===strategy?.dataset_id)||datasets.find(d=>d.id==="synthetic-seed-33")||datasets[0];
  const completed=runs.filter(r=>r.status==="completed");
  const latest=completed[0];
  return <>
    <div className="page-heading desk-heading"><div><div className="eyebrow">THE RESEARCH DESK</div><h1>Your next idea starts here.</h1><p>Follow a signal. Question the assumptions. Keep the evidence.</p></div><Link className="text-link" href="/datasets/">Explore datasets <ArrowUpRight size={16}/></Link></div>
    <div className="dashboard-grid desk-intro">
      <section className="panel hypothesis-hero">
        <div className="hero-label"><span className="small-label">REFERENCE HYPOTHESIS</span>{dataset&&<Badge kind={dataset.kind}/>}</div>
        <h2>Follow the wallets.<br/><em>Question the signal.</em></h2>
        <p className="hero-question">Does a smart-money hypothesis beat a comparable baseline after costs on a separate evaluation period?</p>
        <div className="hero-hypothesis"><FlaskConical size={19}/><div><b>{strategy?.name||"Smart Money Accumulation"}</b><p>{strategy?.config.hypothesis||"When several previously profitable wallets buy the same token, does the signal survive trading costs?"}</p></div></div>
        <div className="hero-action"><Link className="button primary" href="/audit/">Audit this hypothesis <ArrowRight size={18}/></Link><span><Clock size={15}/>{dataset?`${day(dataset.start_ts)} – ${day(dataset.end_ts)} · ${dataset.tokens.length} tokens · UTC`:"Choose a dataset to begin"}</span></div>
        <div className="hero-footer">Train <span>→</span> Freeze <span>→</span> Compare holdout <span>→</span> Export evidence</div>
      </section>
      <section className="panel integrity-card">
        <div className="panel-heading"><h2>Before the numbers</h2><ShieldCheck size={21} className="mint"/></div>
        {dataset?<><div className="integrity-dataset"><Badge kind={dataset.kind}/><b>{dataset.name}</b></div><div className="quality-score"><strong>{num(dataset.quality.price_coverage_pct,0)}<span>%</span></strong><div>Historical price coverage<small>{dataset.quality.performance_ready?"Required market fields present":"Performance calculations blocked"}</small></div></div>
          <div className="coverage-track" aria-hidden="true"><span style={{width:`${Math.max(0,Math.min(100,dataset.quality.price_coverage_pct))}%`}}/></div>
          <div className="quality-list">{[["Historical liquidity",`${num(dataset.quality.liquidity_coverage_pct,0)}%`],["Missing market bars",dataset.quality.missing_bars],["Supported swaps",num(dataset.quality.swap_events,0)]].map(([label,value])=><div key={String(label)}><span>{label}</span><b>{value}</b></div>)}</div>
          <p className="integrity-disclosure">{dataset.kind==="SYNTHETIC"?"Simulated observations. These results do not represent actual Solana returns.":"Actual observations. Inspect provenance and exclusions before interpreting results."}</p>
          <Link className="text-link" href="/datasets/">Inspect data & provenance <ArrowUpRight size={16}/></Link>
        </>:<p>No dataset loaded. Add observations to begin a study.</p>}
      </section>
    </div>
    <div className="stat-grid desk-stats">
      <div className="stat"><span><Database size={16}/>Research datasets</span><strong>{num(datasets.length,0)}</strong><small>{datasets.filter(d=>d.quality.performance_ready).length} ready for evaluation</small></div>
      <div className="stat"><span><Wallet size={16}/>Observed wallets</span><strong>{num(dataset?.wallets.length,0)}</strong><small>In this selected universe</small></div>
      <div className="stat"><span><Layers size={16}/>Market observations</span><strong>{num(dataset?.quality.market_observations,0)}</strong><small>{dataset?`${num(dataset.resolution_seconds/60,0)}-minute historical snapshots`:"No dataset loaded"}</small></div>
      <div className="stat"><span><FlaskConical size={16}/>Completed backtests</span><strong>{num(completed.length,0)}</strong><small>{strategies.length} saved {strategies.length===1?"configuration":"configurations"}</small></div>
    </div>
    <section className="panel"><div className="panel-heading"><div><div className="eyebrow">YOUR NOTEBOOK</div><h2>Research projects</h2><p>Saved hypotheses and strategy configurations.</p></div><Link className="text-link" href="/lab/">Open strategy lab <ArrowUpRight size={16}/></Link></div><div className="project-list">{strategies.slice(0,4).map(s=><Link key={s.id} href={`/lab/?strategy=${s.id}`} className="project-row"><div className="icon-box small"><FlaskConical size={18}/></div><div className="grow"><b>{s.name}</b><small>{s.config.min_wallet_count} wallets · {s.config.accumulation_minutes}m accumulation · {s.config.holding_minutes}m hold</small></div><Badge kind={datasets.find(d=>d.id===s.dataset_id)?.kind||"SYNTHETIC"}/><span className="tag">{num(s.config.train_fraction*100,0)} / {num((1-s.config.train_fraction)*100,0)} split</span><ArrowUpRight className="subtle project-arrow" size={17}/></Link>)}</div>{!strategies.length&&<p>No saved configurations yet.</p>}</section>
    <section className="panel"><div className="panel-heading"><div><h2>Backtest history</h2><p>Exploratory runs. Use Audit hypothesis for frozen experiments and benchmark comparisons.</p></div><Activity size={19} className="subtle"/></div>{runs.length?<div className="table-wrap"><table><thead><tr><th>Backtest</th><th>Dataset</th><th>Status</th><th>OOS net return</th><th>Closed trades</th><th>Created</th></tr></thead><tbody>{runs.slice(0,6).map(r=>{const net=r.summary?.out_of_sample.net_return_pct;return <tr key={r.id}><td><Link className="text-link" href={`/results/?run=${r.id}`}>{r.config.name}</Link><small className="mono">{r.id.slice(-8)}</small></td><td><Badge kind={r.summary?.dataset_kind||datasets.find(d=>d.id===r.dataset_id)?.kind||"SYNTHETIC"}/></td><td><span className={`status ${r.status}`}>{r.status==="completed"&&<Check size={13}/>} {r.status}</span></td><td className={net==null?"":net<0?"negative":"positive"}>{pct(net)}</td><td>{r.summary?.out_of_sample.trade_count??"—"}</td><td className="subtle">{new Date(r.created_at).toLocaleDateString("en-GB",{timeZone:"UTC"})}</td></tr>;})}</tbody></table></div>:<div className="inline-empty"><div className="icon-box"><Activity size={24}/></div><div><h3>A question is a good place to start.</h3><p>The audit records your attempts, including negative and inconclusive results.</p></div></div>}</section>
    {latest&&<div className="notice neutral"><Check size={17}/><span>Latest completed backtest: out-of-sample net return <b>{pct(latest.summary?.out_of_sample.net_return_pct)}</b>. <Link href={`/results/?run=${latest.id}`}>Inspect the evidence</Link></span></div>}
    <LiveOverview/>
    <div className="bottom-note"><Database size={16}/><span>Coverage: {dataset?`${day(dataset.start_ts)} – ${day(dataset.end_ts)} (UTC)` :"No dataset"}. A positive backtest does not establish alpha.</span></div>
  </>;
}

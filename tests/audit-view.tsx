import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {renderToStaticMarkup} from "react-dom/server";
import {buildAuditCurve} from "../frontend/lib/audit-chart";
import Comparison from "../frontend/components/audit-comparison";
import type {AuditResult} from "../frontend/components/audit";
import type {Point} from "../frontend/lib/types";
import {auditGuide,costVerdict} from "../frontend/lib/audit-guide";
import AuditNextStep from "../frontend/components/audit-next-step";
import MarketUnavailable from "../frontend/components/market-unavailable";

const point=(ts:number,net_equity:number):Point=>({ts,net_equity,gross_equity:net_equity,drawdown_pct:0,cash:net_equity,open_positions:0,reserved_cash:0});

test("comparison preserves asynchronous observations as gaps, without forward or backward fills",()=>{
  const results={strategy:{valid:true,equity_curve:[point(30,120),point(10,100)]},buy_and_hold:{valid:true,equity_curve:[point(20,105),point(30,108)]},momentum:{valid:true,equity_curve:[point(10,100),point(20,0)]}};
  const original=JSON.stringify(results);
  assert.deepEqual(buildAuditCurve(results),[
    {ts:10,strategy:100,buy_and_hold:null,momentum:100},
    {ts:20,strategy:null,buy_and_hold:105,momentum:0},
    {ts:30,strategy:120,buy_and_hold:108,momentum:null},
  ]);
  assert.equal(JSON.stringify(results),original,"the display must not mutate persisted results");
});

test("an invalid portfolio cannot supply a performance curve",()=>{
  assert.deepEqual(buildAuditCurve({strategy:{valid:false,equity_curve:[point(10,999)]}}),[]);
});

test("nonfinite values cannot become displayed equity or timestamps",()=>{
  assert.deepEqual(buildAuditCurve({strategy:{valid:true,equity_curve:[point(NaN,999),point(10,Infinity),point(20,100)]}}),[
    {ts:10,strategy:null,buy_and_hold:null,momentum:null},
    {ts:20,strategy:100,buy_and_hold:null,momentum:null},
  ]);
});

const reference=JSON.parse(readFileSync("research/reference/results.json","utf8"));
test("both saved reference phases map every chart value to its exact engine observation",()=>{
  for(const phase of [reference.training,reference.holdout] as AuditResult[]){
    const curve=buildAuditCurve(phase.results);
    assert.ok(curve.length>1);
    for(const [key,portfolio] of Object.entries(phase.results)){
      for(const p of portfolio.equity_curve){
        assert.equal(curve.find(row=>row.ts===p.ts)?.[key as "strategy"|"buy_and_hold"|"momentum"],p.net_equity,`${phase.phase}/${key}/${p.ts}`);
      }
    }
    const strategy=phase.results.strategy;
    assert.equal(curve.at(-1)?.strategy,strategy.equity_curve.at(-1)?.net_equity);
  }
});

test("holdout evidence retains synthetic labeling, negative net returns, costs and all benchmark methodology",()=>{
  const audit=reference.holdout as AuditResult;
  const markup=renderToStaticMarkup(<Comparison audit={audit}/>);
  assert.ok(audit.results.strategy.metrics.net_return_pct!<0);
  for(const text of ["SYNTHETIC","-1.92%","+4.24%","-8.88%","$319.68","Wallet hypothesis","Buy-and-hold","Simple momentum","Gross return","Exposure","Turnover","Failed executions","Cost breakdown","Research limitations","does not establish alpha"]){
    assert.ok(markup.includes(text),`evidence missing: ${text}`);
  }
  for(const b of Object.values(audit.benchmarks)){
    assert.ok(markup.includes(b.name));
  }
  assert.ok(markup.includes('class="negative"'));
});

test("the next action follows durable training, freeze and evaluation states",()=>{
  const initial={training:false,holdout:false,frozen:false};
  assert.equal(auditGuide(initial).action,"training");
  assert.equal(auditGuide({...initial,status:"trained",training:true}).action,"freeze");
  assert.equal(auditGuide({...initial,status:"frozen",training:true,frozen:true}).action,"holdout");
  assert.equal(auditGuide({...initial,status:"evaluated",training:true,holdout:true,frozen:true}).action,"export");
  for(const status of ["training","evaluating","holdout_failed","evaluated"]){
    const guide=auditGuide({...initial,status,frozen:true});
    assert.notEqual(guide.action,"holdout",`an interrupted, failed or incomplete ${status} attempt cannot offer another evaluation`);
  }
});

test("working actions are disabled and progress does not invent a completed result",()=>{
  const markup=renderToStaticMarkup(<AuditNextStep state={{status:"frozen",training:true,holdout:false,frozen:true}} busy={true} progress={0} operation="holdout" disabled={false} exportPrepared={false} onAction={()=>{throw new Error("not user initiated");}} onEvidence={()=>{}}/>);
  assert.ok(markup.includes("Checking the later period"));
  assert.match(markup,/<button[^>]*disabled/);
  assert.match(markup,/<progress[^>]*max="100"/);
  assert.doesNotMatch(markup,/<progress[^>]*value=/);
  assert.doesNotMatch(markup,/Bundle prepared/);
});

test("plain-language verdict distinguishes costs, losses and missing data without claiming alpha",()=>{
  assert.equal(costVerdict(true,1,-1).title,"Costs erase the observed gain");
  assert.match(costVerdict(true,-1,-2).detail,/negative research result/);
  assert.match(costVerdict(true,2,1).detail,/does not establish alpha/);
  for(const [valid,gross,net] of [[false,10,10],[true,null,0],[true,NaN,10],[true,10,Infinity]] as [boolean,number|null,number|null][]){
    assert.equal(costVerdict(valid,gross,net).title,"No usable performance result");
  }
});

test("invalid saved portfolios cannot display apparent returns in cards or the full table",()=>{
  const audit=structuredClone(reference.holdout) as AuditResult;
  for(const r of Object.values(audit.results)){r.valid=false;r.metrics.net_return_pct=99999;r.metrics.gross_return_pct=88888;r.metrics.max_drawdown_pct=77777;r.metrics.costs_usd=66666;}
  const markup=renderToStaticMarkup(<Comparison audit={audit}/>);
  assert.match(markup,/No usable performance result/);
  for(const value of ["99,999","88,888","77,777","66,666"]){assert.ok(!markup.includes(value));}
  assert.match(markup,/Insufficient observations/);
});

test("denied market access explains missing observations, retains HTTP evidence and offers the audit",()=>{
  const markup=renderToStaticMarkup(<MarketUnavailable message="CoinGecko rejected the request (HTTP 403)." busy={true} onRetry={()=>{}}/>);
  for(const text of ["Live prices are unavailable","does not tell us whether","HTTP 403","synthetic audit","Provider response"]){assert.ok(markup.includes(text),`missing provider explanation: ${text}`);}
  assert.match(markup,/href="\/audit\/?"/);
  assert.match(markup,/<button[^>]*disabled/);
  assert.doesNotMatch(markup,/Upgrade|Purchase|guarantee/);
});

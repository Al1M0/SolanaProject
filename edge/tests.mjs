// Runs the exact hosted code against the committed migration and real WebCrypto.
import {test,after} from "node:test";
import assert from "node:assert/strict";
import {DatabaseSync} from "node:sqlite";
import {mkdtempSync,readFileSync,rmSync,readdirSync} from "node:fs";
import {tmpdir} from "node:os";
import path from "node:path";
import {pathToFileURL,fileURLToPath} from "node:url";
import {build} from "esbuild";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const temporary=mkdtempSync(path.join(tmpdir(),"quant-edge-test-"));
await build({stdin:{contents:'export {default as worker} from "./edge/index.ts"; export * from "./edge/runtime.ts"; export * from "./edge/solana.ts"; export * from "./edge/market.ts";',resolveDir:root,loader:"ts"},bundle:true,format:"esm",platform:"node",outfile:path.join(temporary,"edge.mjs")});
const {worker,SolanaService,WalletService,MarketDataService,remember,address,WSOL}=await import(pathToFileURL(path.join(temporary,"edge.mjs")));
after(()=>rmSync(temporary,{recursive:true,force:true}));
const origin="https://quant.example.test";
const alphabet="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
function base58(bytes){let n=0n;for(const b of bytes)n=n*256n+BigInt(b);let out="";while(n){out=alphabet[Number(n%58n)]+out;n/=58n;}for(const b of bytes){if(b!==0)break;out="1"+out;}return out;}
async function identity(){const keys=await crypto.subtle.generateKey({name:"Ed25519"},true,["sign","verify"]);const wallet=base58(new Uint8Array(await crypto.subtle.exportKey("raw",keys.publicKey)));return {wallet,async sign(message){return Buffer.from(await crypto.subtle.sign("Ed25519",keys.privateKey,new TextEncoder().encode(message))).toString("base64");}};}
function database(t){
  const sql=new DatabaseSync(":memory:");for(const file of readdirSync(path.join(root,"drizzle")).filter(f=>f.endsWith(".sql")).sort())sql.exec(readFileSync(path.join(root,"drizzle",file),"utf8"));t.after(()=>sql.close());
  class Statement{constructor(query,values=[]){this.query=query;this.values=values;}bind(...values){return new Statement(this.query,values);}async first(){return sql.prepare(this.query).get(...this.values)||null;}async all(){return {results:sql.prepare(this.query).all(...this.values)};}async run(){return {meta:{changes:Number(sql.prepare(this.query).run(...this.values).changes)}};}}
  return {sql,env:{APP_ORIGIN:origin,DB:{prepare:query=>new Statement(query),async batch(statements){sql.exec("BEGIN");try{const out=statements.map(s=>({meta:{changes:Number(sql.prepare(s.query).run(...s.values).changes)}}));sql.exec("COMMIT");return out;}catch(e){sql.exec("ROLLBACK");throw e;}}}}};
}
function request(route,body,extra={}){return new Request(origin+route,{method:body===undefined?"GET":"POST",headers:{...(body===undefined?{}:{Origin:origin,"Content-Type":"application/json"}),...extra},body:body===undefined?undefined:JSON.stringify(body)});}
async function challenge(env,key){const response=await worker.fetch(request("/api/auth/nonce",{wallet:key.wallet}),env);assert.equal(response.status,200);return response.json();}
async function login(env,key){const nonce=await challenge(env,key);const response=await worker.fetch(request("/api/auth/verify",{id:nonce.id,wallet:key.wallet,signature:await key.sign(nonce.message)}),env);assert.equal(response.status,200);return response;}

test("hosted login verifies Ed25519, stores only a session hash, and blocks replay",async t=>{
  const {sql,env}=database(t),key=await identity(),nonce=await challenge(env,key);
  assert.match(nonce.message,/Chain ID: solana:mainnet/);assert.match(nonce.message,/quant\.example\.test/);
  const body={id:nonce.id,wallet:key.wallet,signature:await key.sign(nonce.message)};
  const response=await worker.fetch(request("/api/auth/verify",body),env);assert.equal(response.status,200);
  const cookie=response.headers.get("set-cookie");assert.match(cookie,/HttpOnly/);assert.match(cookie,/SameSite=Lax/);assert.match(cookie,/Secure/);
  const raw=cookie.split(";")[0].split("=")[1];assert.notEqual(sql.prepare("SELECT token_hash FROM wallet_sessions").get().token_hash,raw);
  const sessionResponse=await worker.fetch(request("/api/auth/session",undefined,{Cookie:cookie}),env);assert.equal((await sessionResponse.json()).session.wallet,key.wallet);
  assert.equal((await worker.fetch(request("/api/auth/verify",body),env)).status,401);
  assert.equal((await worker.fetch(request("/api/auth/logout",{}, {Cookie:cookie}),env)).status,200);
  assert.equal((await (await worker.fetch(request("/api/auth/session",undefined,{Cookie:cookie}),env)).json()).session,null);
});
test("simultaneous verification consumes one nonce exactly once",async t=>{
  const {env}=database(t),key=await identity(),nonce=await challenge(env,key),signature=await key.sign(nonce.message);
  const out=await Promise.all([1,2].map(()=>worker.fetch(request("/api/auth/verify",{id:nonce.id,wallet:key.wallet,signature}),env)));
  assert.deepEqual(out.map(r=>r.status).sort(),[200,401]);
});
test("expired and invalid signatures cannot create sessions",async t=>{
  const {sql,env}=database(t),key=await identity(),nonce=await challenge(env,key);
  const bad={id:nonce.id,wallet:key.wallet,signature:Buffer.alloc(64).toString("base64")};
  assert.equal((await worker.fetch(request("/api/auth/verify",bad),env)).status,401);
  assert.equal((await worker.fetch(request("/api/auth/verify",{...bad,signature:await key.sign(nonce.message)}),env)).status,401);
  const expired=await challenge(env,key);sql.prepare("UPDATE wallet_nonces SET expires_at=0 WHERE id=?").run(expired.id);
  assert.equal((await worker.fetch(request("/api/auth/verify",{id:expired.id,wallet:key.wallet,signature:await key.sign(expired.message)}),env)).status,401);
  assert.equal(sql.prepare("SELECT COUNT(*) AS n FROM wallet_sessions").get().n,0);
});
test("origin, wallet substitution, malformed input, and nonce rate limit are enforced",async t=>{
  const {env}=database(t),key=await identity(),other=await identity(),nonce=await challenge(env,key);
  assert.equal((await worker.fetch(request("/api/auth/nonce",{wallet:key.wallet},{Origin:"https://foreign.example.test"}),env)).status,403);
  assert.equal((await worker.fetch(request("/api/auth/verify",{id:nonce.id,wallet:other.wallet,signature:await key.sign(nonce.message)}),env)).status,401);
  assert.equal((await worker.fetch(request("/api/auth/nonce",{wallet:"fake-wallet"}),env)).status,422);
  for(let i=0;i<4;i++)await challenge(env,key);
  assert.equal((await worker.fetch(request("/api/auth/nonce",{wallet:key.wallet}),env)).status,429);
});
test("signed sessions cannot read or write another wallet's observations",async t=>{
  const {env}=database(t),key=await identity(),other=await identity(),response=await login(env,key),Cookie=response.headers.get("set-cookie");
  assert.equal((await worker.fetch(request(`/api/wallets/${other.wallet}/observations`,undefined,{Cookie}),env)).status,401);
  assert.equal((await worker.fetch(request(`/api/wallets/${other.wallet}/observations`,{}, {Cookie}),env)).status,401);
  const rows=await worker.fetch(request(`/api/wallets/${key.wallet}/observations`,undefined,{Cookie}),env);assert.equal(rows.status,200);assert.deepEqual((await rows.json()).points,[]);
});
test("hosted observations derive values on the server and deduplicate concurrent saves",async t=>{
  const {sql,env}=database(t),key=await identity(),response=await login(env,key),Cookie=response.headers.get("set-cookie");
  t.mock.method(WalletService.prototype,"snapshot",async wallet=>({wallet,sol_balance:2,valued_subtotal_usd:250,portfolio_complete:false,retrieved_at:new Date().toISOString()}));
  const out=await Promise.all([1,2].map(()=>worker.fetch(request(`/api/wallets/${key.wallet}/observations`,{valued_subtotal_usd:999999},{Cookie}),env)));
  assert.deepEqual(out.map(r=>r.status),[200,200]);const rows=sql.prepare("SELECT valued_usd, complete FROM wallet_snapshots").all();assert.equal(rows.length,1);assert.equal(rows[0].valued_usd,250);assert.equal(rows[0].complete,0);
});
test("missing storage/provider credentials and database failures return sanitized errors",async()=>{
  assert.equal((await worker.fetch(request("/api/auth/nonce",{wallet:WSOL}),{})).status,503);
  assert.equal((await worker.fetch(request(`/api/wallets/${WSOL}/history?start=1704067200&end=1704067500`),{})).status,503);
  const response=await worker.fetch(request("/api/auth/nonce",{wallet:WSOL}),{APP_ORIGIN:origin,DB:{prepare(){throw new Error("sensitive SQL provider credentials");}}});
  assert.equal(response.status,503);assert.doesNotMatch(await response.text(),/sensitive|credentials/);
});
test("cache deduplicates concurrent calls and evicts failed in-flight work",async()=>{
  let calls=0;const key="unit-cache-"+crypto.randomUUID(),work=async()=>{calls++;await new Promise(r=>setTimeout(r,5));return {real:true};};
  const result=await Promise.all([1,2,3].map(()=>remember(key,60,work)));assert.equal(calls,1);assert.deepEqual(result[0],{real:true});
  const failed="unit-failed-"+crypto.randomUUID();await assert.rejects(remember(failed,10,async()=>{throw new Error("failed");}));assert.equal(await remember(failed,10,async()=>42),42);
});
test("denied aggregated SOL access falls back once to an actual wSOL base-token quote",async t=>{
  const calls=[];
  t.mock.method(globalThis,"fetch",async url=>{
    calls.push(String(url));
    if(String(url).includes("api.coingecko.com"))return new Response(null,{status:403});
    return Response.json([{chainId:"solana",baseToken:{address:WSOL,symbol:"SOL"},priceUsd:"140",liquidity:{usd:2000},pairAddress:"pool-fixture",dexId:"fixture-dex"}]);
  });
  const quote=await new MarketDataService({COINGECKO_DEMO_API_KEY:"denied-fixture"}).sol();
  assert.equal(calls.length,2);assert.match(calls[1],/api\.dexscreener\.com/);
  assert.equal(quote.price_usd,140);assert.equal(quote.provider,"DEX Screener");assert.equal(quote.pair_address,"pool-fixture");assert.equal(quote.market_cap_usd,null);
  assert.match(quote.limitations.at(-1),/HTTP 403.*actual wSOL pool/);
});
test("an unusable SOL alternative stays unavailable and retains both failures",async t=>{
  t.mock.method(globalThis,"fetch",async()=>new Response(null,{status:403}));
  const service=new MarketDataService({COINGECKO_DEMO_API_KEY:"denied-and-missing-fixture"});
  t.mock.method(service,"tokens",async()=>[]);
  await assert.rejects(service.sol(),error=>error.status===503&&/HTTP 403.*No usable wSOL/.test(error.message));
});
test("SOL history uses configured Birdeye access and excludes unclosed or missing prices",async t=>{
  const now=1767229200000,calls=[];
  t.mock.method(Date,"now",()=>now);
  t.mock.method(globalThis,"fetch",async(url,options)=>{
    calls.push({url:String(url),options});
    return Response.json({success:true,data:{items:[{unixTime:1767225600,value:140},{unixTime:1767222000,value:null},{unixTime:1767229200,value:150},{unixTime:1767218400,value:-1}]}});
  });
  const data=await new MarketDataService({BIRDEYE_API_KEY:"unit-test-fixture"}).history(WSOL,1);
  assert.equal(calls.length,1);assert.match(calls[0].url,/public-api\.birdeye\.so/);
  assert.match(calls[0].url,/type=1H/);assert.match(calls[0].url,/ui_amount_mode=raw/);
  assert.equal(data.provider,"Birdeye");assert.equal(data.kind,"REAL");
  assert.deepEqual(data.points,[{ts:1767229200,price_usd:140}]);
  assert.match(data.limitations.at(-1),/no historical liquidity/);
});
test("mainnet RPC preserves exact token amounts across reordered SPL and Token-2022 batches",async t=>{
  const env={SOLANA_RPC_URL:"https://rpc-unit-"+crypto.randomUUID()+".invalid"},mint=base58(new Uint8Array(32).fill(7)),tiny=base58(new Uint8Array(32).fill(8));
  const account=(mint,raw,decimals,extensions=[])=>({account:{owner:"token-program",data:{parsed:{info:{mint,tokenAmount:{amount:raw,decimals},extensions}}}}});
  t.mock.method(globalThis,"fetch",async(_url,init)=>Response.json(JSON.parse(init.body).reverse().map(c=>({id:c.id,result:c.method==="getGenesisHash"?"5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d":c.method==="getBalance"?{value:1234567890,context:{slot:100}}:{value:c.id===1?[account(mint,"9007199254740993",9),account(tiny,"1",24)]:[account(mint,"2",9,[{extension:"scaledUiAmountConfig"}])]}}))));
  const data=await new SolanaService(env).balances(WSOL);assert.equal(data.sol_balance,1.23456789);assert.equal(data.tokens[0].raw_amount,"9007199254740995");assert.equal(data.tokens[0].amount,"9007199.254740995");assert.equal(data.tokens[0].valuation_supported,false);assert.equal(data.tokens[1].amount,"0.000000000000000000000001");assert.equal(data.kind,"REAL");assert.equal(data.network,"mainnet-beta");
});
test("a non-mainnet RPC is rejected instead of being presented as mainnet",async t=>{
  t.mock.method(globalThis,"fetch",async()=>Response.json([{id:0,result:"testnet-genesis"}]));
  await assert.rejects(new SolanaService({SOLANA_RPC_URL:"https://testnet-unit.invalid"}).balances(WSOL),/mainnet-beta/);
});
test("DEX quotes use the requested base mint and leave missing metadata and liquidity unknown",async t=>{
  const mint=base58(new Uint8Array(32).fill(9));
  t.mock.method(globalThis,"fetch",async()=>Response.json([{chainId:"solana",baseToken:{address:WSOL},quoteToken:{address:mint},priceUsd:"999",liquidity:{usd:100000000}},{chainId:"solana",baseToken:{address:mint},priceUsd:"0.25"}]));
  const rows=await new MarketDataService({}).tokens([mint]);assert.equal(rows.length,1);assert.equal(rows[0].price_usd,.25);assert.equal(rows[0].symbol,null);assert.equal(rows[0].liquidity_usd,null);assert.equal(rows[0].market_cap_usd,null);
});
test("token and address validation never accepts short or non-base58 placeholders",()=>{
  assert.equal(address(WSOL),WSOL);assert.throws(()=>address("fake_wallet"));assert.throws(()=>address("111"));
});

test("hosted historical marks retain missing prices and defer bucket availability",async t=>{
  const start=1767225600,end=start+300,mint=base58(crypto.getRandomValues(new Uint8Array(32)));
  t.mock.method(globalThis,"fetch",async()=>Response.json({success:true,data:{items:[{unixTime:start,value:12},{unixTime:end,value:null}]}}));
  const response=await worker.fetch(request(`/api/markets/${mint}/research-prices?start=${start}&end=${end}`),{BIRDEYE_API_KEY:"unit-test-fixture"});
  assert.equal(response.status,200);const data=await response.json();assert.equal(data.kind,"REAL");
  assert.deepEqual(data.prices,[{ts:start+300,source_price_ts:start,price_usd:12},{ts:end+300,source_price_ts:end,price_usd:null}]);
});
test("hosted research rejects corrupt timestamps and non-positive prices before import",async t=>{
  const start=1767225600,end=start+300;
  for(const row of [null,{}, {unixTime:String(start),value:1},{unixTime:start+1,value:1},{unixTime:end+300,value:1},{unixTime:start,value:-1}]){
    const mint=base58(crypto.getRandomValues(new Uint8Array(32)));
    const mock=t.mock.method(globalThis,"fetch",async()=>Response.json({success:true,data:{items:[row]}}));
    const response=await worker.fetch(request(`/api/markets/${mint}/research-prices?start=${start}&end=${end}`),{BIRDEYE_API_KEY:"unit-test-fixture"});
    assert.equal(response.status,502);assert.match((await response.json()).detail,/Historical provider/);mock.mock.restore();
  }
});
test("hosted research rejects future or negative liquidity and preserves unknown depth",async t=>{
  const anchor=1767225900;
  for(const row of [{unix_time:anchor,exit_liquidity_usd:null,liquidity_usd:1000},{unix_time:anchor+60,exit_liquidity_usd:1000},{unix_time:anchor,exit_liquidity_usd:-1}]){
    const mint=base58(crypto.getRandomValues(new Uint8Array(32)));
    const mock=t.mock.method(globalThis,"fetch",async()=>Response.json({success:true,data:{items:[row]}}));
    const response=await worker.fetch(request(`/api/markets/${mint}/research-liquidity?time=${anchor}`),{BIRDEYE_API_KEY:"unit-test-fixture"});
    if(row.exit_liquidity_usd===null){assert.equal(response.status,200);assert.deepEqual((await response.json()).items,[{ts:anchor,liquidity_usd:null,total_liquidity_usd:1000}]);}
    else assert.equal(response.status,502);mock.mock.restore();
  }
});

test("provider readiness distinguishes missing credentials from endpoint entitlement",async()=>{
  const response=await worker.fetch(request("/api/providers/readiness",{}),{APP_ORIGIN:origin});
  assert.equal(response.status,200);const data=await response.json();assert.equal(data.ready,false);assert.deepEqual(data.checks.map(c=>c.status),["missing_key","missing_key","missing_key"]);
});
test("hosted manifests freeze in persistent storage and permit only one holdout",async t=>{
  const {env,sql}=database(t);
  const initial=await worker.fetch(request("/api/experiments"),env),Cookie=initial.headers.get("set-cookie");
  const m={experiment_id:"exp_"+"a".repeat(24),dataset_content_hash:"b".repeat(64),dataset_kind:"SYNTHETIC",configuration:{fee_bps:30},token_universe:["fixture"],split:{training_end:1,holdout_start:2},source_revision:"fixture"};
  const raw=JSON.stringify(m),manifest_hash=Buffer.from(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(raw))).toString("hex");
  const created=await worker.fetch(request("/api/experiments",{manifest_json:raw,manifest_hash},{Cookie}),env);assert.equal(created.status,201);
  const route=`/api/experiments/${m.experiment_id}`;
  assert.equal((await worker.fetch(request(route+"/evaluate",{},{Cookie}),env)).status,409);
  assert.equal((await worker.fetch(request(route+"/training",{fingerprint:"c".repeat(64)},{Cookie}),env)).status,200);
  const frozen=await worker.fetch(request(route+"/freeze",{},{Cookie}),env);assert.equal(frozen.status,200);assert.equal((await frozen.json()).frozen_hash,manifest_hash);
  assert.throws(()=>sql.prepare("UPDATE audit_experiments SET manifest_json='{}' WHERE id=?").run(m.experiment_id),/immutable/);
  assert.throws(()=>sql.prepare("UPDATE audit_experiments SET frozen_hash='changed' WHERE id=?").run(m.experiment_id),/immutable/);
  assert.equal((await worker.fetch(request(route+"/freeze",{},{Cookie}),env)).status,409);
  assert.equal((await worker.fetch(request(route+"/evaluate",{fee_bps:0},{Cookie}),env)).status,422);
  const concurrent=await Promise.all([1,2].map(()=>worker.fetch(request(route+"/evaluate",{},{Cookie}),env)));assert.deepEqual(concurrent.map(r=>r.status).sort(),[200,409]);
  assert.equal((await worker.fetch(request(route+"/holdout",{fingerprint:"d".repeat(64)},{Cookie}),env)).status,200);
  assert.equal((await worker.fetch(request(route+"/evaluate",{},{Cookie}),env)).status,409);
  assert.equal((await worker.fetch(request(route),env)).status,404);
  assert.equal((await worker.fetch(request("/api/experiments",{manifest_json:raw,manifest_hash},{Cookie}),env)).status,409);
  const result=await worker.fetch(request(route,undefined,{Cookie}),env);assert.deepEqual((await result.json()).history.map(h=>h.state),["training","trained","frozen","evaluating","evaluated"]);
});

test("stored canonical manifest text survives JSON number normalization",async t=>{
  const {env}=database(t),initial=await worker.fetch(request('/api/experiments'),env),Cookie=initial.headers.get('set-cookie');
  const raw='{"experiment_id":"exp_'+"e".repeat(24)+'","dataset_content_hash":"'+"f".repeat(64)+'","dataset_kind":"SYNTHETIC","configuration":{"fee_bps":30.0},"token_universe":["fixture"],"split":{"training_end":1,"holdout_start":2},"source_revision":"fixture"}';
  const manifest_hash=Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw))).toString('hex');
  const response=await worker.fetch(request('/api/experiments',{manifest_json:raw,manifest_hash},{Cookie}),env);assert.equal(response.status,201);const e=await response.json();assert.equal(e.manifest_json,raw);assert.equal(e.manifest_hash,manifest_hash);assert.equal(e.manifest.configuration.fee_bps,30);
});

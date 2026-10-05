// Provider mocks stay exclusively in tests. Production always uses Phantom's injected API.
import {test} from "node:test";
import assert from "node:assert/strict";
import {act,create} from "react-test-renderer";
import {WalletProvider,useWallet} from "../frontend/components/wallet-provider";
import {phantomProvider,signatureBase64} from "../frontend/lib/phantom";
import {mergeHistory} from "../frontend/lib/chain";
const A="So11111111111111111111111111111111111111112",B="11111111111111111111111111111111";
const key=(s:string)=>({toString:()=>s});
type Wallet=ReturnType<typeof useWallet>;
async function mount(t:any,options:{installed?:boolean;rejected?:boolean;verifyPaused?:boolean;pendingBalance?:boolean}={}){
  const originalWindow=(globalThis as any).window,originalDocument=(globalThis as any).document,originalFetch=globalThis.fetch;
  (globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
  let connected=false,current=key(A),state:Wallet,signs=0,verifies=0,loggedOut=0,resolveBalance:(r:Response)=>void=()=>{},resolveVerify:(r:Response)=>void=()=>{};
  const listeners=new Map<string,Set<(k?:any)=>void>>(),emit=(event:string,value?:any)=>listeners.get(event)?.forEach(cb=>cb(value));
  const provider={isPhantom:true,get isConnected(){return connected;},get publicKey(){return connected?current:null;},async connect(){if(options.rejected)throw {code:4001};connected=true;emit("connect",current);return {publicKey:current};},async disconnect(){connected=false;emit("disconnect");},async signMessage(message:Uint8Array,display:string){assert.equal(display,"utf8");assert.match(new TextDecoder().decode(message),/nonce/);signs++;return {signature:new Uint8Array(64),publicKey:current};},on(event:string,cb:(k?:any)=>void){if(!listeners.has(event))listeners.set(event,new Set());listeners.get(event)!.add(cb);},removeListener(event:string,cb:(k?:any)=>void){listeners.get(event)?.delete(cb);}};
  (globalThis as any).window=options.installed===false?{}:{phantom:{solana:provider}};(globalThis as any).document={visibilityState:"visible"};
  globalThis.fetch=async(input:any,init?:RequestInit)=>{
    const url=String(input),body=init?.body?JSON.parse(String(init.body)):{};
    if(url.includes("/auth/nonce"))return Response.json({id:"challenge",wallet:body.wallet,message:"Sign in to test origin; nonce: unique",expires_at:Math.floor(Date.now()/1000)+300});
    if(url.includes("/auth/verify")){verifies++;if(options.verifyPaused)return new Promise(r=>resolveVerify=r);return Response.json({wallet:body.wallet,expires_at:Math.floor(Date.now()/1000)+86400});}
    if(url.includes("/auth/logout")){loggedOut++;return Response.json({ok:true});}
    if(url.includes("/auth/session"))return Response.json({session:null});
    if(options.pendingBalance)return new Promise(r=>resolveBalance=r);
    return Response.json({wallet:url.split("/").at(-1),sol_balance:1,kind:"REAL",tokens:[]});
  };
  function Probe(){state=useWallet();return null;}
  let renderer:any;await act(async()=>{renderer=create(<WalletProvider><Probe/></WalletProvider>);});
  t.after(async()=>{await act(async()=>renderer.unmount());(globalThis as any).window=originalWindow;(globalThis as any).document=originalDocument;globalThis.fetch=originalFetch;});
  return {get state(){return state!;},provider,get signs(){return signs;},get verifies(){return verifies;},get loggedOut(){return loggedOut;},async switchAccount(next:string|null){await act(async()=>{if(next)current=key(next);connected=!!next;emit("accountChanged",next?current:null);});},resolveBalance:(r:Response)=>resolveBalance(r),resolveVerify:(r:Response)=>resolveVerify(r)};
}
test("missing Phantom reports an actionable message and creates no wallet",async t=>{const app=await mount(t,{installed:false});await act(async()=>app.state.connect());assert.equal(app.state.address,null);assert.match(app.state.error,/not installed/);assert.equal(app.signs,0);});
test("rejected connect leaves wallet disconnected without signing",async t=>{const app=await mount(t,{rejected:true});await act(async()=>app.state.connect());assert.equal(app.state.address,null);assert.match(app.state.error,/declined/);assert.equal(app.signs,0);});
test("approved connection reads the actual public key; login signs a message and logout clears state",async t=>{const app=await mount(t);await act(async()=>app.state.connect());assert.equal(app.state.address,A);assert.equal(app.state.session,null);await act(async()=>app.state.login());assert.equal(app.signs,1);assert.equal(app.verifies,1);assert.equal(app.state.session?.wallet,A);await act(async()=>app.state.disconnect());assert.equal(app.state.address,null);assert.equal(app.state.snapshot,null);assert.equal(app.state.session,null);assert.ok(app.loggedOut>=1);});
test("account changes revoke local session and clear the old wallet snapshot",async t=>{const app=await mount(t);await act(async()=>app.state.connect());await act(async()=>app.state.login());assert.equal(app.state.session?.wallet,A);await app.switchAccount(B);assert.equal(app.state.address,B);assert.equal(app.state.session,null);assert.notEqual(app.state.snapshot?.wallet,A);assert.ok(app.loggedOut>=1);await app.switchAccount(null);assert.equal(app.state.address,null);assert.equal(app.state.snapshot,null);});
test("a login that finishes after account change cannot authenticate the replacement account",async t=>{const app=await mount(t,{verifyPaused:true});await act(async()=>app.state.connect());let pending:Promise<void>;await act(async()=>{pending=app.state.login();await Promise.resolve();});assert.equal(app.verifies,1);await app.switchAccount(B);await act(async()=>{app.resolveVerify(Response.json({wallet:A,expires_at:Math.floor(Date.now()/1000)+86400}));await pending;});assert.equal(app.state.address,B);assert.equal(app.state.session,null);assert.ok(app.loggedOut>=2);});
test("an old balance response cannot populate a disconnected wallet",async t=>{const app=await mount(t,{pendingBalance:true});await act(async()=>app.state.connect());await act(async()=>app.state.disconnect());await act(async()=>app.resolveBalance(Response.json({wallet:A,sol_balance:9})));assert.equal(app.state.address,null);assert.equal(app.state.snapshot,null);assert.equal(app.state.loading,false);});
test("unverified injected providers and invalid signatures are rejected",()=>{const original=(globalThis as any).window;(globalThis as any).window={solana:{isPhantom:false}};assert.equal(phantomProvider(),null);assert.throws(()=>signatureBase64(new Uint8Array(63)),/invalid/);(globalThis as any).window=original;});
test("incremental finalized-history updates deduplicate overlap and expire old rows",()=>{
  const old:any={wallet:A,coverage_complete:true,transactions:[{signature:"old",timestamp:1},{signature:"same",timestamp:10}]};
  const update:any={wallet:A,coverage_complete:true,transactions:[{signature:"same",timestamp:10},{signature:"new",timestamp:20}]};
  const merged=mergeHistory(old,update,5,20);assert.deepEqual(merged.transactions.map(t=>t.signature),["new","same"]);assert.equal(merged.coverage_complete,true);assert.equal(merged.requested_start,5);
  assert.equal(mergeHistory(old,{...update,coverage_complete:false},5,20).coverage_complete,false);assert.equal(mergeHistory(old,update,5,20,1).coverage_complete,false);assert.throws(()=>mergeHistory(old,{...update,wallet:B},5,20),/same wallet/);
});

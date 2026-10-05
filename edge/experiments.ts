import {ApiError, Env, jsonBody, requiredDB, retrieved} from "./runtime";
import {originFor} from "./auth";
const hash = async (s:string) => Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s)))).map(b=>b.toString(16).padStart(2,"0")).join("");
const sha = (v:unknown):v is string => typeof v === "string" && /^[a-f0-9]{64}$/.test(v);
async function owner(request:Request) {
  let token=request.headers.get("Cookie")?.match(/(?:^|;\s*)quant_audit=([a-f0-9]{64})(?:;|$)/)?.[1];
  const fresh=!token;
  if(!token) token=crypto.randomUUID().replaceAll("-","")+crypto.randomUUID().replaceAll("-","");
  return {owner:await hash(token),cookie:fresh?`quant_audit=${token}; Path=/; HttpOnly; ${new URL(request.url).protocol === "https:" ? "Secure; " : ""}SameSite=Lax; Max-Age=31536000`:undefined};
}
function view(row:Record<string,unknown>,history:unknown[]=[]) {
  return {id:row.id,manifest_json:row.manifest_json,manifest:JSON.parse(row.manifest_json as string),manifest_hash:row.manifest_hash,status:row.status,frozen_hash:row.frozen_hash,error:row.error,created_at:row.created_at,training_fingerprint:row.training_fingerprint,holdout_fingerprint:row.holdout_fingerprint,history,computation:"Client-side shared Python; server stores immutable manifest and lifecycle hashes, not a certification of client results"};
}
export async function experimentRoute(request:Request,env:Env,path:string) {
  const db=requiredDB(env),identity=await owner(request);
  if(request.method==="POST") originFor(request,env);
  const response=(v:unknown,status=200)=>Response.json(v,{status,headers:identity.cookie?{"Set-Cookie":identity.cookie}:{}});
  if(path==="/api/experiments"&&request.method==="GET") {
    const rows=await db.prepare("SELECT * FROM audit_experiments WHERE owner = ? ORDER BY created_at DESC").bind(identity.owner).all();
    return response(rows.results.map(row=>view(row)));
  }
  if(path==="/api/experiments"&&request.method==="POST") {
    const body=await jsonBody(request),raw=body.manifest_json;
    if(typeof raw!=="string"||raw.length>60000||!sha(body.manifest_hash)||await hash(raw)!==body.manifest_hash) throw new ApiError(422,"Manifest content hash mismatch.");
    let m;try{m=JSON.parse(raw);}catch{throw new ApiError(422,"Invalid manifest JSON.");}
    if(!/^exp_[a-f0-9]{24}$/.test(m.experiment_id)||!sha(m.dataset_content_hash)||!["REAL","SYNTHETIC"].includes(m.dataset_kind)||!m.configuration||!Array.isArray(m.token_universe)||!m.token_universe.length||!m.split||typeof m.source_revision!=="string") throw new ApiError(422,"Manifest is incomplete.");
    if(await db.prepare("SELECT id FROM audit_experiments WHERE id = ?").bind(m.experiment_id).first()) throw new ApiError(409,"Experiment already exists; snapshots cannot be overwritten.");
    const count=await db.prepare("SELECT count(*) AS n FROM audit_experiments WHERE owner = ?").bind(identity.owner).first<{n:number}>();
    if((count?.n||0)>=500) throw new ApiError(429,"Workspace attempt limit reached; existing unsuccessful attempts are retained.");
    await db.batch([db.prepare("INSERT INTO audit_experiments (id, owner, manifest_json, manifest_hash, status, created_at) VALUES (?, ?, ?, ?, 'training', ?)").bind(m.experiment_id,identity.owner,raw,body.manifest_hash,retrieved()),db.prepare("INSERT INTO audit_events (experiment_id,state,at) VALUES (?, 'training', ?)").bind(m.experiment_id,retrieved())]);
    return response(view((await db.prepare("SELECT * FROM audit_experiments WHERE id = ? AND owner = ?").bind(m.experiment_id,identity.owner).first())!),201);
  }
  const match=path.match(/^\/api\/experiments\/(exp_[a-f0-9]{24})(?:\/(training|freeze|evaluate|holdout|fail))?$/);
  if(!match) throw new ApiError(404,"Experiment route not found.");
  const [,id,action]=match;
  let row=await db.prepare("SELECT * FROM audit_experiments WHERE id = ? AND owner = ?").bind(id,identity.owner).first();
  if(!row) throw new ApiError(404,"Experiment not found in this workspace.");
  if(request.method==="POST"&&action) {
    const body=await jsonBody(request);if(["freeze","evaluate"].includes(action)&&Object.keys(body).length)throw new ApiError(422,"Locked experiments accept no parameter changes. Create a new attempt.");let from:string,to:string,column:string|undefined,value:unknown;
    if(action==="training") {from="training";to="trained";column="training_fingerprint";value=body.fingerprint;}
    else if(action==="freeze") {from="trained";to="frozen";column="frozen_hash";value=row.manifest_hash;}
    else if(action==="evaluate") {from="frozen";to="evaluating";}
    else if(action==="holdout") {from="evaluating";to="evaluated";column="holdout_fingerprint";value=body.fingerprint;}
    else {from=String(row.status);if(!["training","evaluating"].includes(from))throw new ApiError(409,"A completed or frozen attempt cannot be overwritten.");to=from==="training"?"training_failed":"holdout_failed";column="error";value=String(body.error||"Interrupted client computation").slice(0,1000);}
    if(column?.endsWith("fingerprint")&&!sha(value)) throw new ApiError(422,"A deterministic result fingerprint is required.");
    const update=await db.prepare(`UPDATE audit_experiments SET status = ?${column?", "+column+" = ?":""} WHERE id = ? AND owner = ? AND status = ?`).bind(to,...(column?[value]:[]),id,identity.owner,from).run();
    if(update.meta.changes!==1) throw new ApiError(409,"Invalid transition. Freeze once before holdout; changes require a new experiment. Repeated holdouts are not independent evidence.");
    await db.prepare("INSERT INTO audit_events (experiment_id,state,at) VALUES (?, ?, ?)").bind(id,to,retrieved()).run();
    row=(await db.prepare("SELECT * FROM audit_experiments WHERE id = ? AND owner = ?").bind(id,identity.owner).first())!;
  } else if(request.method!=="GET"||action) throw new ApiError(405,"Experiment snapshots have no edit operation.");
  const history=await db.prepare("SELECT state,at FROM audit_events WHERE experiment_id = ? ORDER BY id").bind(id).all();
  return response(view(row,history.results));
}

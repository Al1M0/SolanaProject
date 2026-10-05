import {get,set,values,update} from "idb-keyval";
import {browserMode,request,researchCompute,exportDataset} from "./api";
import {chainRequest} from "./chain";
import type {AuditResult} from "@/components/audit";
import type {Config,Metrics} from "./types";
export type Manifest={experiment_id:string;dataset_id:string;dataset_kind:"REAL"|"SYNTHETIC";dataset_content_hash:string;configuration:Config;token_universe:string[];wallet_universe:string[];created_at:string;source_revision:string;[key:string]:unknown};
export type Sensitivity={design:Record<string,string>;selection:string;rows:{row:string;changes:Record<string,number>;phase:string;end_ts:number;metrics:Metrics;fingerprint:string}[]};
export type Experiment={id:string;manifest_json?:string;manifest:Manifest;manifest_hash:string;frozen_hash:string|null;status:string;training?:AuditResult;sensitivity?:Sensitivity;holdout?:AuditResult;training_fingerprint?:string;holdout_fingerprint?:string;error:string|null;history:{state:string;at:string}[];created_at:string};
let offlineMode=false;
export function setOfflineAudit(value:boolean){offlineMode=value;}
async function offlineEndpoint<T>(path:string,body?:unknown):Promise<T>{
  if(path==="/api/experiments"&&body===undefined)return (await values<Experiment&{offline?:boolean}>()).filter(e=>e?.offline===true&&e.manifest).sort((a,b)=>b.created_at.localeCompare(a.created_at)) as T;
  if(path==="/api/experiments"){
    const b=body as {manifest_json:string;manifest_hash:string},manifest=JSON.parse(b.manifest_json) as Manifest;
    if(await get("experiment:"+manifest.experiment_id))throw new Error("Snapshot already exists.");
    const e={id:manifest.experiment_id,manifest,manifest_json:b.manifest_json,manifest_hash:b.manifest_hash,frozen_hash:null,status:"training",error:null,history:[{state:"training",at:new Date().toISOString()}],created_at:manifest.created_at,offline:true};await set("experiment:"+e.id,e);return e as T;
  }
  const match=path.match(/^\/api\/experiments\/(exp_[a-f0-9]{24})(?:\/(training|freeze|evaluate|holdout|fail))?$/);if(!match)throw new Error("Unknown local experiment operation.");
  const [,id,action]=match,key="experiment:"+id;if(!action){const e=await get<Experiment>(key);if(!e)throw new Error("Local attempt not found.");return e as T;}
  const transitions:Record<string,[string,string]>={training:["training","trained"],freeze:["trained","frozen"],evaluate:["frozen","evaluating"],holdout:["evaluating","evaluated"]};
  await update<Experiment>(key,e=>{if(!e)throw new Error("Local attempt not found.");const b=(body||{}) as Record<string,string>;if(action==="fail"){if(!["training","evaluating"].includes(e.status))throw new Error("Completed attempts cannot be overwritten.");return {...e,status:e.status==="training"?"training_failed":"holdout_failed",error:b.error||"Interrupted computation",history:[...e.history,{state:"failed",at:new Date().toISOString()}]};}const [from,to]=transitions[action];if(e.status!==from)throw new Error("Invalid transition: freeze once before holdout; changing parameters requires a new attempt.");return {...e,status:to,frozen_hash:action==="freeze"?e.manifest_hash:e.frozen_hash,history:[...e.history,{state:to,at:new Date().toISOString()}]};});return await get(key) as T;
}
const endpoint=<T>(path:string,body?:unknown)=>browserMode&&offlineMode?offlineEndpoint<T>(path,body):browserMode?chainRequest<T>(path,{body}):request<T>(path,body);
async function merge(remote:Experiment):Promise<Experiment>{if(!browserMode)return remote;const local=await get<Experiment>("experiment:"+remote.id);if(local?.manifest_hash===remote.manifest_hash){if(remote.training_fingerprint&&local.training&&remote.training_fingerprint!==local.training.fingerprint)throw new Error("Local training fingerprint differs from the persisted attempt.");if(remote.holdout_fingerprint&&local.holdout&&remote.holdout_fingerprint!==local.holdout.fingerprint)throw new Error("Local holdout fingerprint differs from the persisted attempt.");return {...local,...remote,training:remote.training||local.training,sensitivity:remote.sensitivity||local.sensitivity,holdout:remote.holdout||local.holdout};}return remote;}
async function saved(e:Experiment){if(browserMode)await set("experiment:"+e.id,e);return e;}
export async function listExperiments(){const remote=await endpoint<Experiment[]>("/api/experiments");return Promise.all(remote.map(merge));}
export async function getExperiment(id:string){return merge(await endpoint<Experiment>(`/api/experiments/${id}`));}
async function wait(id:string,progress:(n:number)=>void){for(;;){const e=await getExperiment(id);if(!["training","evaluating"].includes(e.status)){if(e.error)throw new Error(`${e.id}: ${e.error}`);return e;}progress(0);await new Promise(r=>setTimeout(r,600));}}
export async function startExperiment(datasetId:string,c:Config,tokens:string[],progress:(n:number)=>void):Promise<Experiment>{
  if(!browserMode){const e=await endpoint<Experiment>("/api/experiments",{dataset_id:datasetId,config:c,token_ids:tokens});return wait(e.id,progress);}
  if(!offlineMode)await endpoint<Experiment[]>("/api/experiments"); // Establish the workspace cookie before the first write.
  const dataset=await exportDataset(datasetId);
  const m=await researchCompute<{manifest:Manifest;manifest_json:string;manifest_hash:string}>("manifest",{dataset,config:c,tokens});
  const e=await endpoint<Experiment>("/api/experiments",{manifest_json:m.manifest_json,manifest_hash:m.manifest_hash});
  await saved(e);
  try {
    const trained=await researchCompute<{training:AuditResult;sensitivity:Sensitivity}>("train_experiment",{dataset,manifest:e.manifest,manifest_json:e.manifest_json},progress);
    const remote=await endpoint<Experiment>(`/api/experiments/${e.id}/training`,{fingerprint:trained.training.fingerprint});
    return saved({...remote,...trained});
  } catch(error){const message=error instanceof Error?error.message:String(error);await endpoint(`/api/experiments/${e.id}/fail`,{error:message}).catch(()=>undefined);throw error;}
}
export async function freezeExperiment(id:string){return saved(await merge(await endpoint<Experiment>(`/api/experiments/${id}/freeze`,{})));}
export async function evaluateExperiment(id:string,progress:(n:number)=>void):Promise<Experiment>{
  const remote=await endpoint<Experiment>(`/api/experiments/${id}/evaluate`,{});
  if(!browserMode)return wait(id,progress);
  const e=await merge(remote);await saved(e);
  try{
    const holdout=await researchCompute<AuditResult>("evaluate_experiment",{dataset:await exportDataset(e.manifest.dataset_id),manifest:e.manifest,manifest_json:e.manifest_json,frozen_hash:e.frozen_hash},progress);
    const done=await endpoint<Experiment>(`/api/experiments/${id}/holdout`,{fingerprint:holdout.fingerprint});return saved({...e,...done,holdout});
  }catch(error){const message=error instanceof Error?error.message:String(error);await endpoint(`/api/experiments/${id}/fail`,{error:message}).catch(()=>undefined);throw error;}
}
export async function exportExperiment(e:Experiment,progress?:(n:number)=>void){
  // Re-read the durable lifecycle lock, never trust only device-local status.
  const current=await getExperiment(e.id);
  if(!current.frozen_hash)throw new Error("Freeze this attempt before exporting the bundle.");
  let blob:Blob;
  if(browserMode){if(!current.training||!current.sensitivity)throw new Error("Detailed results remain on the original device. Rerun the immutable manifest with its authorized dataset using the offline CLI.");const data=await researchCompute<string>("bundle",{dataset:await exportDataset(current.manifest.dataset_id),manifest:current.manifest,manifest_json:current.manifest_json,trained:{training:current.training,sensitivity:current.sensitivity},holdout:current.holdout},progress);blob=new Blob([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],{type:"application/zip"});}
  else{const base=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";const r=await fetch(`${base}/api/experiments/${e.id}/bundle`,{credentials:"include"});if(!r.ok)throw new Error("Reproduction export failed. Verify frozen status and dataset access.");blob=await r.blob();}
  const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=e.id+"-reproduction.zip";document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
}

"use client";
import {useEffect,useRef} from "react";
import {Play,LockKeyhole,FileSearch,Download,LoaderCircle,Check,BookOpen} from "lucide-react";
import {auditGuide,type AuditAction,type GuideState} from "@/lib/audit-guide";

export default function AuditNextStep({state,busy,progress,operation,disabled,onAction,onEvidence,exportPrepared}:{state:GuideState;busy:boolean;progress:number;operation:AuditAction|null;disabled:boolean;onAction:(action:AuditAction)=>void;onEvidence:(phase:"training"|"holdout")=>void;exportPrepared:boolean}) {
  const guide=auditGuide(state),heading=useRef<HTMLHeadingElement>(null),previous=useRef(state.status);
  useEffect(()=>{if(busy)return;if(previous.current!==state.status)heading.current?.focus({preventScroll:true});previous.current=state.status;},[state.status,busy]);
  const Icon=guide.action==="freeze"?LockKeyhole:guide.action==="holdout"?FileSearch:guide.action==="export"?Download:Play;
  const working=operation==="training"?"Checking the earlier period…":operation==="holdout"?"Checking the later period…":operation==="freeze"?"Saving the locked snapshot…":"Verifying the saved results for export…";
  return <section className={`audit-next-step ${busy?"is-working":""}`} aria-label="Your next audit step" aria-busy={busy}>
    <div className="next-step-mark" aria-hidden="true">{busy?<LoaderCircle className="spin" size={27}/>:<Icon size={27}/>}</div>
    <div className="next-step-copy"><div className="eyebrow">{busy?"WORK IN PROGRESS":"YOUR NEXT STEP"}</div><h2 ref={heading} tabIndex={-1} key={busy?working:guide.title}>{busy?working:guide.title}</h2><p>{busy?"The result appears when the actual engine or storage operation finishes. Its attempt record stays visible if interrupted.":guide.description}</p>
      {guide.evidence&&<button type="button" className="text-link evidence-jump" disabled={busy} onClick={()=>onEvidence(guide.evidence!)}><BookOpen size={15}/>Read {guide.evidence==="training"?"training results":"the final result"}</button>}
      {exportPrepared&&<p className="export-confirmation" role="status"><Check size={16}/>Bundle prepared. Your browser handles saving the ZIP.</p>}
    </div>
    <div className="next-step-action">{guide.action?<button type="button" className="button primary next-action" disabled={busy||disabled} onClick={()=>onAction(guide.action!)}>{busy?<LoaderCircle size={18} className="spin"/>:<Icon size={18}/>}<span>{busy?working:guide.label}</span></button>:<a className="button" href="#audit-attempt-log">Inspect attempt history</a>}
      {busy&&<div className="audit-operation" role="status"><progress aria-label={working} max={100} value={progress>0?Math.min(100,progress):undefined}/><small>{progress>0?`Engine progress ${progress}%${progress>=100?" · preparing the result":""}`:"Waiting for the engine or storage response"}</small></div>}
      {!busy&&<small>Every attempt stays in the log.</small>}
    </div>
  </section>;
}

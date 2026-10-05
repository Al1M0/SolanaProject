"use client";
import {createContext,useCallback,useContext,useEffect,useState,ReactNode} from "react";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {LayoutDashboard,FlaskConical,ChartNoAxesCombined,FileText,Database,ChevronRight,LoaderCircle,TriangleAlert,PanelLeftClose,PanelLeftOpen,Wallet,Radio,Search} from "lucide-react";
import {WalletButton,useWallet} from "./wallet-provider";
import * as api from "@/lib/api";
import type {Dataset,Strategy,Run} from "@/lib/types";
type Workspace={datasets:Dataset[];strategies:Strategy[];runs:Run[];loading:boolean;error:string;refresh:()=>Promise<void>;busy:boolean;progress:number;execute:(strategy:Strategy)=>Promise<Run>};
const Context=createContext<Workspace|null>(null);
export const useWorkspace=()=>{const c=useContext(Context);if(!c)throw new Error("Workspace unavailable");return c;};
export function Badge({kind}:{kind:string}){return <span className={`badge ${kind==="REAL"?"real":"synthetic"}`}>{kind}</span>;}
export function Notice({children,error=false}:{children:ReactNode;error?:boolean}){return <div className={`notice ${error?"error":""}`} role={error?"alert":undefined}><TriangleAlert size={17}/><div>{children}</div></div>;}
export function Empty({title,children}:{title:string;children:ReactNode}){return <div className="empty"><FlaskConical size={30}/><h3>{title}</h3><p>{children}</p></div>;}
export function WorkspaceProvider({children}:{children:ReactNode}){
  const [datasets,setDatasets]=useState<Dataset[]>([]),[strategies,setStrategies]=useState<Strategy[]>([]),[runs,setRuns]=useState<Run[]>([]);
  const [loading,setLoading]=useState(true),[error,setError]=useState(""),[busy,setBusy]=useState(false),[progress,setProgress]=useState(0),[collapsed,setCollapsed]=useState(false);
  const path=usePathname();
  const wallet=useWallet();
  const chainPage=["/wallet","/markets","/live","/research"].some(p=>path===p||path===p+"/");
  const refresh=useCallback(async()=>{try{const [d,s,r]=await Promise.all([api.listDatasets(),api.listStrategies(),api.listRuns()]);setDatasets(d);setStrategies(s);setRuns(r);setError("");}catch(e){setError(e instanceof Error?e.message:String(e));}finally{setLoading(false);}},[]);
  useEffect(()=>{void refresh();},[refresh]);
  const execute=async(strategy:Strategy)=>{if(busy)throw new Error("An experiment is already running");setBusy(true);setProgress(0);try{const r=await api.runStrategy(strategy,setProgress);await refresh();return r;}finally{setBusy(false);}};
  const researchNav=[{href:"/",name:"Research desk",icon:LayoutDashboard},{href:"/audit/",name:"Audit hypothesis",icon:FlaskConical},{href:"/lab/",name:"Strategy lab",icon:FlaskConical},{href:"/results/",name:"Backtests",icon:ChartNoAxesCombined},{href:"/report/",name:"Research report",icon:FileText},{href:"/datasets/",name:"Datasets",icon:Database}];
  const chainNav=[{href:"/wallet/",name:"Wallet",icon:Wallet},{href:"/research/",name:"Wallet research",icon:Search},{href:"/markets/",name:"Markets",icon:ChartNoAxesCombined},{href:"/live/",name:"Live signals",icon:Radio}];
  const nav=[...researchNav,...chainNav];
  const isActive=(href:string)=>path===href||path===href.slice(0,-1);
  return <Context.Provider value={{datasets,strategies,runs,loading,error,refresh,busy,progress,execute}}><div className={`app-shell ${collapsed?"collapsed":""}`}>
    <a href="#main-content" className="skip-link">Skip to research</a>
    <aside className="sidebar"><Link href="/" className="brand" aria-label="Solana Quant Research Lab home"><div className="brand-symbol brand-mark" aria-hidden="true"><i/><i/><i/></div><div><strong>SOLANA QUANT</strong><span>Research Lab</span></div></Link><button className="collapse-control" onClick={()=>setCollapsed(!collapsed)} aria-label={collapsed?"Expand navigation":"Collapse navigation"} aria-expanded={!collapsed}>{collapsed?<PanelLeftOpen size={18}/>:<PanelLeftClose size={18}/>}</button>
      <div className="navigation-groups">{[{label:"Research",items:researchNav},{label:"On-chain tools",items:chainNav}].map(group=><div className="nav-group" key={group.label}><div className="nav-label">{group.label}</div><nav aria-label={group.label}>{group.items.map(({href,name,icon:Icon})=><Link key={href} href={href} title={name} aria-current={isActive(href)?"page":undefined} className={`${isActive(href)?"active":""} ${href==="/audit/"?"audit-nav":""}`}><Icon size={18}/><span>{name}</span></Link>)}</nav></div>)}</div>
      <div className="sidebar-bottom"><div className="desk-note"><FlaskConical size={18}/><b>Evidence over instinct.</b></div><p>{api.browserMode?"Research details stay on this device. Your audit shows the selected storage mode.":"Research and wallet observations saved to your database."}</p><div className="version">ENGINE 1.2.0 <span>USD · UTC</span></div></div>
    </aside>
    <div className="app-main"><header className="topbar"><div className="breadcrumb">Research <ChevronRight size={14}/><span>{nav.find(n=>isActive(n.href))?.name||"Research desk"}</span></div><div className="topbar-right"><span className="chain-label">SOLANA MAINNET-BETA</span><WalletButton/></div></header>
      <main id="main-content" tabIndex={-1}>{busy&&<div className="job-banner" role="status"><LoaderCircle className="spin" size={18}/><span>Processing historical events</span><progress aria-label="Historical processing progress" max={100} value={progress}/><b>{progress}%</b><span className="subtle">Keep this workspace open</span></div>}
        {wallet.error&&<Notice error>{wallet.error} {wallet.error.includes("not installed")&&<a href="https://phantom.com/download" target="_blank" rel="noopener noreferrer">Install Phantom</a>}</Notice>}
        {chainPage?children:loading?<div className="loading" role="status"><LoaderCircle className="spin" size={28}/><h2>Opening your research workspace</h2><p>{api.browserMode?"Loading the Python engine and deterministic dataset…":"Connecting to the research API…"}</p></div>:error?<><Notice error>{error}</Notice><button className="button" onClick={()=>{setLoading(true);void refresh();}}>Retry connection</button></>:children}
      </main><footer>Reproducible research. Measurable assumptions.<span>No live trading · No execution keys</span></footer>
    </div></div></Context.Provider>;
}

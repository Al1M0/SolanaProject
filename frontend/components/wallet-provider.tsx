"use client";
import {createContext,useCallback,useContext,useEffect,useRef,useState,ReactNode} from "react";
import {Wallet,LoaderCircle,LogOut,ShieldCheck} from "lucide-react";
import {chainRequest,Session,shortAddress,WalletSnapshot} from "@/lib/chain";
import {phantomProvider,phantomError,signatureBase64,PublicKey,PhantomProvider} from "@/lib/phantom";
type WalletContext={address:string|null;connecting:boolean;signing:boolean;session:Session|null;snapshot:WalletSnapshot|null;loading:boolean;error:string;connect:()=>Promise<void>;disconnect:()=>Promise<void>;login:()=>Promise<void>;refresh:()=>Promise<void>};
const Context=createContext<WalletContext|null>(null);
export function useWallet(){const value=useContext(Context);if(!value)throw new Error("Wallet provider is unavailable");return value;}
export function WalletProvider({children}:{children:ReactNode}){
  const [address,setAddress]=useState<string|null>(null),[session,setSession]=useState<Session|null>(null),[snapshot,setSnapshot]=useState<WalletSnapshot|null>(null),[loading,setLoading]=useState(false),[error,setError]=useState(""),[connecting,setConnecting]=useState(false),[signing,setSigning]=useState(false);
  const addressRef=useRef<string|null>(null),generation=useRef(0);
  const [provider,setProvider]=useState<PhantomProvider|null>(null);
  const change=useCallback((wallet:string|null)=>{generation.current++;addressRef.current=wallet;setAddress(wallet);setSnapshot(null);setSession(null);setError("");setLoading(false);},[]);
  const refresh=useCallback(async()=>{const wallet=addressRef.current;if(!wallet)return;const version=generation.current;setLoading(true);try{const data=await chainRequest<WalletSnapshot>(`/api/wallets/${wallet}`);if(generation.current===version){setSnapshot(data);setError("");}}catch(e){if(generation.current===version)setError(e instanceof Error?e.message:String(e));}finally{if(generation.current===version)setLoading(false);}},[]);
  useEffect(()=>{
    if(!provider){const detected=phantomProvider();if(detected)setProvider(detected);return;}
    const connected=(key?:PublicKey|null)=>{const next=key?.toString()||provider.publicKey?.toString()||null;if(next!==addressRef.current)change(next);};
    const changed=(key?:PublicKey|null)=>{change(key?.toString()||null);void chainRequest("/api/auth/logout",{body:{}}).catch(()=>{});};
    const disconnected=()=>{change(null);void chainRequest("/api/auth/logout",{body:{}}).catch(()=>{});};
    provider.on("connect",connected);provider.on("accountChanged",changed);provider.on("disconnect",disconnected);
    if(provider.isConnected&&provider.publicKey)connected(provider.publicKey);
    return()=>{provider.removeListener("connect",connected);provider.removeListener("accountChanged",changed);provider.removeListener("disconnect",disconnected);};
  },[change,provider]);
  useEffect(()=>{if(!session)return;const timer=setTimeout(()=>setSession(null),Math.max(0,session.expires_at*1000-Date.now()));return()=>clearTimeout(timer);},[session]);
  useEffect(()=>{if(!address)return;void refresh();const version=generation.current;void chainRequest<{session:Session|null}>("/api/auth/session").then(r=>{if(version===generation.current&&r.session?.wallet===address)setSession(r.session);}).catch(()=>{});const timer=setInterval(()=>{if(document.visibilityState==="visible")void refresh();},60000);return()=>clearInterval(timer);},[address,refresh]);
  async function connect(){setError("");const p=phantomProvider();if(!p){setError("Phantom is not installed or is unavailable here. Install the extension, or open this site in Phantom's mobile browser.");return;}setProvider(p);setConnecting(true);try{const result=await p.connect();const wallet=result.publicKey.toString();if(wallet!==addressRef.current)change(wallet);}catch(e){setError(phantomError(e));}finally{setConnecting(false);}}
  async function disconnect(){let failure="";try{await chainRequest("/api/auth/logout",{body:{}});}catch(e){failure=e instanceof Error?e.message:String(e);}try{await phantomProvider()?.disconnect();}catch(e){failure=phantomError(e);}finally{change(null);if(failure)setError(failure);}}
  async function login(){const p=phantomProvider(),wallet=addressRef.current;if(!p||!wallet)return;const version=generation.current;setSigning(true);setError("");try{
    const nonce=await chainRequest<{id:string;wallet:string;message:string}>("/api/auth/nonce",{body:{wallet}});
    if(generation.current!==version||p.publicKey?.toString()!==wallet)throw new Error("Wallet changed. Connect the intended account and try again.");
    const signed=await p.signMessage(new TextEncoder().encode(nonce.message),"utf8");
    if(generation.current!==version||signed.publicKey.toString()!==wallet||p.publicKey?.toString()!==wallet)throw new Error("Wallet changed during login. Request a new message.");
    const authenticated=await chainRequest<Session>("/api/auth/verify",{body:{id:nonce.id,wallet,signature:signatureBase64(signed.signature)}});
    if(generation.current!==version){await chainRequest("/api/auth/logout",{body:{}});return;}setSession(authenticated);
  }catch(e){if(generation.current===version)setError(phantomError(e));}finally{setSigning(false);}}
  return <Context.Provider value={{address,connecting,signing,session,snapshot,loading,error,connect,disconnect,login,refresh}}>{children}</Context.Provider>;
}
export function WalletButton(){const w=useWallet();return <div className="wallet-menu"><button className={`button small ${w.address?"":"primary"}`} disabled={w.connecting} onClick={()=>void (w.address?w.disconnect():w.connect())}>{w.connecting?<LoaderCircle size={16} className="spin"/>:w.address?<LogOut size={16}/>:<Wallet size={16}/>}<span>{w.address?shortAddress(w.address):w.connecting?"Connecting…":"Connect Wallet"}</span></button>{w.address&&<span className="wallet-session" title={w.session?"Message signature verified":"Connected, not signed in"}>{w.session&&<ShieldCheck size={15}/>}</span>}</div>;}

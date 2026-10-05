// Translate managed preview's Vite-shaped arguments while keeping the requested Next.js stack.
import {spawn} from "node:child_process";
import {existsSync} from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
let api;
// The supervisor clears inherited environment; its forwarded flags identify preview mode.
// Run the same hosted Worker behind Next's proxy, within the canonical project checkout.
if(process.argv.includes("--strictPort")&&existsSync(path.join(root,"scripts/preview-edge.mjs"))){
  const env={...process.env,CORS_ORIGINS:"http://terminal.local:4173",APP_ORIGIN:"http://terminal.local:4173"};
  api=spawn(process.execPath,[path.join(root,"scripts/preview-edge.mjs")],{cwd:root,env,stdio:"inherit"});
  process.env.NEXT_DEV_CHAIN_PROXY="http://127.0.0.1:7778";
}
const input=process.argv.slice(2),args=[];
for(let i=0;i<input.length;i++){
  if(input[i]==="--strictPort")continue;
  args.push(input[i]==="--host"?"--hostname":input[i]);
}
if(!args.includes("--hostname"))args.push("--hostname","0.0.0.0");
if(!args.includes("--port"))args.push("--port","3000");
const child=spawn(process.execPath,["node_modules/next/dist/bin/next","dev",...args],{stdio:"inherit",env:process.env});
for(const signal of ["SIGINT","SIGTERM"])process.on(signal,()=>{child.kill(signal);api?.kill(signal);});
child.on("exit",code=>{api?.kill();process.exit(code||0);});

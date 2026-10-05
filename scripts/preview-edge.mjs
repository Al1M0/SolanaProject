// Development-only Node adapter for the deployed Worker. Never included in its bundle.
import {createServer} from "node:http";
import {DatabaseSync} from "node:sqlite";
import {readFileSync,mkdirSync,readdirSync} from "node:fs";
import {build} from "esbuild";
import path from "node:path";
import {pathToFileURL} from "node:url";
mkdirSync(".sites-runtime",{recursive:true});
await build({entryPoints:["edge/index.ts"],bundle:true,format:"esm",platform:"node",target:"es2022",outfile:".sites-runtime/preview-worker.mjs"});
const {default:worker}=await import(pathToFileURL(path.resolve(".sites-runtime/preview-worker.mjs")));
const sqlite=new DatabaseSync(".sites-runtime/preview.db");
sqlite.exec("CREATE TABLE IF NOT EXISTS preview_migrations (name TEXT PRIMARY KEY)");
for(const name of readdirSync("drizzle").filter(n=>n.endsWith(".sql")).sort()){
  if(sqlite.prepare("SELECT name FROM preview_migrations WHERE name=?").get(name))continue;
  sqlite.exec("BEGIN");
  try{sqlite.exec(readFileSync(path.join("drizzle",name),"utf8"));sqlite.prepare("INSERT INTO preview_migrations VALUES (?)").run(name);sqlite.exec("COMMIT");}catch(e){sqlite.exec("ROLLBACK");throw e;}
}
class Statement{
  constructor(sql,values=[]){this.sql=sql;this.values=values;}
  bind(...values){return new Statement(this.sql,values);}
  async first(){return sqlite.prepare(this.sql).get(...this.values)||null;}
  async all(){return {results:sqlite.prepare(this.sql).all(...this.values)};}
  async run(){return {meta:{changes:Number(sqlite.prepare(this.sql).run(...this.values).changes)}};}
}
const DB={prepare:sql=>new Statement(sql),async batch(statements){sqlite.exec("BEGIN");try{const out=statements.map(s=>({meta:{changes:Number(sqlite.prepare(s.sql).run(...s.values).changes)}}));sqlite.exec("COMMIT");return out;}catch(e){sqlite.exec("ROLLBACK");throw e;}}};
const env={DB,APP_ORIGIN:process.env.APP_ORIGIN||"http://terminal.local:4173",...Object.fromEntries(["HELIUS_API_KEY","BIRDEYE_API_KEY","COINGECKO_DEMO_API_KEY","SOLANA_RPC_URL"].filter(k=>process.env[k]).map(k=>[k,process.env[k]]))};
const server=createServer(async(req,res)=>{
  try{
    const buffers=[];let size=0;for await(const chunk of req){size+=chunk.length;if(size>65536){res.writeHead(413,{"content-type":"application/json"});res.end(JSON.stringify({detail:"Request too large."}));return;}buffers.push(chunk);}
    const request=new Request(env.APP_ORIGIN+req.url,{method:req.method,headers:req.headers,...(["GET","HEAD"].includes(req.method)?{}:{body:Buffer.concat(buffers)})});
    const response=await worker.fetch(request,env);res.writeHead(response.status,Object.fromEntries(response.headers));res.end(Buffer.from(await response.arrayBuffer()));
  }catch{res.writeHead(503,{"content-type":"application/json"});res.end(JSON.stringify({detail:"Preview API unavailable."}));}
});
server.listen(7778,"127.0.0.1",()=>console.log("Read-only mainnet Worker API ready."));
for(const signal of ["SIGTERM","SIGINT"])process.on(signal,()=>server.close(()=>{sqlite.close();process.exit(0);}));

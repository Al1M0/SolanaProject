import {execFileSync} from "node:child_process";
import {cpSync,rmSync} from "node:fs";
import {build} from "esbuild";
const options={stdio:"inherit",env:{...process.env,NEXT_PUBLIC_EXECUTION_MODE:"browser",NEXT_PUBLIC_CHAIN_API_URL:"",NEXT_PUBLIC_API_URL:"",STATIC_EXPORT:"1",NEXT_TELEMETRY_DISABLED:"1"}};
execFileSync("npm",["--prefix","frontend","run","prepare:browser"],options);
execFileSync("npm",["--prefix","frontend","run","build"],options);
rmSync("dist",{recursive:true,force:true});
cpSync("frontend/out","dist/client",{recursive:true});
await build({entryPoints:["edge/index.ts"],bundle:true,format:"esm",target:"es2022",platform:"browser",outfile:"dist/server/index.js",minify:true});

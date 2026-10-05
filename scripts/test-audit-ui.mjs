import {build} from "esbuild";
import {execFileSync} from "node:child_process";
import {mkdtempSync,rmSync} from "node:fs";
import {tmpdir} from "node:os";
import path from "node:path";
const temporary=mkdtempSync(path.join(tmpdir(),"quant-audit-view-test-"));
try{
  const outfile=path.join(temporary,"audit-tests.cjs");
  await build({entryPoints:["tests/audit-view.tsx"],bundle:true,platform:"node",format:"cjs",jsx:"automatic",external:["react","react/jsx-runtime","react-dom/server","recharts","lucide-react"],nodePaths:[path.resolve("frontend/node_modules")],tsconfig:"frontend/tsconfig.json",outfile});
  execFileSync(process.execPath,["--test",outfile],{stdio:"inherit",timeout:30000,env:{...process.env,NODE_PATH:path.resolve("frontend/node_modules")}});
}finally{rmSync(temporary,{recursive:true,force:true});}

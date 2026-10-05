import {build} from "esbuild";
import {execFileSync} from "node:child_process";
import {mkdtempSync,rmSync} from "node:fs";
import {tmpdir} from "node:os";
import path from "node:path";
const temporary=mkdtempSync(path.join(tmpdir(),"quant-wallet-test-"));
try{
  const outfile=path.join(temporary,"wallet-tests.cjs");
  // Keep React's native module.require available to act(); bundling it retains MessagePorts.
  await build({entryPoints:["tests/wallet-flow.tsx"],bundle:true,platform:"node",format:"cjs",jsx:"automatic",external:["react","react/jsx-runtime","react-test-renderer","lucide-react"],nodePaths:[path.resolve("frontend/node_modules")],tsconfig:"frontend/tsconfig.json",outfile});
  execFileSync(process.execPath,["--test",outfile],{stdio:"inherit",timeout:30000,env:{...process.env,NODE_PATH:path.resolve("frontend/node_modules")}});
}finally{rmSync(temporary,{recursive:true,force:true});}

// Run the local REA source service in a fresh Vite process; no dist rebuild.
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [image,output,rawOutput]=process.argv.slice(2);if(!image||!output||!rawOutput)throw new Error('expected image, redacted and private paths');
const req=createRequire(`${process.cwd()}/package.json`),vite=await import(pathToFileURL(req.resolve('vite')).href);
const server=await vite.createServer({configFile:false,server:{middlewareMode:true},appType:'custom'});
try{
 const {MalbolgeService}=await server.ssrLoadModule('/src/application/malbolge/MalbolgeService.ts');
 const result=await new MalbolgeService().trace({path:image,max_steps:5000,event_start_step:2600,event_capture_limit:512,eof_mode:'olmstead_1998'});
 if(!result.ok)throw new Error(String(result.error));const raw=JSON.stringify(result.value,null,2)+'\n';
 await writeFile(rawOutput,raw,{flag:'wx',mode:0o600});await writeFile(output,raw.split(image).join('<image>'),{flag:'wx'});
 const n=result.value.normalized_result,visits=n.events.filter(e=>e.position===58470).map(e=>({step:e.step,opcode:e.opcode,a:e.a,d:e.d}));
 console.log(JSON.stringify({evidence_id:result.value.evidence_id,raw_sha256:createHash('sha256').update(raw).digest('hex'),status:n.run.status,steps:n.run.steps,first_event:n.events[0]?.step,events_truncated:n.run.events_truncated,output_bytes:n.output_bytes,visits}));
 if(n.run.status!=='HALTED')throw new Error('not halted');
}finally{await server.close()}

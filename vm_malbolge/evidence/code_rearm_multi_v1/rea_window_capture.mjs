// Run REA source service from its checkout. Arguments: image, redacted output, private raw output.
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const [image,output,rawOutput]=process.argv.slice(2);
if(!image||!output||!rawOutput)throw new Error('image, redacted path and private raw path required');
const req=createRequire(`${process.cwd()}/package.json`),vite=await import(pathToFileURL(req.resolve('vite')).href);
const server=await vite.createServer({configFile:false,server:{middlewareMode:true},appType:'custom'});
try {
 const {MalbolgeService}=await server.ssrLoadModule('/src/application/malbolge/MalbolgeService.ts');
 const result=await new MalbolgeService().trace({path:image,max_steps:8000,event_start_step:5250,event_capture_limit:512,eof_mode:'olmstead_1998'});
 if(!result.ok)throw new Error(String(result.error));
 const raw=JSON.stringify(result.value,null,2)+'\n';await writeFile(rawOutput,raw,{flag:'wx',mode:0o600});
 await writeFile(output,raw.split(image).join('<image>'),{flag:'wx'});
 const n=result.value.normalized_result,visits=n.events.filter(e=>e.position===58550||e.position===58573).map(e=>({step:e.step,pc:e.position,opcode:e.opcode}));
 console.log(JSON.stringify({evidence_id:result.value.evidence_id,raw_sha256:createHash('sha256').update(raw).digest('hex'),status:n.run.status,steps:n.run.steps,events_truncated:n.run.events_truncated,first_event:n.events[0]?.step,visits}));
 if(n.run.status!=='HALTED')throw new Error('not halted');
} finally {await server.close()}

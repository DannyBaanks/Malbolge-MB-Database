import {readFileSync,writeFileSync} from 'node:fs';import {pathToFileURL} from 'node:url';import assert from 'node:assert/strict';
const [dist,folder]=process.argv.slice(2);const {runMalbolge}=await import(pathToFileURL(`${dist}/domain/malbolge/malbolgeClassic.js`));
const local=JSON.parse(readFileSync(`${folder}/results.json`)),reports={};
for(const label of Object.keys(local)){
 const plan=JSON.parse(readFileSync(`${folder}/${label}.plan.json`));const source=readFileSync(`${folder}/${label}.mb`);
 const options={maxSteps:100000,eventCaptureLimit:4096};const baseline=runMalbolge(source.toString('latin1'),options);
 assert.equal(baseline.status,'HALTED');assert.equal(baseline.steps,local[label].steps);assert.equal(Buffer.from(baseline.output_bytes).toString('hex'),local[label].output_hex);
 const merged=new Map(baseline.events.map(e=>[e.step,e]));const windows=[{start:1,end:baseline.events.at(-1).step}];let overlaps=0;
 for(let start=4096;start<=baseline.steps;start+=4095){
  const run=runMalbolge(source.toString('latin1'),{...options,eventStartStep:start});
  for(const key of ['status','steps','output_bytes','state_digest_before','state_digest_after'])assert.deepEqual(run[key],baseline[key]);
  windows.push({start,end:run.events.at(-1).step});
  for(const e of run.events){if(merged.has(e.step)){assert.deepEqual(e,merged.get(e.step));overlaps++;}merged.set(e.step,e);}
 }
 const all=[...merged.values()].sort((a,b)=>a.step-b.step);assert.equal(all.length,baseline.steps);all.forEach((e,i)=>assert.equal(e.step,i+1));
 const mem=new Map([...source].map((v,i)=>[i,v]));let active=false;const operations=[],emissions=[],changes=[],flag_reads=[];
 const flagAddrs=[plan.d0,plan.d1,plan.s0,plan.s1];
 function snapshot(){const flags=flagAddrs.map(x=>mem.get(x));const depth=({'74,74':0,'70,74':1,'70,70':2})[flags.slice(0,2).join(',')]??-1;return {flags,depth,slots:flags.slice(2).map(x=>x===74?'A':x===70?'B':'?')};}
 for(const e of all){
  if(e.position===plan.entry && Object.hasOwn(plan.starts,mem.get(e.d)+2)){active=true;operations.push({step:e.step,...plan.starts[mem.get(e.d)+2],...snapshot()});}
  if(e.position===plan.rot && Object.hasOwn(plan.emissions,e.d))emissions.push({step:e.step,...plan.emissions[e.d],...snapshot()});
  if(active && flagAddrs.includes(e.position))flag_reads.push({step:e.step,pc:e.position,opcode:e.opcode_name,...snapshot()});
  const before=snapshot().flags;for(const w of e.writes)mem.set(w.position,w.value_after);const after=snapshot().flags;
  if(active && JSON.stringify(before)!==JSON.stringify(after))changes.push({step:e.step,pc:e.position,before,after});
 }
 const final=snapshot();for(const [key,value] of Object.entries({operations,emissions,changes,final}))assert.deepEqual(value,local[label][key]);
 assert.equal(emissions.map(e=>e.char).join(''),Buffer.from(baseline.output_bytes).toString('ascii'));
 reports[label]={status:baseline.status,steps:baseline.steps,output_hex:local[label].output_hex,operations,emissions,changes,final,flag_reads,capture:{windows,overlaps,contiguous_steps:all.length,equivalent_runs:true},digest:baseline.state_digest_after};
}
writeFileSync(`${folder}/rea.json`,JSON.stringify(reports,null,2)+'\n');console.log(`PASS: REA confirms runtime stack states, flags, returned tokens and guards in ${Object.keys(reports).length} programs`);

import {readFileSync,writeFileSync} from 'node:fs';import {pathToFileURL} from 'node:url';import assert from 'node:assert/strict';
const [dist,folder]=process.argv.slice(2);const {runMalbolge}=await import(pathToFileURL(`${dist}/domain/malbolge/malbolgeClassic.js`));
const local=JSON.parse(readFileSync(`${folder}/results.json`)),reports={};
for(const mode of Object.keys(local)){
 const plan=JSON.parse(readFileSync(`${folder}/${mode}.plan.json`));const source=readFileSync(`${folder}/${mode}.mb`);
 const options={maxSteps:100000,eventCaptureLimit:4096},baseline=runMalbolge(source.toString('latin1'),options);
 assert.equal(baseline.status,'HALTED');assert.equal(baseline.steps,local[mode].steps);assert.equal(Buffer.from(baseline.output_bytes).toString('hex'),local[mode].output_hex);
 const merged=new Map(baseline.events.map(e=>[e.step,e]));const windows=[{start:1,end:baseline.events.at(-1).step}];let overlaps=0;
 for(let start=4096;start<=baseline.steps;start+=4095){
  const run=runMalbolge(source.toString('latin1'),{...options,eventStartStep:start});
  for(const key of ['status','steps','output_bytes','state_digest_before','state_digest_after'])assert.deepEqual(run[key],baseline[key]);
  windows.push({start,end:run.events.at(-1).step});
  for(const e of run.events){if(merged.has(e.step)){assert.deepEqual(e,merged.get(e.step));overlaps++;}merged.set(e.step,e);}
 }
 const all=[...merged.values()].sort((a,b)=>a.step-b.step);assert.equal(all.length,baseline.steps);all.forEach((e,i)=>assert.equal(e.step,i+1));
 const mem=new Map([...source].map((v,i)=>[i,v]));let active=false;const events=[],jumps=[],writes=[],slot_events=[];
 for(const e of all){
  if(Object.hasOwn(plan.markers,e.position)){
   active=true;for(const mark of plan.markers[e.position])events.push({...mark,step:e.step,pc:e.position,d:e.d,a:e.a,slot:mem.get(plan.slot),journal:mem.get(plan.journal),mask:mem.get(plan.mask),sources:plan.sources.map(x=>mem.get(x))});
  }
  if(active && e.opcode_name==='jmp'){
   const j={step:e.step,pc:e.position,d:e.d,stored:mem.get(e.d),next_pc:(mem.get(e.d)+1)%59049};jumps.push(j);
   assert.equal(all[e.step].position,j.next_pc);
  }
  const before=[mem.get(plan.slot),mem.get(plan.journal)];
  if(active && [plan.slot,plan.journal].includes(e.d) && ['crazy','rot'].includes(e.opcode_name))slot_events.push(e);
  for(const w of e.writes)mem.set(w.position,w.value_after);
  const after=[mem.get(plan.slot),mem.get(plan.journal)];if(active && JSON.stringify(before)!==JSON.stringify(after))writes.push({step:e.step,pc:e.position,before,after});
 }
 const final_slot=mem.get(plan.slot),final_journal=mem.get(plan.journal);
 for(const [key,value] of Object.entries({events,jumps,writes,final_slot,final_journal}))assert.deepEqual(value,local[mode][key]);
 reports[mode]={status:baseline.status,steps:baseline.steps,output_hex:local[mode].output_hex,events,jumps,writes,slot_events,final_slot,final_journal,capture:{windows,overlaps,contiguous_steps:all.length,equivalent_runs:true},digest:baseline.state_digest_after};
}
writeFileSync(`${folder}/rea.json`,JSON.stringify(reports,null,2)+'\n');
console.log('PASS: saludar CALL/body/RET, exact Hola LF, physical caller continuation and controls');

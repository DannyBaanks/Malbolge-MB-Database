import {readFileSync,writeFileSync,readdirSync} from 'node:fs';import {pathToFileURL} from 'node:url';import assert from 'node:assert/strict';
const [dist,root]=process.argv.slice(2);const {runMalbolge}=await import(pathToFileURL(`${dist}/domain/malbolge/malbolgeClassic.js`));
const results=JSON.parse(readFileSync(`${root}/results.json`)),reports={};
for(const name of Object.keys(results)){
 const folder=`${root}/${name}`,source=readFileSync(`${folder}/program.mb`),map=JSON.parse(readFileSync(`${folder}/map.json`)),local=JSON.parse(readFileSync(`${folder}/trace.json`));
 const options={maxSteps:200000,eventCaptureLimit:4096},baseline=runMalbolge(source.toString('latin1'),options);
 assert.equal(baseline.status,'HALTED');assert.equal(baseline.steps,local.steps);assert.equal(Buffer.from(baseline.output_bytes).toString('hex'),results[name].output_hex);
 const merged=new Map(baseline.events.map(e=>[e.step,e]));const windows=[{start:1,end:baseline.events.at(-1).step}];let overlaps=0;
 for(let start=4096;start<=baseline.steps;start+=4095){
  const run=runMalbolge(source.toString('latin1'),{...options,eventStartStep:start});
  for(const key of ['status','steps','output_bytes','state_digest_before','state_digest_after'])assert.deepEqual(run[key],baseline[key]);
  windows.push({start,end:run.events.at(-1).step});
  for(const e of run.events){if(merged.has(e.step)){assert.deepEqual(e,merged.get(e.step));overlaps++;}merged.set(e.step,e);}
 }
 const all=[...merged.values()].sort((a,b)=>a.step-b.step);assert.equal(all.length,baseline.steps);all.forEach((e,i)=>assert.equal(e.step,i+1));
 const mem=new Map([...source].map((v,i)=>[i,v]));let active=false;const events=[],jumps=[],stack=[],visits=new Map(),instances=new Map(map.instances.map(i=>[i.id,i]));
 const slots=()=>Object.fromEntries(Object.entries(map.slots).map(([d,s])=>[d,{value:mem.get(s.slot),journal:mem.get(s.journal)}]));
 for(const e of all){
  if(e.position===map.main_entry)active=true;
  if(active){
   visits.set(e.position,(visits.get(e.position)||0)+1);
   for(const mark of map.markers[e.position]||[]){
    events.push({...mark,step:e.step,pc:e.position,d:e.d,a:e.a,slots:slots()});
    if(mark.kind==='call'){
     const i=instances.get(mark.instance);assert.equal(mem.get(e.d),i.entry-1);assert.equal(mem.get(i.slot),i.continuation-1);assert.equal(i.depth,stack.length+1);stack.push(i.id);
    } else if(mark.kind==='function_entry')assert.equal(stack.at(-1),mark.instance);
    else if(mark.kind==='return'){assert.equal(stack.pop(),mark.instance);assert.equal(mem.get(e.d),instances.get(mark.instance).continuation-1);}
    else if(mark.kind==='main_halt')assert.equal(stack.length,0);
   }
   for(const id of stack.slice(0,-1)){const i=instances.get(id);assert.equal(mem.get(i.slot),i.continuation-1);}
   if(e.opcode_name==='jmp'){
    const j={step:e.step,pc:e.position,d:e.d,stored:mem.get(e.d),next_pc:(mem.get(e.d)+1)%59049};jumps.push(j);assert.equal(all[e.step].position,j.next_pc);
   }
  }
  for(const w of e.writes)mem.set(w.position,w.value_after);
 }
 assert.equal(stack.length,0);assert.ok([...visits.values()].every(n=>n===1));assert.equal(jumps.length,map.instances.length*2);
 assert.deepEqual(events,local.events);assert.deepEqual(jumps,local.jumps);assert.deepEqual(slots(),local.final_slots);
 reports[name]={status:baseline.status,steps:baseline.steps,output_hex:results[name].output_hex,events,jumps,final_slots:slots(),compiled_code_visits_max:Math.max(...visits.values()),capture:{windows,overlaps,contiguous_steps:all.length,equivalent_runs:true},digest:baseline.state_digest_after};
}
writeFileSync(`${root}/rea.json`,JSON.stringify(reports,null,2)+'\n');console.log(`PASS: REA verifies outputs, physical CALL/RET, nested slot isolation and one-shot execution in ${Object.keys(reports).length} programs`);

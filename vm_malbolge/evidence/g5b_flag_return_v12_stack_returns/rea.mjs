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
 const mem=new Map([...source].map((v,i)=>[i,v]));let active=false,pending=null;
 const events=[],changes=[],mutations=[],pops=[],body_events=[],slot_reads=[];
 const flagsAt=[plan.d0,plan.d1,plan.s0,plan.s1];
 function state(){const flags=flagsAt.map(x=>mem.get(x));return {flags,depth:({'74,74':0,'70,74':1,'70,70':2})[flags.slice(0,2).join(',')]??-1,slots:flags.slice(2).map(x=>x===74?'A':x===70?'B':'?'),values:plan.variables.map(v=>mem.get(v))};}
 for(const e of all){
  let kind=null;
  if(e.position===plan.entry && Object.hasOwn(plan.markers,mem.get(e.d)+2)){active=true;kind=plan.markers[mem.get(e.d)+2];}
  if(e.position===plan.r_entry)kind='r_entry';if(e.position===plan.mix)kind='body';
  if(e.position===plan.rot && Object.hasOwn(plan.emissions,e.d))kind='emit_'+plan.emissions[e.d].char;
  if(kind){
   const snapshot={kind,step:e.step,pc:e.position,d:e.d,a:e.a,...state()};events.push(snapshot);
   if(kind==='body'){assert.equal(e.d,plan.variables[snapshot.depth-1]);body_events.push(e);}
   if(kind==='pop'){
    assert.equal(pending,null);const depth=snapshot.depth,token=depth?snapshot.slots[depth-1]:null;
    const target=depth===0?'emit_U':depth===1?'return_'+token:token==='A'?'resume':'emit_E';
    pending={step:e.step,depth,token,expected_target:target,before_flags:snapshot.flags};
   } else if(pending && ['resume','return_A','return_B','emit_E','emit_U'].includes(kind)){
    pops.push({...pending,actual_target:kind,return_step:e.step,return_pc:e.position,after_depth:snapshot.depth,matches_catalog:kind===pending.expected_target});
    assert.equal(snapshot.depth,pending.depth?pending.depth-1:0);pending=null;
   }
  }
  if(active && [plan.s0,plan.s1].includes(e.position))slot_reads.push({step:e.step,pc:e.position,opcode:e.opcode_name,...state()});
  const before=state();for(const w of e.writes){if(active && plan.variables.includes(w.position))assert.equal(e.position,plan.mix);mem.set(w.position,w.value_after);}const after=state();
  if(active && JSON.stringify(before.flags)!==JSON.stringify(after.flags))changes.push({step:e.step,pc:e.position,before:before.flags,after:after.flags});
  if(active && JSON.stringify(before.values)!==JSON.stringify(after.values))mutations.push({step:e.step,pc:e.position,before:before.values,after:after.values});
 }
 assert.equal(pending,null);assert.equal(pops.filter(p=>!p.matches_catalog).length,mode==='wrong_slot'?1:0);
 const final=state();for(const [key,value] of Object.entries({events,changes,mutations,final}))assert.deepEqual(value,local[mode][key]);
 reports[mode]={status:baseline.status,steps:baseline.steps,output_hex:local[mode].output_hex,events,changes,mutations,final,pops,body_events,slot_reads,capture:{windows,overlaps,contiguous_steps:all.length,equivalent_runs:true},digest:baseline.state_digest_after};
}
writeFileSync(`${folder}/rea.json`,JSON.stringify(reports,null,2)+'\n');console.log('PASS: native pop selects actual R continuation, nested contexts and guard/error paths verified');

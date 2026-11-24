import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const [dist,folder]=process.argv.slice(2);
const {runMalbolge}=await import(pathToFileURL(`${dist}/domain/malbolge/malbolgeClassic.js`));
const local=JSON.parse(readFileSync(`${folder}/results.json`)),reports={};
for(const mode of Object.keys(local)) {
 const plan=JSON.parse(readFileSync(`${folder}/${mode}.plan.json`));const source=readFileSync(`${folder}/${mode}.mb`);
 const prefix=runMalbolge(source.toString('latin1'),{maxSteps:10000,eventCaptureLimit:4096});
 const suffix=runMalbolge(source.toString('latin1'),{maxSteps:10000,eventCaptureLimit:4096,eventStartStep:Math.max(1,prefix.steps-4095)});
 for(const key of ['status','steps','output_bytes','state_digest_before','state_digest_after'])assert.deepEqual(prefix[key],suffix[key]);
 const merged=new Map(prefix.events.map(e=>[e.step,e]));let overlap=0;
 for(const e of suffix.events){if(merged.has(e.step)){assert.deepEqual(e,merged.get(e.step));overlap++;}merged.set(e.step,e);}
 const all=[...merged.values()].sort((a,b)=>a.step-b.step);assert.equal(all.length,prefix.steps);all.forEach((e,i)=>assert.equal(e.step,i+1));
 assert.equal(prefix.status,'HALTED');assert.equal(prefix.steps,local[mode].steps);assert.equal(Buffer.from(prefix.output_bytes).toString('hex'),local[mode].output_hex);
 const mem=new Map([...source].map((v,i)=>[i,v]));let active=false,maxDepth=0;
 const stack=[],events=[],clocks=[],mutations=[],dispatches=[],depths=[],inner_outer_writes=[];
 const state=()=>({fo:mem.get(plan.fo),values:plan.variables.map(v=>mem.get(v)),entry_word:mem.get(plan.entry),mix_word:mem.get(plan.mix),dispatch_word:mem.get(plan.dispatch)});
 for(const e of all) {
  if(e.position===plan.k){active=true;assert.equal(stack.length,0);clocks.push({step:e.step,...state()});}
  let kind=e.position===plan.entry?'entry':e.position===plan.mix?'body':e.position===plan.resume?'resume':null;
  if(active && e.opcode_name==='jmp' && [plan.a_cont,plan.b_cont].includes(e.d))kind=e.d===plan.a_cont?'return_A':'return_B';
  if(kind) {
   const from=stack.length;
   events.push({kind,step:e.step,pc:e.position,d:e.d,a:e.a,argument:kind==='entry'?mem.get(e.d):null,...state()});
   if(kind==='entry'){
    assert.ok(stack.length<2);const variable=mem.get(e.d)+3;assert.equal(variable,plan.variables[stack.length]);
    stack.push({variable,fo:mem.get(plan.fo),valueAfterBody:null});maxDepth=Math.max(maxDepth,stack.length);
   } else if(kind==='body'){
    assert.equal(e.d,stack.at(-1).variable);assert.equal(mem.get(plan.fo),stack[0].fo);
    if(stack.length===2)assert.equal(mem.get(plan.variables[0]),stack[0].valueAfterBody);
   } else if(kind==='resume'){
    if(mode==='bypass_inner')assert.equal(stack.length,1);
    else {assert.equal(stack.length,2);stack.pop();assert.equal(mem.get(plan.variables[0]),stack[0].valueAfterBody);}
   } else {assert.equal(stack.length,1);stack.pop();}
   depths.push({step:e.step,kind,from,to:stack.length});
  }
  if(e.position===plan.dispatch)dispatches.push({step:e.step,pc:e.position,d:e.d,frame_pointer:mem.get(e.d),...state()});
  const before=plan.variables.map(v=>mem.get(v));
  for(const w of e.writes){
   if(stack.length===2 && w.position===plan.fo)inner_outer_writes.push({step:e.step,...w});
   if(active && plan.variables.includes(w.position))assert.equal(e.position,plan.mix);
   mem.set(w.position,w.value_after);
  }
  if(kind==='body')stack.at(-1).valueAfterBody=mem.get(e.d);
  const after=plan.variables.map(v=>mem.get(v));if(active && JSON.stringify(before)!==JSON.stringify(after))mutations.push({step:e.step,pc:e.position,before,after});
 }
 assert.equal(stack.length,0);assert.equal(maxDepth,mode==='bypass_inner'?1:2);
 assert.equal(inner_outer_writes.length,mode==='outer_clobber'?3:0);
 for(const [key,value] of Object.entries({events,clocks,mutations,dispatches}))assert.deepEqual(value,local[mode][key]);
 assert.deepEqual(plan.variables.map(v=>mem.get(v)),local[mode].final_values);
 reports[mode]={status:prefix.status,steps:prefix.steps,output_hex:local[mode].output_hex,events,clocks,mutations,dispatches,depths,max_depth:maxDepth,inner_outer_writes,body_events:all.filter(e=>e.position===plan.mix),capture:{overlap_events:overlap,contiguous_steps:all.length,equivalent_runs:true},digest:prefix.state_digest_after};
}
writeFileSync(`${folder}/rea.json`,JSON.stringify(reports,null,2)+'\n');console.log('PASS: same entry/body/dispatcher reentered at depth 2, exterior context preserved, controls detected');

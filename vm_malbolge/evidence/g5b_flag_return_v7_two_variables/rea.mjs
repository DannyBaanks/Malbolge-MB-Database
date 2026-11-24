import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const [dist,folder]=process.argv.slice(2);
const {runMalbolge}=await import(pathToFileURL(`${dist}/domain/malbolge/malbolgeClassic.js`));
const local=JSON.parse(readFileSync(`${folder}/results.json`));
const records={};
for(const mode of Object.keys(local)) {
 const plan=JSON.parse(readFileSync(`${folder}/${mode}.plan.json`));
 const source=readFileSync(`${folder}/${mode}.mb`);
 const run=runMalbolge(source.toString('latin1'),{maxSteps:10000,eventCaptureLimit:4096});
 assert.equal(run.status,'HALTED');
 assert.equal(run.events_truncated,false);
 assert.equal(run.steps,local[mode].steps);
 assert.equal(Buffer.from(run.output_bytes).toString('hex'),local[mode].output_hex);
 const watched=[...plan.variables,plan.flag,plan.mix];
 const state=Object.fromEntries(watched.map(v=>[v,v<source.length?source[v]:null]));
 const calls=[],clocks=[],returns=[],mutations=[];
 let active=false;
 for(const e of run.events) {
  if(e.position===plan.k) {
   active=true;
   clocks.push({flag:state[plan.flag],mix:state[plan.mix],values:plan.variables.map(v=>state[v])});
  }
  if(active && e.opcode_name==='jmp' && [...plan.a_conts,plan.b_cont].includes(e.d)) returns.push(plan.a_conts.includes(e.d)?'A':'B');
  const before=plan.variables.map(v=>state[v]);
  if(e.position===plan.mix) calls.push({step:e.step,a:e.a,d:e.d,value:state[e.d],flag:state[plan.flag],before});
  for(const w of e.writes) {
   if(watched.includes(w.position)) state[w.position]=w.value_after;
   if(active && plan.variables.includes(w.position)) assert.equal(e.position,plan.mix);
  }
  const after=plan.variables.map(v=>state[v]);
  if(e.position===plan.mix) calls.at(-1).after=after;
  if(active && JSON.stringify(before)!==JSON.stringify(after)) mutations.push({step:e.step,pc:e.position,before,after});
 }
 assert.deepEqual(calls,local[mode].calls);
 assert.deepEqual(clocks,local[mode].clocks);
 assert.deepEqual(returns,local[mode].returns);
 assert.deepEqual(mutations,local[mode].mutations);
 assert.deepEqual(plan.variables.map(v=>state[v]),local[mode].final_values);
 records[mode]={status:run.status,steps:run.steps,output_hex:local[mode].output_hex,calls,clocks,returns,mutations,final_values:local[mode].final_values,site_events:run.events.filter(e=>e.position===plan.mix),digest:run.state_digest_after,all_events_retained:true};
}
writeFileSync(`${folder}/rea.json`,JSON.stringify(records,null,2)+'\n');
console.log('PASS: REA independently confirms variable isolation, recurrence, rearm and returns in four cases');

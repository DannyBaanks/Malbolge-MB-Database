import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const [dist,folder]=process.argv.slice(2);
const {runMalbolge}=await import(pathToFileURL(`${dist}/domain/malbolge/malbolgeClassic.js`));
const local=JSON.parse(readFileSync(`${folder}/results.json`));const reports={};
for(const mode of Object.keys(local)) {
 const plan=JSON.parse(readFileSync(`${folder}/${mode}.plan.json`));
 const source=readFileSync(`${folder}/${mode}.mb`);
 const run=runMalbolge(source.toString('latin1'),{maxSteps:10000,eventCaptureLimit:4096});
 assert.equal(run.status,'HALTED');assert.equal(run.events_truncated,false);
 assert.equal(run.steps,local[mode].steps);
 assert.equal(Buffer.from(run.output_bytes).toString('hex'),local[mode].output_hex);
 const watched=[plan.fo,plan.fi,plan.mix,plan.v];
 const state=Object.fromEntries(watched.map(v=>[v,v<source.length?source[v]:null]));
 let active=false,depth=0;const events=[],clocks=[],mutations=[],depths=[],inner_outer_writes=[];
 for(const e of run.events) {
  if(e.position===plan.k){active=true;clocks.push({step:e.step,fo:state[plan.fo],fi:state[plan.fi],mix:state[plan.mix],value:state[plan.v]});assert.equal(depth,0);}
  let kind=e.position===plan.entry?'outer_entry':e.position===plan.mix?'inner_entry':e.position===plan.after?'inner_return':null;
  if(active && e.opcode_name==='jmp' && [plan.a_cont,plan.b_cont].includes(e.d))kind=e.d===plan.a_cont?'outer_return_A':'outer_return_B';
  if(kind){
   const from=depth;
   if(kind==='outer_entry'){assert.equal(depth,0);depth=1;}
   else if(kind==='inner_entry'){assert.equal(depth,1);depth=2;}
   else if(kind==='inner_return'){assert.equal(depth,2);depth=1;}
   else {assert.equal(depth,1);depth=0;}
   events.push({kind,step:e.step,pc:e.position,d:e.d,a:e.a,fo:state[plan.fo],fi:state[plan.fi],value:state[plan.v]});
   depths.push({step:e.step,kind,from,to:depth});
  }
  const before=state[plan.v];
  for(const w of e.writes){if(depth===2 && w.position===plan.fo)inner_outer_writes.push({step:e.step,...w});if(watched.includes(w.position))state[w.position]=w.value_after;if(active && w.position===plan.v)assert.equal(e.position,plan.mix);}
  if(active && before!==state[plan.v])mutations.push({step:e.step,pc:e.position,before,after:state[plan.v]});
 }
 assert.equal(depth,0);assert.deepEqual(events,local[mode].events);assert.deepEqual(clocks,local[mode].clocks);assert.deepEqual(mutations,local[mode].mutations);
 assert.equal(inner_outer_writes.length,mode==='outer_clobber'?local[mode].returns.length:0);
 reports[mode]={status:run.status,steps:run.steps,output_hex:local[mode].output_hex,events,clocks,mutations,depths,inner_outer_writes,site_events:run.events.filter(e=>e.position===plan.mix),all_events_retained:true,digest:run.state_digest_after};
}
writeFileSync(`${folder}/rea.json`,JSON.stringify(reports,null,2)+'\n');console.log('PASS: REA confirms nested 0-1-2-1-0 paths and both controls');

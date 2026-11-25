import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const [dist,folder]=process.argv.slice(2);
const {runMalbolge}=await import(pathToFileURL(`${dist}/domain/malbolge/malbolgeClassic.js`));
const results=JSON.parse(readFileSync(`${folder}/results.json`));
const records={};
for(const mode of ['positive','control_a','control_b']) {
 const plan=JSON.parse(readFileSync(`${folder}/${mode}.plan.json`));
 const run=runMalbolge(readFileSync(`${folder}/${mode}.mb`,'latin1'),{maxSteps:10000,eventCaptureLimit:4096});
 const site=run.events.filter(e=>e.position===plan.mix);
 const clocks=run.events.filter(e=>e.position===plan.k);
 const returns=run.events.filter(e=>e.opcode_name==='jmp' && [plan.a_cont,plan.b_cont].includes(e.d)).map(e=>e.d===plan.a_cont?'A':'B');
 assert.equal(Buffer.from(run.output_bytes).toString('hex'),results[mode].output_hex);
 assert.equal(run.steps,results[mode].steps);
 assert.equal(run.events_truncated,false);
 assert.deepEqual(returns,results[mode].returns);
 assert.deepEqual(site.map(e=>({step:e.step,a:e.a,d:e.d})),results[mode].calls.map(e=>({step:e.step,a:e.a,d:e.d})));
 assert.equal(clocks.length,4);
 records[mode]={status:run.status,steps:run.steps,output_hex:results[mode].output_hex,site_events:site,returns,clock_steps:clocks.map(e=>e.step),digest:run.state_digest_after};
}
writeFileSync(`${folder}/rea.json`,JSON.stringify(records,null,2)+'\n');
console.log('PASS: REA agrees on positive and both negative controls');

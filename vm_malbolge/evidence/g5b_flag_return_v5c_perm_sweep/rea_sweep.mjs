import {readFileSync, writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const [pack, dist, output] = process.argv.slice(2);
const {runMalbolge} = await import(pathToFileURL(`${dist}/domain/malbolge/malbolgeClassic.js`));
const summary = JSON.parse(readFileSync(`${pack}/run01/sweep.json`));
const records = [];
for (const row of summary.runs) {
  const name = row.order.join('-');
  const source = readFileSync(`${pack}/run01/${name}/positive.mb`, 'latin1');
  const start = Math.max(1, row.local_trace_steps - 4095);
  const full = runMalbolge(source, {maxSteps:10000, eventCaptureLimit:4096});
  const window = runMalbolge(source, {maxSteps:10000, eventCaptureLimit:4096,eventStartStep:start});
  for (const key of ['status','steps','output_bytes','state_digest_before','state_digest_after']) assert.deepEqual(window[key], full[key], `${name}: ${key}`);
  assert.equal(window.steps, row.local_trace_steps);
  assert.equal(Buffer.from(window.output_bytes).toString('hex'), row.output_hex);
  const site = window.events.filter(e=>e.position===38058);
  const continuations = window.events.filter(e=>[15000,15004,15008,15012,15016].includes(e.position)).map(e=>e.position);
  assert.deepEqual(site.map(e=>e.a), [39999,12130,21990,7534,21990]);
  assert.deepEqual(site.map(e=>e.d), [40006,40006,40006,40006,40006]);
  assert.deepEqual(continuations,row.continuation_visits);
  assert.equal(window.events.at(-1).step, window.steps);
  records.push({order:row.order,start,steps:window.steps,status:window.status,site_calls:site.length,continuations,output_hex:row.output_hex,digest:window.state_digest_after,equivalence:true});
}
writeFileSync(output,JSON.stringify({schema:'g5b_p5c_rea_sweep_v1',records},null,2)+'\n');
console.log(`PASS: REA events and window equivalence for ${records.length} orders`);

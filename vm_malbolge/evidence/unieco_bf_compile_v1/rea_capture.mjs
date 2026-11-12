// Execute REA's source service in the REA checkout without rebuilding dist.
// Usage: node <this-script> <absolute-image> <new-redacted-json-path> <new-raw-json-path>
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const [image, output, rawOutput] = process.argv.slice(2);
if (!image || !output || !rawOutput) throw new Error('image and two output paths required');
const require = createRequire(`${process.cwd()}/package.json`);
const vite = await import(pathToFileURL(require.resolve('vite')).href);
const server = await vite.createServer({ configFile: false, server: { middlewareMode: true }, appType: 'custom' });
try {
  const { MalbolgeService } = await server.ssrLoadModule('/src/application/malbolge/MalbolgeService.ts');
  const result = await new MalbolgeService().trace({path:image, input_text:'\x00\x0a\x80\xff', eof_mode:'olmstead_1998', max_steps:20000, event_capture_limit:64});
  if (!result.ok) throw new Error(`trace failed: ${String(result.error)}`);
  const raw = JSON.stringify(result.value, null, 2) + '\n';
  await writeFile(rawOutput,raw,{flag:'wx',mode:0o600});
  const redacted=raw.split(image).join('compiled_relocated.mb');
  await writeFile(output,redacted,{flag:'wx'});
  const r=result.value.normalized_result;
  console.log(JSON.stringify({evidence_id:result.value.evidence_id, raw_sha256:createHash('sha256').update(raw).digest('hex'), status:r.run.status, steps:r.run.steps, output_bytes:r.output_bytes, events_truncated:r.run.events_truncated}));
  if (r.run.status !== 'HALTED' || JSON.stringify(r.output_bytes)!=='[0,10,128,255]') throw new Error('unexpected result');
} finally { await server.close(); }

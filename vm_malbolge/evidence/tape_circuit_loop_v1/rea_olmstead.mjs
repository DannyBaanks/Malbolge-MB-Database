// Run from the REA checkout: node <script> <image> <redacted-out> <raw-out> <input> <start-step> [max-steps].
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const [image, output, rawOutput, inputArg, start, maxSteps] = process.argv.slice(2);
const input = inputArg?.startsWith('hex:')
  ? Buffer.from(inputArg.slice(4), 'hex').toString('latin1')
  : inputArg;

if (!image || !output || !rawOutput || input === undefined || !start) {
  throw new Error('missing arguments');
}

const req = createRequire(`${process.cwd()}/package.json`);
const vite = await import(pathToFileURL(req.resolve('vite')).href);
const server = await vite.createServer({
  configFile: false,
  server: { middlewareMode: true },
  appType: 'custom',
});

try {
  const { MalbolgeService } = await server.ssrLoadModule('/src/application/malbolge/MalbolgeService.ts');
  const r = await new MalbolgeService().trace({
    path: image,
    input_text: input,
    max_steps: Number(maxSteps ?? 100000),
    event_start_step: Number(start),
    event_capture_limit: 4096,
    eof_mode: 'olmstead_1998',
  });
  if (!r.ok) {
    throw new Error(JSON.stringify(r.error));
  }
  const raw = JSON.stringify(r.value, null, 2) + '\n';
  await writeFile(rawOutput, raw, { flag: 'wx', mode: 0o600 });
  await writeFile(output, raw.split(image).join('<image>'), { flag: 'wx' });

  const n = r.value.normalized_result;
  console.log(
    JSON.stringify({
      id: r.value.evidence_id,
      raw_sha256: createHash('sha256').update(raw).digest('hex'),
      status: n.run.status,
      steps: n.run.steps,
      output_bytes: n.output_bytes,
      first_event: n.events[0]?.step,
      last_event: n.events.at(-1)?.step,
      truncated: n.run.events_truncated,
    }),
  );

  const rawBytes = Array.from(Buffer.from(input, 'latin1'));
  const want = [];
  for (let i = 0; i + 1 < rawBytes.length; i += 2) {
    want.push(rawBytes[i + 1], rawBytes[i]);
  }
  if (n.run.status !== 'HALTED' || JSON.stringify(n.output_bytes) !== JSON.stringify(want)) {
    throw new Error(`unexpected result: status=${n.run.status}, got=${n.output_bytes.length}B, want=${want.length}B`);
  }
} finally {
  await server.close();
}

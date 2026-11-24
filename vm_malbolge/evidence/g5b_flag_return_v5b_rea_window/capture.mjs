#!/usr/bin/env node
// Re-captura REA de G5b P5 con ventana de eventos tardía (event_start_step).
//
// Cierra el hueco documentado en ../g5b_flag_return_v5/REA.md: la captura de
// 4096 eventos reténía solo el prefijo (pasos 1..4096) y dejaba fuera el
// bloque compartido, por lo que la cobertura de llamadas/retornos por eventos
// quedó NOT_DEMONSTRATED.
//
// event_start_step no cambia la ejecución: los pasos anteriores se ejecutan
// igual; solo cambia qué eventos se retienen. Aquí se demuestra que la salida,
// los pasos y los digests de estado son idénticos a los ya registrados.
//
// Uso: node capture.mjs <ruta-al-dist-de-rea> <imagen.mb> [event_start_step]
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const [reaDist, imagePath, startArg] = process.argv.slice(2);
if (!reaDist || !imagePath) {
  console.error('uso: node capture.mjs <rea-dist-dir> <imagen.mb> [event_start_step]');
  process.exit(2);
}
const { runMalbolge } = await import(
  pathToFileURL(`${reaDist.replace(/\/$/, '')}/domain/malbolge/malbolgeClassic.js`).href
);

const source = readFileSync(imagePath, 'latin1');
const eventStartStep = startArg ? Number(startArg) : 1;

const full = runMalbolge(source, {
  maxSteps: 10_000,
  eventCaptureLimit: 4096,
  eventStartStep: 1,
});
const windowed = runMalbolge(source, {
  maxSteps: 10_000,
  eventCaptureLimit: 4096,
  eventStartStep,
});

const SITE = 38_058;
const CONT = [15_000, 15_004, 15_008, 15_012, 15_016];

function describe(run) {
  const site = run.events.filter((e) => e.position === SITE);
  const conts = run.events.filter((e) => CONT.includes(e.position));
  return {
    status: run.status,
    steps: run.steps,
    output_bytes: run.output_bytes,
    output_hex: run.output_bytes.map((b) => b.toString(16).padStart(2, '0')).join(''),
    peak_position: run.peak_position,
    writebacks: run.writebacks,
    representation_changes: run.representation_changes,
    state_digest_before: run.state_digest_before,
    state_digest_after: run.state_digest_after,
    events_retained: run.events.length,
    events_truncated: run.events_truncated,
    captured_step_range: run.events.length
      ? [run.events[0].step, run.events[run.events.length - 1].step]
      : null,
    site_calls: site.length,
    site_values_a: site.map((e) => e.a),
    site_d_values: [...new Set(site.map((e) => e.d))],
    continuation_visits: conts.map((e) => e.position),
    continuation_first_steps: Object.fromEntries(
      CONT.map((c) => [c, conts.find((e) => e.position === c)?.step ?? null])
    ),
  };
}

const report = {
  schema: 'g5b_p5b_rea_window_v1',
  tool: { name: 'rea', module: 'dist/domain/malbolge/malbolgeClassic.js', engine: 'malbolgeClassic' },
  image: imagePath,
  parameters: { max_steps: 10_000, event_capture_limit: 4096, event_start_step: eventStartStep },
  baseline_prefix_only: describe(full),
  windowed: describe(windowed),
  equivalence: {
    same_status: full.status === windowed.status,
    same_steps: full.steps === windowed.steps,
    same_output: JSON.stringify(full.output_bytes) === JSON.stringify(windowed.output_bytes),
    same_digest_before: full.state_digest_before === windowed.state_digest_before,
    same_digest_after: full.state_digest_after === windowed.state_digest_after,
  },
  window_is_suffix_of_run:
    windowed.events.length > 0 &&
    windowed.events[windowed.events.length - 1].step === full.steps,
};

console.log(JSON.stringify(report, null, 2));

# G5b P5b: ventana REA tardía — cierre de la cobertura por eventos

Fecha: 2026-11-24. Extiende [`g5b_flag_return_v5`](../g5b_flag_return_v5/VERDICT.md)
sin reescribir nada de ese pack. Resultado: **PASS — la cobertura de llamadas y
retornos por eventos REA queda demostrada**.

## El hueco que cierra

`g5b_flag_return_v5/REA.md` registró `captured_shared_site_events: 0` porque la
captura retenía los pasos 1–4096 y el bloque compartido se ejecuta al final. El
veredicto P5 dejó por eso la cobertura de rutas como `NOT_DEMONSTRATED`.

La causa era una restricción de la **herramienta**, no del programa: el tope de
`event_capture_limit` es 4096 en
`rea/src/domain/malbolge/malbolgeAnalysis.ts:96`
(`z.number().int().min(0).max(4096)`). El motor siempre ejecuta el presupuesto
completo de pasos; el 4096 solo limita cuántos eventos se **retienen**.

`event_start_step` (rea `32aade1ac`, 2026-11-12) resuelve esto: fija el primer
paso elegible para captura, y **los pasos anteriores se ejecutan igual**. Con
una ventana tardía, los 4096 eventos cubren el tramo final.

## Medición

Captura con `capture.mjs` sobre el `dist` compilado de rea (incluye
`event_start_step`). Se corrieron dos veces por imagen: la corrida de referencia
con la ventana completa y la ventana tardía, más una repetición para determinismo.

| Medición | Positivo `lll→rr→lr→rl→llr` | Control (`f_extra` en `lll`) |
|---|---|---|
| `event_start_step` | 628 | 711 |
| Pasos capturados | 628 → 4723 | 711 → 4806 |
| Llamadas al sitio `pc=38058` | **5** | **1** |
| `d` en las llamadas | `40006` (las 5) | `40006` |
| Valores `a` en el sitio | `39999, 12130, 21990, 7534, 21990` | `39999` |
| Retornos visitados | `15000→15004→15008→15012→15016` | `15016` |
| Salida | `62e66ee66e` | `62` |

Los cinco eventos del sitio comparten `d=40006` y `opcode_name=crazy`. El orden
de continuaciones es el previsto en el protocolo P5.

## Equivalencia con lo ya registrado

Cada valor medido en P5 se preserva exactamente. Compara contra
[`../g5b_flag_return_v5/rea_summary.json`](../g5b_flag_return_v5/rea_summary.json):

| Campo | Positivo | Control |
|---|---|---|
| `steps` | 4723 = 4723 | 4806 = 4806 |
| `output_bytes` | `[98,230,110,230,110]` = ídem | `[98]` = ídem |
| `peak_position` | 38883 = 38883 | 38507 = 38507 |
| `writebacks` | 6066 = 6066 | 6188 = 6188 |
| `representation_changes` | 5685 = 5685 | 5809 = 5809 |
| `state_digest_before` | `93d3bf61…` = ídem | `78f76b01…` = ídem |
| `state_digest_after` | `76426f46…` = ídem | `20cff9e6…` = ídem |

La ventana no altera la ejecución: cambia qué se retiene, no qué ocurre. El
prefijo de 4096 eventos (`baseline_prefix_only` en los JSON) sigue dando
`site_calls: 0`, que reproduce el `NOT_DEMONSTRATED` original.

## Determinismo

Dos corridas del positivo producen JSON idéntico byte a byte (SHA-256
`8cc2411072e65dfa…` en ambas).

## Lo que esto NO demuestra

- No mide el barrido de órdenes de cinco llamadores (120 permutaciones): sigue
  pendiente.
- No cubre más de cinco hojas, varias variables, entrada/EOF ni recursión.
- No sustituye a Olmstead, `clasesbolge` ni al trazador local: confirma por
  eventos REA lo que esos motores ya reportaban.

## Reproducción

```sh
REA=<ruta-a-rea>/dist
node capture.mjs "$REA" ../g5b_flag_return_v5/run01/positive.mb 628
node capture.mjs "$REA" ../g5b_flag_return_v5/run01/control/negative.mb 711
python3 verify.py
```

Artefactos: [positive.json](positive.json), [control.json](control.json),
[manifest.json](manifest.json), [hashes.sha256](hashes.sha256).

# epoch_audit_v1 — auditoría de `epoch_resolver_epoch_select_v1` y `epoch_rearm_barrier_v1`

- Auditor: claude_code_a029a379be0f4681 (Claude Code, Opus 5.5), a pedido de Danny.
- Fecha: 2026-11-10 (hora local) / 2026-11-11T04:3xZ.
- Commit auditado: `b85260f` (origin/master en ese momento, árbol limpio).
- Entorno: Linux 7.0.0-42-generic, Python 3.12.3.
- Alcance: sólo esos dos packs y las dependencias que declaran sus manifests. No
  se reescribe nada de los packs auditados: las correcciones van como adiciones a
  sus VERDICT.

## Método

1. Se extrajo `b85260f` a una copia limpia con `git -c core.autocrlf=false archive`.
   Se copió aparte el binario C, que está en `.gitignore`.
2. Se verificaron los SHA-256 de `artifacts` y `dependencies` de los dos manifests.
3. Se volvieron a correr `build.py .` y `probe.py` de los dos packs en la copia, y
   se comparó byte a byte con lo commiteado.
4. Se escribieron dos scripts **que no importan nada del repo**, con las tablas
   tomadas de la especificación:
   - `indep_interpreter.py`: intérprete Classic propio, en modo permisivo y en
     modo con la guarda de imprimibilidad del runner C. Ejecuta las 7 instancias,
     los 3 controles y un barrido de los 256 bytes de época.
   - `barrier_remeasure.py`: vuelve a medir M2, M3, M4 y M7, el lema del
     semigrupo y las épocas candidatas, y los amplía con modelos alternativos.
5. Salida cruda: `stdout.raw.txt`. Hashes: `SHA256SUMS.txt`.

Reproducción:

```
cd vm_malbolge/evidence/epoch_audit_v1
python3 -I indep_interpreter.py ../epoch_resolver_epoch_select_v1/resolver_epoch.mb
python3 -I barrier_remeasure.py ../epoch_resolver_epoch_select_v1/resolver_epoch.mb
```

## Confirmado

| afirmación | resultado de la auditoría |
|---|---|
| hashes de los manifests | coinciden todos, salvo `epoch_resolver_epoch_select_v1/VERDICT.md`, que recibió una adición después de generar el manifest (ver H6) |
| reproducción | `build.py` y `probe.py` de los dos packs regeneran byte a byte la imagen (`41cdbc79…`), `results.json`, `build_index.json`, `position_table.json` y `stdout.raw.txt` |
| 7 instancias del selector | el intérprete independiente reproduce OUT, `pc = T`, END en `T+1`, 218 pasos, el payload exacto en la celda elegida y la máscara 29524 en las otras dos |
| guarda del runner C | con la guarda activa, el intérprete independiente para en el paso 217 en las 6 instancias con payload no imprimible y completa `e100_p93` |
| controles A, B y C | se reproducen |
| M1 = 0/2400, M2 = 839/2400 | se reproducen |
| M3 = 26 materializables (modelo de un ROT) | se reproduce, también probando todas las palabras de control posibles y no sólo la primera |
| M4 = 34/3200 (modelo del pack) | se reproduce |
| M7: con una celda sembrada sólo se llega a 34..127 | resiste una alternativa que el pack no probó: las celdas de **relleno** del cargador (4 valores distintos) no dan ningún destino en 128..339 |
| semigrupo de un operando: 15 mapas | se reproduce; con los operandos invertidos salen 17 (trampa T24), así que el pack usó la orientación correcta |
| 92 épocas candidatas | se reproduce con la regla del pack |

No se volvieron a medir M5, M6 ni el lema de los tripletes de opcodes.

## Hallazgos

### H1 (ALTA): la tabla de posiciones de M3/M4 es un límite del modelo de carga, no de Classic

M3 y M4 suponen que la palabra que necesita el acumulador sólo se puede cargar con
**un `ROT`** desde una celda sembrada (840 palabras en órbitas imprimibles). Si se
permite **un `CRAZY` de preparación** (cargar `x` con `ROT` desde una celda
sembrada y hacer `CRAZY` contra otra celda sembrada rotada a `y`, que deja
`a = crazy(x, y)`), las palabras alcanzables pasan a ser 8281 y:

- M3: la palabra de control es materializable en **839 de 839** pares
  restaurables (antes 26);
- M4: `swap01(v)` es cargable en **3200 de 3200** pares (antes 34).

Así que la "tabla de posiciones" de 34 celdas no restringe a Classic, sólo al
modelo de un `ROT`. Un planificador que la respete estaría sobrerrestringido.
**NOT_DEMONSTRATED**: el coste real de la vía `ROT` + `CRAZY` (pasos, rutado del
puntero `d`, rearm de la celda auxiliar que el `CRAZY` modifica).

### H2 (ALTA): parte de las "8 mediciones" están escritas a mano

- M8: `current_loop_body_size_estimate = 200` y
  `capacity_sufficient_for_current_body = False` son literales; la puerta
  `not False` pasa siempre. M8 no es una medición.
- M7: el alcance sembrado es `range(34, 128)` fijado a mano (es correcto por
  aritmética, pero la puerta no mide nada del programa).
- M6: `chain_cell_free_in_current_layout` compara contra `(55, 65, 75)` fijo.
- Los docstrings de `epoch_rearm_barrier_v1/probe.py` y `build.py` contradicen
  los resultados: dicen 65% (sale 35%), "0 en órbita imprimible" (salen 26) y
  "452 direcciones" (salen 36). Las hipótesis y las puertas se ajustaron después
  de medir y ese cambio no quedó registrado.

### H3 (MEDIA): el dialecto de Classic no está declarado

- 24 de las 340 celdas de `resolver_epoch.mb` (41–50, 52–54, 63, 69, 75, 100,
  102, 103, 106, 108, 109, 112 y 114: la zona de dato) no decodifican a un opcode
  válido en su posición. Pasa lo mismo en `epoch_algebra_v3/resolver.mb` (10
  celdas) y en `epoch_resolver_request_v1/resolver_request.mb` (16). Según
  recuerda el auditor, el cargador del intérprete de Olmstead (1998) rechaza esos
  programas ("invalid character in source file"). **No se pudo confirmar contra la
  fuente** (en línea no fue accesible durante la auditoría): `NOT_DEMONSTRATED`.
- En 6 de las 7 instancias, la ejecución del payload la confirman sólo motores
  Python; el runner C para en la guarda. Además, los dos trazadores Python están
  en el mismo `probe.py` y comparten el bucle (sólo cambian las tablas). El
  intérprete de esta auditoría es un motor independiente más y coincide.
- Recomendación: etiquetar la línea de épocas como **"Classic permisivo"**
  (cargador sin validación y ejecución de celdas no imprimibles).

### H4 (MEDIA): el control C sólo probó un byte

Barrido de los 256 bytes de época con el payload 29797: ningún byte fuera del
catálogo hace aterrizar el payload en una celda de época (confirma el pack), pero
**30 de los 253 bytes fuera de catálogo sí producen salida** (por ejemplo, b = 21
emite `0d0d59` y b = 234 emite `148989`). El pack probó b = 50, que es silencioso.
"No selecciona ninguna época" es cierto; "no pasa nada" no lo es.

### H5 (BAJA): dos lemas dicen más de lo que miden

- Semigrupo: 15 mapas es correcto en el modelo de **un** operando (componer
  `a -> crazy(a, k)`). Con **dos** operandos (como el `crazy(M, P)` que usa el
  propio pack) y las constantes 0, 1 y 2, el cierre tiene 27 mapas y
  `(0,2,0) = crazy(a=1, mem=crazy(a=2, mem=x))`. Lo que limita es el modelo, no
  "el álgebra". La constante 59048 (todo 2) no es alcanzable con `ROT` + un
  `CRAZY`, así que la ruta práctica queda **NOT_DEMONSTRATED**.
- M3: "la palabra de control es siempre 29403" sale de que `ctrl_for` toma la
  primera solución; probando todas, hay 4 palabras posibles. El 26 se mantiene.

### H6 (BAJA): inconsistencias de bookkeeping

- `epoch_resolver_epoch_select_v1/manifest.json` no se regeneró tras la adición
  del VERDICT, y `epoch_rearm_barrier_v1/manifest.json` registra el hash viejo de
  ese VERDICT como dependencia.
- Zona de dato: 34..126 en el selector y 41..126 en la barrera (de ahí las 86
  celdas de M8).

### H7 (ENTORNO)

- `.git/config` de este repo tiene `core.autocrlf=true`: `git archive` o un clon
  con esa configuración sale con CRLF y fallan **todos** los hashes de los
  manifests. Los blobs están en LF.
- `runners/malbolge-original/malbolge` está en `.gitignore`: un clon no puede
  reproducir la parte C. Su `manifest.json` describe el `.exe` de Windows
  (`9A7AD87E…`), no el ELF que usan los packs (`3257f1ae…`).

## Tabla de afirmaciones

| afirmación auditada | estado tras la auditoría |
|---|---|
| la petición elige época y payload (selector) | DEMONSTRATED en Classic permisivo; el dialecto se declara en H3 |
| 4 motores coinciden | parcial: en 6/7 instancias la ejecución del payload la confirman sólo motores Python (más el intérprete de esta auditoría) |
| un byte fuera de catálogo no selecciona época | DEMONSTRATED (barrido de 256 bytes); pero 30 bytes producen salida (H4) |
| "limitación del álgebra" (semigrupo) | sólo en el modelo de un operando (H5) |
| barrera = tabla de posiciones (M3/M4) | **no se sostiene como barrera de Classic**; vale para el modelo de un ROT (H1) |
| M7 alcance sembrado 34..127 | confirmado, también frente al relleno del cargador |
| M8 el diario no cabe | NOT_DEMONSTRATED: valores escritos a mano (H2) |

## NOT_DEMONSTRATED (de esta auditoría)

- El comportamiento del cargador y de la ejecución del intérprete de Olmstead de
  1998 (H3): no se pudo consultar la fuente.
- El coste de la vía `ROT` + `CRAZY` (H1).
- M5, M6 y el lema de los tripletes de opcodes: no se volvieron a medir.

## Siguiente paso propuesto

Un pack corto que mida el coste real de la vía `ROT` + `CRAZY` para la palabra de
control y para `swap01(v)`, y que mida M8 de verdad (tamaño del cuerpo del bucle a
partir de la imagen, no un estimado), antes de construir el planificador.

## Adición 2026-11-11 — dialecto confirmado y auditoría de `epoch_rearm_cost_v1` (sólo se añade)

Auditor: claude_code_a029a379be0f4681. Commit auditado: `99ee3de` (local, sin push en
ese momento). Script: `addendum_checks.py`; salida cruda:
`stdout_addendum_2026-11-11.raw.txt`.

### H3 pasa a DEMONSTRATED

La fuente del intérprete de Ben Olmstead (1998) está en el repo hermano
`Malbolge-PureEpoch/vendor/olmstead_original.c` (sha256 `05abd38e…`, cabecera
"'98 Ben Olmstead", dominio público). Compilada con `gcc -O2 -w`:

- el cargador rechaza (`invalid character in source file`) `resolver_epoch.mb` y,
  probado por separado con el mismo binario, `epoch_algebra_v3/resolver.mb` y
  `epoch_resolver_request_v1/resolver_request.mb`;
- el bucle de ejecución hace `if ( mem[c] < 33 || mem[c] > 126 ) continue;`: una
  celda no imprimible en el PC produce un **bucle infinito**, no una ejecución.

La línea de épocas es, por tanto, **Classic permisivo**, y no corre en el intérprete
de 1998. (Contraste: los programas de PureEpoch probados sí pasan ese cargador.)

### Auditoría de `epoch_rearm_cost_v1`

Confirmado:

| comprobación | resultado |
|---|---|
| hashes del manifest (12 artefactos + 4 dependencias) | coinciden, en una copia limpia con `core.autocrlf=false` |
| reproducción | `build.py` + `probe.py` regeneran las tres imágenes y `results.json` byte a byte |
| orden de las puertas | `GATES.md` (`6a604fe`, 23:35) se commiteó antes del pack (`99ee3de`, 23:48) y no se modificó después |
| intérprete independiente | `restore` 2a37/21/HALTED, `no_restore` 2a/21/HALTED, `rearm` 2a/28/HALTED, con y sin guarda |
| álgebra de C1/C2 | `crazy(rot(54), 74) = 29552` y `crazy(29552, ENC[55]) = 55`: el restore 110→55 es exacto |
| H1 (en un caso) | la celda 44 no está en la tabla de 34 posiciones y aun así se restaura y se re-ejecuta en una sola ejecución |

Hallazgos:

- **H8 (ALTA): el M8 = 12 no responde a H2.** Ese 12 es el cuerpo del programa de
  demostración de 105 bytes. La pregunta de H2 era el cuerpo del **resolvedor de
  épocas**. Medido desde la traza (`e100_p29797`): **218 celdas de código distintas
  en 218 pasos, ninguna ejecutada dos veces**, en el rango 0..339, y sólo 2 dentro
  de 34..126. El literal `200` de `epoch_rearm_barrier_v1` era un estimado sin
  medir, pero estaba cerca: el valor medido es 218. Volver a atender una petición
  con ese cuerpo exige restaurar del orden de 218 celdas, no 12.
- **H9 (MEDIA): dialecto.** Las tres imágenes del pack también las rechaza el
  cargador de 1998 (78/105, 78/105 y 70/105 celdas no válidas). El pack lo declara
  en `GATES.md` ("Classic permisivo"), así que es correcto como está escrito. Pero el
  "tercer motor" de G1 es el runner C de `Malbolge-Engine`, **no** el intérprete
  de Olmstead.
- **H10 (BAJA): G2 es una especificación, no un umbral.** La puerta fija "exactamente
  5 instrucciones (`DLOAD,DLOAD,ROT,DLOAD,CRAZY`)" antes de implementar: codifica el
  diseño ya conocido, así que el coste de 5 es el de este caso construido, no una
  cota general.
- **H11 (BAJA): robustez del probe.** `run_c` no fija el stdin del runner C, que
  hereda el del proceso padre. Con un stdin abierto que no llega a EOF, el probe
  agota su timeout de 120 s y termina con `exit 1`; con `</dev/null` pasa. Además,
  `stdout.raw.txt` no incluye la línea final `[verdict] all_checks_pass=True` que el
  probe sí imprime.

Tabla de afirmaciones (adición):

| afirmación | estado |
|---|---|
| H3: el dialecto de la línea de épocas no es Olmstead 1998 | **DEMONSTRATED** (cargador de 1998) |
| la palabra de control se carga con ROT + 1 CRAZY y el restore es exacto (un caso) | DEMONSTRATED en Classic permisivo |
| restore + re-ejecución en una sola ejecución, con control negativo | DEMONSTRATED en Classic permisivo |
| M8 del resolvedor de épocas | **218 celdas medidas** (no 12, no 200) |
| ciclo cerrado (rearm de todas las auxiliares) | NOT_DEMONSTRATED (igual que el pack) |

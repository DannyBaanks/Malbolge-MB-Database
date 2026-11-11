# epoch_dload_compose_v1 — veredicto

Responde a las puertas de `GATES.md` (commit `15fe38b`, pre-registrado antes de
`probe.py`, más la adición fechada `ebaf700`, escrita antes de la corrida canónica).
Repo MALBOLGE-MB-DATABASE, local sin push. Autor: `opencode_handoff_mbdb_1794xxxxx`
(handoff de `claude_code_87747efe962f42f4`, bridge seq 12135/12136, pedido de Danny),
2026-11-11. Base `f161c8a`.

## Resultado

**G0..G4 true** con una salvedad declarada en Q4: el motivo de `ctrl_dload_phase` se
enmendó por adición fechada antes de la corrida canónica, porque la predicción
original `2, 0, 2, 0, …` es **FALSA** en los tres objetivos. G4 se evalúa con la
enmienda; las dos lecturas están abajo.

El `DLOAD` que reinicia `d` de `epoch_dload_reset_v1` **se compone con OUT, ROT y
CRAZY** en un solo bucle de tabla constante: cada imagen cierra las 10 000 vueltas
medidas con exactamente una X y un `DLOAD` por vuelta, y su estado completo se repite
con periodo **3060**. Esto cierra C9 de `epoch_dload_reset_v1`.

Dialecto: **Classic permisivo (3^10)**. El cargador de Olmstead 1998 rechaza las tres
imágenes (Q5).

## Q1 — construcción

Parámetros derivados en el probe desde los ciclos de XLAT2 y los parámetros medidos,
no copiados de la tabla de papel; las cuatro ecuaciones del punto fijo se comprueban
leyendo los bytes de la imagen (`q1.fixed_point`, `G0.image_checks`). `shift = 60`,
`T = 59` en los tres.

| X | δ | e | J | n | D0 | V0 | V1 | datos (A,B,C,D) | d en la X | W | r | largo | sha256 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OUT | 59 | 0 | 124 | 65 | 127 | 66 | 66 | 127, 130, 135, 126 | 125 | 68 | 1 | 137 | `d92fe18e…` |
| ROT | 93 | 0 | 158 | 99 | 161 | 66 | 66 | 161, 164, 169, 160 | 159 | 102 | 1 | 171 | `de244cc3…` |
| CRAZY | 22 | 12 | 99 | 40 | 114 | 78 | 78 | 114, 117, 122, 113 | 100 | 55 | 1 | 124 | `b48d45dd…` |

**Coinciden exactamente con la predicción en papel** de `GATES.md` (15/15 campos por
objetivo, `q1.all_match_prediction = true`): el cálculo independiente del probe
(`independent_derive`, con las tablas del motor scratch y código propio) reproduce
los mismos parámetros (`G0.independent_rederivation = true`).

Estructura leída de los bytes: las tres imágenes son imprimibles; el par de `DLOAD`
(offsets 0 y 4) y el par de X (δ y δ+4) valen 74 y decodifican 40 / `op`; el `JMP`
decodifica 4; el trampolín `T = 59` y las celdas de tabla llevan el valor declarado;
las semillas (celda 0 = 40, celda 1 = 39 → lee `mem[41] = W`) son las calculadas. Los
sha256 completos están en `results.json` (`images`) y en `manifest.json`.

**Relleno (defecto encontrado y corregido antes de la corrida canónica).** La primera
corrida exploratoria usaba `filler_value` de `epoch_xlat2_block_v1`, cuyo ciclo XLAT2
puede incluir 68 (NOP): un opcode **válido**, que violaba el conjunto `{4, 40, op}` ya
pre-registrado en G2 (`body_valid_ops` salía `[4, 5, 40, 68]`). `probe.py` usa ahora
un relleno estricto (ciclo entero sin ningún opcode válido), verificado como existente
en todas las posiciones 60..199. No se cambió ninguna puerta; se ajustó la
construcción a G2. Ver la adición fechada de `GATES.md` (commit `ebaf700`).

## Q2 — 10 000 vueltas compuestas

| X | vueltas | pasos | X/vuelta | DLOAD/vuelta | opcodes del cuerpo | destinos de JMP | `d` al empezar | `d` en la X |
|---|---|---|---|---|---|---|---|---|
| OUT | 10 000 | 650 060 | 1 | 1 | `{4, 5, 40}` | `{59}` | `{127, 131}` | `{125}` |
| ROT | 10 000 | 990 060 | 1 | 1 | `{4, 39, 40}` | `{59}` | `{161, 165}` | `{159}` |
| CRAZY | 10 000 | 400 060 | 1 | 1 | `{4, 40, 62}` | `{59}` | `{114, 118}` | `{100}` |

`d` al empezar la vuelta toma exactamente dos valores (las dos paridades), `d` en la X
un único valor —fuera del código y de las cuatro celdas de dato—, y el cuerpo no
contiene ningún otro opcode válido. El criterio G2 completo (`criterion.checks`) es
true en los tres.

Motores, en la misma ejecución acotada (tope = paso del `JMP` número R según el
trazador):

* oráculo (`MAX_STEPS`), intérprete independiente (`MAX`), motor scratch (`MAX`) y
  runner C (`TIMEOUT`, rc 0) llegan **exactamente al tope** en los tres objetivos;
  ninguno para antes.
* OUT: los cuatro motores emiten **10 000 bytes**, todos `0x00` (en este dialecto OUT
  no modifica `a`, que vale 0), idénticos byte a byte.
* sha256 de la memoria final (59 049 celdas) **idéntico** en trazador, scratch e
  intérprete independiente: OUT `4b1b84da…`, ROT `a5d19ce8…`, CRAZY `69caf34d…`.
* trazador y scratch coinciden en la lista completa de destinos de `JMP` y en `d` al
  empezar cada vuelta.

El oráculo y el runner C no exponen memoria; su acuerdo es de tope y salida (G1).

## Q3 — periodicidad del estado

Se cifran cada vuelta el cuerpo `[60, J]` y el trampolín 59: 66 celdas en OUT, 100 en
ROT, 41 en CRAZY. Los ciclos XLAT2 presentes miden `2, 4, 5, 6, 9, 68` en los tres.

**Predicho:** `P = mcm(2, 4, 5, 6, 9, 68) = 3060`. **Medido:** el hash de
`(mem[0..59048], a, c, d)` al empezar la vuelta se repite por primera vez entre las
vueltas **0 y 3060** (OUT), **1 y 3061** (ROT) y **2 y 3062** (CRAZY) → `P = 3060`, y
`d` tiene periodo 2 en los tres. La máquina es determinista: un estado repetido
significa que el bucle se repite indefinidamente en este dialecto y semántica.

El pre-periodo 0/1/2 no es ruido: cada objetivo arranca el punto fijo en una fase
distinta y el primer estado idéntico aparece en la vuelta indicada.

## Q4 — controles negativos (doce)

| control | OUT | ROT | CRAZY |
|---|---|---|---|
| `k_off` (tabla impar = `T+1`) | JMP malo en la vuelta 1 (destino 60); HALT | igual | igual |
| `no_dload` (par de DLOAD → relleno estricto) | 1 vuelta con 0 DLOAD; JMP a 29554; HALT | igual (29551) | igual (33) |
| `op_phase` (2.ª celda de X = 70) | X por vuelta `2, 0, 2, 0, …` (60 vueltas) | igual | igual |
| `dload_phase` (2.ª celda de DLOAD = 70) | DLOAD por vuelta `[2, 0]` y muere | `[2, 0, 0]` y muere | `[2]` y muere |

Los doce rompen el criterio (`breaks_as_declared = true` y `criterion.ok = false`), y
los cuatro motivos declarados se observan.

**Salvedad de `dload_phase` (publicada, no escondida).** La redacción original de
`GATES.md` predecía `2, 0, 2, 0, …`. Eso es **FALSO**: en OUT y ROT el patrón es
`[2, 0]` y en CRAZY `[2]`; tras ese round el `JMP` cae fuera del trampolín y la
ejecución muere. Lo que sí se mide en los tres es un round cerrado con **2 DLOADs**
(el par dejó de alternar). La adición fechada `ebaf700`, escrita antes de la corrida
canónica, enmienda el motivo declarado a esa frase; G4 se evalúa con la enmienda.
Quien lea G4 contra el texto original de `15fe38b` debe considerar `dload_phase`
fallido: la predicción `2, 0, 2, 0` no se cumplió.

## Q5 — cargador de 1998

`olmstead` rechaza las tres imágenes con `invalid character in source file` (rc 1):
sólo 8 de 137 celdas (OUT), 8 de 171 (ROT) y 10 de 124 (CRAZY) decodifican un opcode
válido al cargar. Dialecto declarado: **Classic permisivo (3^10)**.

## Claims

Ver `manifest.json` (C1..C10). En corto: C1–C7 DEMONSTRATED; C8 (componer `IN`), C9
(una variante que pase el cargador de Olmstead 1998) y C10 (que el bucle haga un
cálculo elegido) NOT_DEMONSTRATED.

## NOT_DEMONSTRATED

* **`IN`**: el cuarto objetivo de `epoch_xlat2_block_v1` sigue sin componer; sólo se
  midieron OUT, ROT y CRAZY.
* **Una variante compatible con el cargador de Olmstead 1998**: las tres imágenes
  usan celdas de código que el cargador rechaza. Q5 sólo declara el dialecto.
* **"Para siempre"** vale en el modelo de Q3 (estado repetido en un motor determinista,
  con acuerdo de motores en el tramo medido); no se ejecutaron infinitos pasos.
* **La memoria final del oráculo y del runner C**: no la exponen; su acuerdo se limita
  a no parar antes del tope (y, en OUT, a los 10 000 bytes de salida).
* **Que el bucle haga algo útil**: las tres composiciones ejecutan una operación por
  vuelta sobre celdas de dato fijas; usarlas dentro de un programa que calcule algo
  elegido por la petición queda fuera de alcance.
* **La predicción `2, 0, 2, 0, …` de `ctrl_dload_phase`**: medida y **FALSA** (ver Q4).

## Reproducción

```
cd vm_malbolge/evidence/epoch_dload_compose_v1
python3 -I probe.py </dev/null > stdout.raw.txt 2>&1   # rc 0, ~14 s, G0..G4 true
python3 manifest.py
```

Dos corridas consecutivas: `results.json` byte a byte idéntico
(`sha256 987297e583dc5e95adf7291ec54faa71cbbc3f052150e4fdd22758d4474dc78a`) y
`stdout.raw.txt` byte a byte idéntico
(`sha256 511cb0f50854eae371cec9aa7d1a9aff7d244056e3d9c58456fe6a4d9f2d3282`).

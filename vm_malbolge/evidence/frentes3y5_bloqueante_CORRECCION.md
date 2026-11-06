# CORRECCIÓN al bloqueante de los frentes 3 y 5

Este fichero **no reescribe** `frentes3y5_bloqueante.md`; lo corrige con
evidencia nueva (regla 10 de AGENTS.md: nunca reescribir evidencia cruda).

## El enunciado corregido

El bloqueante decía: *"no existe en el corpus una imagen Classic que itere sobre
un flujo de bytes"*. Eso es **falso**. Quedaba acotado al corpus `vm_malbolge`
de este repo y era anterior a estos artefactos.

## Evidencia 1 — del corpus hermano (BolgeForge)

`BolgeForge/artifacts/cat_compact.mal` — imagen Classic, **7.596 celdas**,
bucle de fetch real, commiteada en `7b4fbac` (2026-10-26).

Verificada **con los motores de ESTE repo** (no con el oráculo de BolgeForge):

| motor | `A` | `AB` | `HELLO` | vacío | 4.096 aleatorios |
|---|---|---|---|---|---|
| `runners/malbolge-original/malbolge` | `A` | `AB` | `HELLO` | (vacío) | 4.096 bytes, idénticos |
| `tools/oracle_classic.py` (`stop_on_eof=True`) | `41` | `4142` | `48454c4c4f` | (vacío) | — |

sha256 del artefacto: `dd8f9b10…3479b`. El byte extra que emite el runner C al
final es el salto de línea que añade él mismo (verificado: sin él, la salida de
4 KiB es idéntica a la entrada).

También existen `cat_compressed.mal` (8.254 celdas) y
`reference/malbolge_org/cat.mal` (Lutter 2012). MicroCat y los `twostroke`
están refutados/retirados en `BolgeForge/docs/CLAIMS.md`.

## Evidencia 2 — de este repo, ahora commiteada

`third_party/lmao/example_simple_cat.hell` (LMAO 0.6.0, GPL-3) ensamblado:

- `vm_malbolge/src/simple_cat_lmao.mb`, 2.051 bytes,
  sha256 `949a57f8bc664dc27abaf92e3f64b48637bc02319c01ad70020f16fdd321778c`.
- Verificado: eco de `HELLO` correcto (1.906 pasos). Reproducible con
  `./third_party/lmao/lmao -d -o vm_malbolge/src/simple_cat_lmao.mb third_party/lmao/example_simple_cat.hell`

Nota: `ANDAMIO_ITERANTE.md` y `frente3_veredicto_final.md` citaban este binario
cuando **solo existía en /tmp**. Queda ahora commiteado para que la cadena de
evidencia sea íntegra.

## Evidencia 3 — nativo, este repo

`vm_malbolge/src/mbir_native_fold_loop.mb` (130 bytes) + su emisor: bucle de
fetch real con celda de estado que sobrevive entre bytes, 9/9 acuerdo entre
motores y 4 KiB exactos. Detalle en `native_fold_loop.md`.

## Síntesis

| enunciado del bloqueante | estado |
|---|---|
| "no hay imagen Classic que itere sobre flujo" | **REFUTADO** (3 artefactos, 2 verificados en motores propios) |
| "no hay iteración que heredar" | **REFUTADO**: `simple_cat` (2.051 B, commiteado) y `cat_compact` (7.596 celdas) |
| "construir la iteración exige flags de código nuevos y E3 midió el muro" | **VÁLIDO solo para HeLL/LMAO**: la vía nativa no paga ese muro y emitió el bucle |

El bloqueante real que **sigue en pie** es el que ya estaba medido y no depende
de esto: el clasificador/despacho sobre el byte leído (frente 2 etapa 2 y la
pila de profundidad 2 del frente 3) necesita aritmética de estado, y de eso hay
prueba de no-existencia solo para dos operandos variables (`cmp2_two_operand_blocker.json`).

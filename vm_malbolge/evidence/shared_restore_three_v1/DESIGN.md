# Diseño: tercera invocación con CLOCK2 relocado

2026-11-12. Pack `shared_restore_three_v1`. Base medida: `shared_restore_two_v1`
@ `3947d79`.

## Bloqueo que forzó el relocation

En two_v1, `CLOCK2=58397` basta porque call2 es la última invocación y puede
HALTar en la cuarta visita al reloj. Para encadenar call3, call2 necesita el
mismo desvío Phase1→PCRAZY→REARM que call1. Pero:

```
crazy(ONE, 58396) = 58392
```

Eso deja solo 5 celdas antes de CLOCK2: no cabe el trineo REARM de 17 celdas.
Por eso CLOCK2 pasa a **58585**, donde `crazy(ONE, 58584) = 58338` y el sled
REARM2 vive en 58339..58355, lejos de ROT/MOVD/CRAZY/CLOCK.

## Layout

| Pieza | PC / celda | Rol |
| --- | --- | --- |
| Primitivas | 58057 / 58152 / 58268 | ROT / MOVD / CRAZY compartidas |
| CLOCK | 58303 | despacho call1 |
| REARM | 57565 | crazy final T1 + JMP STORE |
| STORE | 57700 | JMP → S2 |
| CLOCK2 | 58585 | despacho call2 |
| PCRAZY2 | 57704 (%94==82) | parchea T2+3 ← 58338 |
| REARM2 | 58339 | crazy final T2 + JMP STORE2 |
| STORE2 | 57720 | JMP → S3 |
| CLOCK3 | 58679 | despacho call3 → HALT |
| T1/T2/T3 | 57100 / 57300 / 57800 | objetivos 70→40 |

## Flujo

1. call1: divert T1+3 → REARM → STORE → S2
2. call2: divert T2+3 → REARM2 → STORE2 → S3
3. call3: isla simple; cuarta visita a CLOCK3 = HALT (op 81)

Control: C/C2/C3 plantan 117 en lugar de 120 → objetivos 39.

# Frente 5 — divergencia oráculo-vs-runner del lexer (P6)

## Reproducida: 4/4

Probe reconstruido (`byte_dispatch18.hell` con las 18 colas `OUT/HALT`
sustituidas por `OUT / R_MOVED / MOVED ENTRY`), ensamblado con el LMAO del repo:
**48.675 B**. Mismo binario, los dos motores:

| stdin | Oráculo Python | pasos | Runner C | Acuerdo |
|---|---|---|---|---|
| `01` | `302ceeffffffa6a602` | 59.902 | `30` (59.675 pasos) | **NO** |
| `01 02` | `302cee303030333302` | 59.902 | `30` | **NO** |
| `02` | `302ceeffffffa6a602` | 59.902 | `30` | **NO** |
| `01 02 03` | `302cee303030333302` | 59.902 | `30` | **NO** |

Esto confirma el síntoma documentado en `python/P6_STATUS.md` (2026-10-10):
**la divergencia es real y reproducible hoy**, no un artefacto de aquella sesión.

## Lo que está acotado

- **Ambos motores HALTED.** No es un bucle infinito ni un presupuesto agotado.
- **Diferencia de pasos: 227** (59.902 vs 59.675). Es decir, ejecutan prácticamente
  el mismo número de instrucciones y divergen solo al final.
- **El runner emite exactamente un byte** (`0x30`) y el oráculo nueve.
- **El segundo byte de entrada no produce el segundo marcador en ningún motor** —
  eso sigue siendo el fallo funcional del lexer, y es independiente de la
  divergencia.

## Lo que NO está averiguado

La causa exacta de la divergencia. Mi instrumento propio (reimplementación del
bucle del oráculo) no reprodujo la salida del oráculo oficial, así que **no**
puedo usarlo como testigo: la divergencia está medida, pero su mecanismo no.

Hipótesis sin verificar: diferencia en el tratamiento de EOF o en el cifrado
`xlat2` de la celda destino del salto. La divergencia aparece justo después del
primer `OUT`, que es donde el probe recién añadido encadena `R_MOVED` +
`MOVED ENTRY`.

## Estado del frente

Síntoma **reproducido y acotado** (4/4, mismo binario). Causa **no** averiguada.
No es un bloqueante para el roadmap del lexer: el fallo funcional (segundo
token) ya estaba documentado y sigue en pie.

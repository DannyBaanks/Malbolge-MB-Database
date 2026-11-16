# G5b O3: sitios de código por celda de datos (análisis en Zig)

2026-11-15. Base `7c10c4a`. Análisis **exploratorio, sin preregistro**: amplía la
adenda O3 de `g5b_crazy_mix_loop_v1/ATTEMPT01_OBSTRUCTION.md`. Implementación en
Zig 0.16.0 (`o3_sites.zig`) que lee `xlat1`/`xlat2` directamente del C del vendor
Olmstead: es una fuente independiente del Python del repo.

## Modelo

Una celda ejecutada en cada pasada recorre toda su órbita. Un sitio que lee `d`
en la celda `T` se alcanza tras un JMP que lee `T−δ_in` y continúa leyendo
`d` en `T+δ_out`; `δ_in−1` y `δ_out−1` son las celdas no-`d` ejecutables antes y
después del op. Dos sitios distintos sobre la misma `T` necesitan `δ_in` y
`δ_out` distintos. El máximo de sitios es un emparejamiento bipartito máximo.
**Estricto:** relleno = NOP persistente. **Laxo:** también celdas IN/OUT de un
solo activo (que disparan E/S en su pasada activa).

## Resultados (`o3_sites.stdout.raw.txt`)

| Medida | Estricto | Laxo |
| --- | --- | --- |
| Sitios por celda, cualquier op | 3 | 4 |
| Sitios por celda, mismo op (ROT / MOVD / CRAZY) | 2 / 2 / 2 | 3 / 3 / 3 |

Sitios con tramo no-`d` (estricto; residuo, órbita, antes, después): ROT `16(6),
28(4), 91(4)`; MOVD `9(4), 83(5), 93(5)`; CRAZY `11(5), 25(6), 36(6), 89(9)`.
Con periodo 2 (70↔74) el máximo es 1, que es la obstrucción O2.

**Paridad Zig ↔ Python:** coinciden los residuos persistentes, los residuos de
fase de periodo 2 de los cinco ops y los residuos con predecesor persistente de O3.

## Consecuencia para G5b-1a

- Un reinicio de celda exige dos CRAZY (`crazy(29524,j)` y luego `crazy(c,c)`).
  No hay reinicio de un paso: ninguna fila de `crazy` es constante y ROT tiene
  orden 10. Con el CRAZY de uso, una variable mutable necesita ≥3 sitios CRAZY
  sobre la misma celda, y el máximo estricto es 2. **Las órbitas largas no
  bastan para el estado mutable en modo estricto.**
- Las constantes invariantes (U=29524 bajo ROT, celdas V bajo `crazy(29524,·)`)
  sí se resuelven duplicando una celda por sitio.
- Quedan abiertos: el modo laxo (3 CRAZY por celda, si las IN/OUT del relleno
  son las del programa) y el coste de calendario (cada op dispara 1 de cada L
  visitas, con L ∈ {4,5,6,9}). Ninguno está medido sobre una imagen.
- Ruta recomendada: retorno calculado con celdas bandera MOVD↔NOP (mini-LMAO
  nativo), que no depende de este límite.

## Reproducción

```sh
zig build-exe vm_malbolge/evidence/g5b_o3_sites_v1/o3_sites.zig -O ReleaseSafe -femit-bin=<tmp>/o3_sites
<tmp>/o3_sites ../Malbolge-PureEpoch/vendor/olmstead_original.c
```

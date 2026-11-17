# G5b P2: cuatro llamadores secuenciales — resultado

Fecha: 2026-11-16. Resultado dentro del alcance: **PASS G0–G4 y REA**.

Una ejecución visitó la misma operación en `pc=38058` cuatro veces, siempre con `d=40006`, desde los llamadores `ll → lr → rl → rr`. Los retornos llegaron a `15000 → 15004 → 15008 → 15012`, y el flujo de salida fue `62e66ee6`.

| Medición | Resultado |
|---|---|
| Olmstead nativo | rc 0; salida `62e66ee6` |
| Trazador local | `halt`; 3756 pasos; cuatro llamadas y continuaciones previstas |
| `clasesbolge` | `end`; salida `62e66ee6` |
| REA (positivo) | HALTED; 3756 pasos; cuatro llamadas al sitio y bytes `[98,230,110,230]` |
| Flags y operación | `[74,74,74]` en cada continuación; operación compartida vuelve a 74 |
| JMP de retorno | sin cambios |
| Control: falta el ajuste de bandera raíz en `lr` | `15000 → 15012`, salida `62e6`, dos llamadas; el control detecta el fallo |
| REA (control) | HALTED; 3672 pasos; dos llamadas; bytes `[98,230]` |
| G4 | segunda generación positiva idéntica byte a byte (ver `hashes.sha256`) |

La variable de 16 bits tomó `12345 → 12130 → 21990 → 7534 → 21990`; los bytes emitidos fueron los valores bajos `62 e6 6e e6`.

## Límites

Se demuestra el orden fijo de cuatro llamadores, una variable compartida, un sitio de operación y el control de una mutación de una bandera. No se demuestra una convención general para un número arbitrario de llamadores, varias variables, entrada/EOF ni rutinas recursivas.

## Reproducción

Consulta [GATES.md](GATES.md). Las imágenes, respuestas estructuradas, logs nativos y referencias REA quedan junto a este veredicto; `hashes.sha256` fija sus bytes.

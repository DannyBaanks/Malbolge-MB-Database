# G5b P3: orden cruzado de cuatro llamadores — resultado

Fecha: 2026-11-16. Resultado dentro del alcance: **PASS G0–G4 y REA**.

La imagen positiva recorrió `rr → ll → rl → lr`, compartiendo una operación en `pc=38058` y una variable en `d=40006`. Las cuatro llamadas transformaron el valor `12345 → 12130 → 21990 → 7534 → 21990`; la salida fue `62e66ee6`. Las continuaciones fueron `15000 → 15004 → 15008 → 15012`.

| Medición | Resultado |
|---|---|
| Imagen Classic | 39 932 bytes; cargador válido; SHA-256 `5c72beaf362d783f7846cd74463cf729786a1c9c0bfc9e0ea9a6f36a91913d72` |
| Olmstead nativo | rc 0; salida `62e66ee6` |
| Trazador local | `halt`; 4014 pasos; cuatro llamadas; un sitio y una variable |
| `clasesbolge` | `end`; salida `62e66ee6` |
| REA positivo | HALTED; 4014 pasos; eventos completos; cuatro llamadas al sitio y salida `[98,230,110,230]` |
| Flags y operación | `[74,74,74]` en cada continuación; la operación compartida vuelve a 74 |
| JMP de retorno | sin cambios |
| Control negativo | El `rr` inicial ajusta `f_root` de más; una llamada, continuación terminal `15012`, salida `62`, HALT |
| REA control | HALTED; 3944 pasos; eventos completos; una llamada; salida `[98]` |
| G4 | segunda generación positiva idéntica byte por byte; SHA-256 `5c72beaf362d783f7846cd74463cf729786a1c9c0bfc9e0ea9a6f36a91913d72` |

## Límites

P3 demuestra este orden alternativo específico con cuatro llamadores, una variable y un sitio compartido. No demuestra las otras 23 permutaciones, un número arbitrario de llamadores, variables múltiples, entrada/EOF ni llamadas recursivas.

## Evidencia y reproducción

Consulta [GATES.md](GATES.md), [REA.md](REA.md), [manifest.json](manifest.json) y [hashes.sha256](hashes.sha256). Las imágenes, JSON de ejecución y flujos nativos están guardados en `run01/` y `run02/`. La receta de reproducción usa rutas relativas al repositorio y un `RUN_ROOT` temporal.

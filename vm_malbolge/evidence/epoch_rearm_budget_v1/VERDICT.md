# epoch_rearm_budget_v1 — ¿alcanza restaurar el resolvedor para una segunda petición?

Autor: claude_code_a029a379be0f4681, 2026-11-11. Puertas pre-registradas en
`GATES.md` (commit `4a5b0b0`, anterior a `probe.py`). Dialecto: Classic permisivo
(el resolvedor no carga en Olmstead 1998, `epoch_audit_v1` H3).

## Resultado

**`BLOCKED(REGRESS)` en las 7 instancias.** Volver a dejar la memoria del
resolvedor como en la imagen, con los mecanismos ya demostrados (carga con `ROT` o
`ROT` + `CRAZY`, restore con un `CRAZY`, rearm a 29524), exige un código restaurador
de **al menos 17 130 instrucciones** para un cuerpo de **218 celdas**. El
restaurador también se cifra al ejecutarse, así que la vía "restaurar el cuerpo"
no cierra: el problema crece en cada vuelta en vez de reducirse.

El bloqueo no depende de la cota de direccionamiento. Aun ignorando por completo
el coste de llevar `d` a las celdas altas, la carga + restore sola cuesta **2268
instrucciones** (más de 10 veces el cuerpo); el mínimo medido por celda es 3
instrucciones (rango 3..16).

Además hay un argumento estructural, independiente del modelo de carga: cada celda
restaurada necesita al menos un `CRAZY` sobre ella, y cada instrucción del
restaurador que no sea `JMP` ni `END` queda a su vez cifrada. Un restaurador que
también tuviera que restaurarse a sí mismo necesitaría `R ≥ B + R`, que no tiene
solución. Las únicas salidas son celdas que no se cifran (`JMP`, `END`) o celdas que
vuelven solas a su valor (ciclos de XLAT2, Q6).

## Números (instancia `e100_p29797`; las 7 en `results.json`)

| medición | valor |
|---|---|
| G0: trazador del pack vs intérprete independiente | 7/7 coinciden (salida, pasos, estado) |
| Q1 cuerpo (celdas de código distintas ejecutadas) | 218, rango 0..339, 0 ejecutadas dos veces |
| Q1 estado sucio | 225 celdas: 215 de código + 10 de dato |
| celdas del cuerpo que no quedan sucias | 3: dos `JMP` (2 y 339, el `JMP` cifra la celda destino) y el `END` (101) |
| palabras alcanzables en `a` (ROT o ROT + CRAZY) | 8281 de 59049 |
| Q2 vía A (un CRAZY) / vía B (dos pasos) / sin vía | 77 / 148 / **0** |
| Q2 coste por celda | 3..16 instrucciones |
| Q3 carga + restore | 2276 instrucciones; 366 celdas auxiliares consumidas |
| Q4 celdas sucias por encima de 127 | 211 |
| Q4 direccionamiento (cota inferior) | 14 862 instrucciones |
| Q5 restaurador (cota inferior) vs cuerpo | 17 138 vs 218 → `REGRESS` |
| G3 control (b = 50, fuera del veredicto) | cuerpo 237, sucias 245, restaurador ≥ 17 263 |

Toda celda sucia **sí** se puede restaurar (0 sin vía): el bloqueo no es de
restaurabilidad ni de memoria (17 138 + 366 ≪ 59 049), sino de tamaño relativo.

## Q6: la salida está en los ciclos de XLAT2

La permutación XLAT2 sobre 33..126 tiene exactamente **un ciclo de cada longitud
2, 4, 5, 6, 9 y 68** (2 + 4 + 5 + 6 + 9 + 68 = 94). El cuerpo del resolvedor usa
valores de los seis ciclos, así que tardaría **mcm = 3060** ejecuciones en volver
solo a su estado inicial, y en las intermedias ejecutaría opcodes distintos.

Eso apunta a la alternativa: no restaurar el código, sino **diseñar el cuerpo del
bucle con celdas de ciclos cortos** (el ciclo de longitud 2 vuelve a su valor cada
dos ejecuciones). Es la vía que usa PureEpoch, cuyo Boss 3 (`while x > 0` con PC
repetido) sí corre en el intérprete de Olmstead de 1998 (comprobado en la sesión de
`epoch_audit_v1`).

## Lo que este pack NO demuestra

- **NOT_DEMONSTRATED**: un bucle construido; este pack sólo mide.
- **NOT_DEMONSTRATED**: el rutado completo de `d`. Q4 es una cota inferior por celda
  (caminar `d` desde 127, o escribir una palabra-puntero en runtime, lo que cueste
  menos). El veredicto no depende de Q4.
- **NOT_DEMONSTRATED**: que un resolvedor de épocas rediseñado sobre ciclos XLAT2
  cortos sea construible. Q6 sólo mide la estructura de ciclos.
- El modelo de carga se limita a `ROT` y `ROT` + un `CRAZY` desde celdas sembradas.
  Cargas más largas alcanzarían más palabras y podrían cambiar los costes por
  celda, pero no el argumento estructural (al menos un `CRAZY` por celda
  restaurada, y el restaurador también se cifra).

## Reproducción

```
cd vm_malbolge/evidence/epoch_rearm_budget_v1
python3 -I probe.py </dev/null      # exit 0; escribe results.json
sha256sum -c SHA256SUMS.txt
```

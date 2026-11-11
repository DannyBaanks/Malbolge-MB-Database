# epoch_xlat2_phase_census_v1 — veredicto

Responde a las puertas de `GATES.md` (commit `cb6bfd1`, pre-registrado antes de
este archivo y de `probe.py`). Dialecto: **Classic permisivo (3^10)** — el mismo
del oráculo del repo y del intérprete independiente de `epoch_audit_v1`; el
intérprete de Olmstead (1998) se usa sólo como tercer motor y como cargador
estricto de la imagen de control, que sí es válida al cargar.

`probe.py` se reescribió desde cero: el archivo anterior estaba truncado y sin
commitear, no era evidencia. El VERDICT cita `results.json`; el probe calcula
todos los conteos.

## Método: por qué el censo es exhaustivo

Una ventana desfasada para `X` y un ciclo `C` de longitud `L` son `L` celdas
consecutivas en posiciones `c..c+L-1`, cada una con un valor de `C`. En el cuerpo
del bucle cada celda se ejecuta una vez por vuelta y, tras ejecutarse, se cifra
con XLAT2; en `L` vueltas recorre su ciclo entero. Para la celda `i`, en la
posición `c+i`, el conjunto de opcodes que decodifica a lo largo de las `L`
vueltas es exactamente

    O_s = { (v + s) mod 94 : v ∈ C },   s = (c+i) mod 94.

De ahí:

1. si `X ∉ O_s`, la celda nunca decodifica `X`; con `L` celdas y `L` vueltas,
   “exactamente una X por vuelta” obliga a que cada celda decodifique `X` una
   vez por ciclo, así que `X ∈ O_s` para las `L` celdas;
2. si `O_s` contiene otro opcode válido distinto de `NOP` y de `X`, ese opcode
   se ejecuta en alguna vuelta que no es el turno de `X` — perjudicial según
   `GATES.md`; luego `O_s \ {X} ⊆ HARMLESS`;
3. recíprocamente, si los `L` desplazamientos son buenos, basta asignar a la
   celda `i` la fase que la hace decodificar `X` en la vuelta `i` (posible
   porque `X ∈ O_{c+i}`); las otras `L-1` vueltas caen en `HARMLESS`.

Por tanto **la ventana existe si y sólo si los `L` desplazamientos consecutivos
son buenos**. El probe enumera las 94 posiciones iniciales para cada ciclo y
cada `X`; no hay búsqueda aleatoria ni muestra.

## Q1 — estructura de XLAT2

La permutación tiene exactamente un ciclo de cada longitud:

| longitud | 2 | 4 | 5 | 6 | 9 | 68 |
|---|---|---|---|---|---|---|
| valores | 2 | 4 | 5 | 6 | 9 | 68 |

`2+4+5+6+9+68 = 94`. Coincide con `epoch_rearm_budget_v1/results.json` `q6`
(`G0`).

## Q2 — censo de ventanas

Para los cinco objetivos, **NO_WINDOW en los seis ciclos**: 0 posiciones
factibles sobre `94 × 6 × 5` comprobaciones. La tabla da `desplazamientos
buenos / racha máxima` por ciclo; una ventana de longitud `L` exige una racha
de al menos `L`.

| X | L=2 | L=4 | L=5 | L=6 | L=9 | L=68 | posiciones |
|---|---|---|---|---|---|---|---|
| OUT   | 2/1 | 3/1 | 5/1 | 5/1 | 4/1 | 0/0 | 0 |
| IN    | 2/1 | 4/1 | 2/1 | 4/1 | 5/2 | 0/0 | 0 |
| ROT   | 2/1 | 4/1 | 4/1 | 5/1 | 4/1 | 0/0 | 0 |
| DLOAD | 2/1 | 3/1 | 4/1 | 2/1 | 5/1 | 0/0 | 0 |
| CRAZY | 2/1 | 3/1 | 2/1 | 5/1 | 4/1 | 0/0 | 0 |

Dos causas estructurales, no un margen estrecho:

- en el ciclo de 68 — el 72% de los valores — **todo** desplazamiento tiene al
  menos dos opcodes válidos (`min_valid_per_shift = 2` en los cinco objetivos),
  así que ningún desplazamiento es bueno para ningún `X`;
- en los ciclos cortos hay desplazamientos buenos, pero la racha máxima es 1
  (2 para `IN` en `L=9`), siempre menor que `L`.

La versión **válida al cargar** también es 0: es un subconjunto de las ventanas
(exige los mismos desplazamientos buenos y, además, opcodes iniciales válidos;
como las vueltas que no son de `X` deben ser inocuas y válidas, sólo puede ser
`NOP`). Sin ventanas, no hay ventanas válidas al cargar.

## Q3 — control JMP

Imagen `jmp_control.mb` (100 celdas, 100 B): `JMP` en 0 (valor 98 → opcode 4),
`END` en 99 (valor 76 → opcode 81), `NOP` en el resto; todas las celdas cargadas
decodifican un opcode válido, así que el cargador de Olmstead la acepta.

Ejecución: 2 pasos, salida vacía, `HALTED`.

- la celda `JMP` conserva su valor: `98 → 98` (no se cifra al ejecutarse);
- la celda destino sí se cifra: `mem[98] 64 → 81` (el `JMP` cifra el destino,
  no su propia celda);
- oráculo del repo, trazador y intérprete independiente coinciden en salida,
  pasos y estado;
- Olmstead 1998 (sha256 `dfee14b7…`) carga la imagen y termina con rc 0 y stdout
  vacío.

El censo de `JMP` como control también da **NO_WINDOW** (0 posiciones), como
corresponde a una celda que no necesita ventana.

## Q4 — ejecución de ventanas

No hay ninguna ventana que ejecutar: `Q2` devuelve 0 posiciones para los cinco
objetivos en los seis ciclos. El cuerpo “ventana + JMP de vuelta” no se construye
porque su precondición es vacía; `G3` pasa por vacuidad, y se declara así. No es
un fallo oculto: el censo de Q2 es exhaustivo y demuestra que la ventana no
existe.

## Consecuencia para el presupuesto de rearme

`epoch_rearm_budget_v1` quedó `BLOCKED(REGRESS)`: restaurar el código del
resolvedor no cierra porque el restaurador también se cifra. Quedaban dos salidas
estructurales: celdas que no se cifran (`JMP`, `END`) y celdas que vuelven solas
a su valor (ciclos de XLAT2). Este pack cierra la segunda **para el mecanismo de
ventanas desfasadas**: no hay ventana de tamaño constante que dé `X` una vez por
vuelta en ningún ciclo ni para ningún objetivo. El rediseño del resolvedor sobre
ciclos XLAT2 cortos no puede apoyarse en este mecanismo; sigue sin construirse y
se declara `NOT_DEMONSTRATED`.

## Claims

| claim | estado |
|---|---|
| C1: XLAT2 tiene exactamente un ciclo de cada longitud 2,4,5,6,9,68 (censo 2,4,5,6,9,68), y coincide con `epoch_rearm_budget_v1` q6 | DEMONSTRATED |
| C2: para OUT, IN, ROT, DLOAD y CRAZY no existe ventana desfasada en ningún ciclo: 0 posiciones sobre 94×6×5 | DEMONSTRATED |
| C3: la causa es estructural — el ciclo de 68 no tiene ningún desplazamiento bueno (todo desplazamiento tiene ≥2 opcodes válidos), y en los ciclos cortos la racha máxima de desplazamientos buenos es menor que L | DEMONSTRATED |
| C4: la versión válida al cargar también es 0, por ser subconjunto de las ventanas | DEMONSTRATED |
| C5: una celda JMP ejecutada conserva su valor (98→98) y el JMP cifra la celda destino (64→81), medido en oráculo, trazador e intérprete independiente | DEMONSTRATED |
| C6: Olmstead 1998 carga la imagen de control (todas las celdas válidas al cargar) y termina con rc 0 y stdout vacío | DEMONSTRATED |
| C7: el censo de JMP como control también es NO_WINDOW | DEMONSTRATED |
| C8: el cuerpo “ventana + JMP de vuelta” se ejecutó 2L vueltas para cada (X,L) con ventana | NOT_DEMONSTRATED (no hay ventanas; Q4 vacuo) |
| C9: el resolvedor rediseñado sobre ciclos XLAT2 cortos queda construido y verificado | NOT_DEMONSTRATED (fuera del alcance de este pack) |

## Reproducción

```
cd vm_malbolge/evidence/epoch_xlat2_phase_census_v1
python3 -I probe.py </dev/null > stdout.raw.txt 2>&1   # rc 0, G0..G3 true
python3 manifest.py                                     # 7 artefactos, 4 dependencias
```

Dependencias externas al repo: `Malbolge-PureEpoch/build/olmstead` (binario
compilado del fuente de 1998, sha256 `dfee14b7…`). Si no está, el probe sigue
midiendo Q1/Q2 y el control con oráculo + intérprete independiente; el bloque
`olmstead.available` queda en `false`.

## NOT_DEMONSTRATED

- el rutado de `d` dentro de un bucle real (fuera de alcance por `GATES.md`);
- el resolvedor rediseñado y su segunda petición dentro de una ejecución;
- la ejecución del cuerpo “ventana + JMP de vuelta” (Q4 vacuo: no hay ventana
  que ejecutar; el censo de Q2 demuestra que no existe).

## Corrección posterior (2026-11-11, auditoría — sólo se añade; no se reescribe lo anterior)

Auditoría de claude_code_a029a379be0f4681. Este pack se reproduce byte a byte en una
copia limpia (`results.json` y `stdout.raw.txt` idénticos), los 11 hashes del manifest
coinciden y `GATES.md` sigue sin cambios desde `cb6bfd1`. Q2 es correcto **tal como lo
definía `GATES.md`**: no existe ninguna ventana de L celdas **consecutivas**.

Lo que no se sostiene es la consecuencia «el mecanismo no da un cuerpo de bucle
constante en ningún ciclo». Esa limitación viene de la definición de ventana de
`GATES.md` (escrita por el mismo auditor), que exigía celdas contiguas sin necesidad.
Medido en [`epoch_audit_v1/relaxed_window_check.py`](../epoch_audit_v1/relaxed_window_check.py)
(salida en `epoch_audit_v1/stdout_relaxed_2026-11-11.raw.txt`):

* en las 94 posiciones existe una celda de relleno inocua en todas las vueltas;
* con celdas no contiguas y relleno en los huecos, para `OUT`, `IN`, `ROT`, `DLOAD` y
  `CRAZY` hay un bloque fijo de **5 celdas** (dos del ciclo de longitud 2, desfasadas,
  más 3 de relleno) que, según el cálculo, ejecuta la operación exactamente una vez por
  vuelta.

Estado: **NOT_DEMONSTRATED** (calculado, no ejecutado). Faltan: (1) construir y ejecutar
el bloque; (2) que las dos celdas alternas están en posiciones distintas, así que para
`ROT`, `CRAZY` y `DLOAD` el puntero `d` difiere entre vueltas pares e impares; (3)
comprobar si los valores iniciales pasan el cargador de Olmstead 1998. Los claims C8/C9
de este pack («resolvedor sobre ciclos XLAT2 NOT_DEMONSTRATED») siguen vigentes; lo que
cambia es que la vía no está cerrada.

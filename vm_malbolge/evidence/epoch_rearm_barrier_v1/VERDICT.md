# epoch_rearm_barrier_v1 — qué se puede rearmar en Classic y qué no

## Pregunta y resultado

H1: en Malbolge Classic, una celda de **código** que ya se ejecutó puede
re-ejecutarse (restaurando su contenido exacto) y, con ello, un programa puede
atender una **segunda** petición en la misma ejecución. H0: la restauración no
se puede hacer o el salto de retorno no alcanza el cuerpo del programa.

**PASS parcial, con la causa medida.** El pack no construye el bucle: mide las
condiciones que tendría que cumplir y las acota con números. Lo que queda
**DEMONSTRADO** es la vía de datos y lo que queda **acotado** es la de código:

| # | Medición | Resultado medido |
|---|---|---|
| M1 | el cifrado posterior a la ejecución se deshace con `ROT` | **0** de 2400 pares (opcode, celda) |
| M2 | se deshace con **un** `CRAZY` (si existe palabra de control) | **839** de 2400 (35%); 290 de 300 celdas tienen ≥1 opcode restaurable |
| M3 | esa palabra de control se puede materializar desde una celda sembrada | 0 imprimibles; **26** en una órbita de rotación imprimible — y la palabra es siempre la misma: **29403** |
| M4 | vía de dos pasos (rearm a 29524 + escritura exacta) | **34** de 3200 pares (opcode, celda), en 34 celdas |
| M5 | rearm de una celda de **dato** | **universal y exacto**: 0 discrepancias sobre las 59049 palabras |
| M6 | papel de la celda sucesora (cadena del puntero + opcode) | per-época y forzado; la cadena sigue siendo compatible con el papel de `JMP` de retorno |
| M7 | alcance del salto de retorno | celda sembrada: sólo 34..127; con la palabra exacta escrita en runtime: 36 destinos en 35..3999 (el mayor, 3767) |
| M8 | capacidad de la zona de dato (86 celdas) frente al diario (1 celda por celda de código re-ejecutada, cuerpo ≈ 200 celdas) | **no cabe** |

## El mecanismo, parte por parte

### Por qué `ROT` no sirve (M1)

Toda celda de código queda cifrada tras su ejecución: `mem[c] = _ENC[mem[c]]`
(la tabla XLAT2). `ROT` cumple `rot^10 = identidad`, luego deshacer el cifrado
con rotaciones exigiría `rot^k(_ENC[v]) = v` para algún `k`. Medido sobre las
2400 combinaciones (opcode, celda) válidas de las celdas 0..299: **ninguna** lo
cumple. El marco de rotación y el cifrado XLAT2 son transformaciones
incompatibles.

### Por qué un `CRAZY` sí deshace el cifrado (M2, M3)

`crazy(a, celda) = TBL[celda_d][a_d]` por trit. Para restaurar `v` sobre `w`
hace falta, por trit, un `a_d` con `TBL[w_d][a_d] = v_d`. La tabla
`TBL[0] = (1,0,0)` no alcanza el valor 2, así que **no** hay solución cuando
`w_d = 0` y `v_d = 2`. Medido: eso deja fuera a 1551 de los 2400 pares, o sea
**839 pares sí se restauran** con un único `CRAZY`, y 290 de las 300 celdas
tienen al menos un opcode restaurable.

El problema no es la operación sino la **palabra de control**: para que el
acumulador reciba una palabra concreta hace falta una celda sembrada
(imprimible) de la que cargarla con un `ROT`, y el `ROT` sólo barre la órbita de
rotación de la palabra sembrada (10 elementos de 59049). Medido: **ninguna** de
las 839 palabras de control es imprimible, pero **26** de ellas están en una
órbita que contiene una palabra imprimible — y las 26 son la misma palabra,
**29403**. Ése es el resultado que abre la puerta: la restauración de un
`CRAZY` es materializable en 26 celdas concretas, con una única constante.

### La vía de dos pasos (M4) y su tabla de posiciones

`epoch_rearm_primitive_v1` da la restauración en dos pasos:

    celda <- crazy(29524, celda) = extract2(celda)
    celda <- crazy(E, E)        = 29524        (E = extract2(celda))
    celda <- crazy(swap01(v), 29524) = v       (escritura exacta del valor original)

El tercer paso necesita `a = swap01(v)`, y `v` es el valor original de la celda
(imprimible, sembrable). Para cargarlo con un `ROT` hace falta que
`swap01(v)` esté en la órbita de rotación de `v`: medido, eso ocurre en **34 de
los 3200** pares (opcode, celda) de las celdas 0..399, en 34 celdas distintas.
El artefacto de este pack es esa **tabla de posiciones** (`position_table.json`):
dice qué celdas admiten qué opcode re-ejecutable, y con qué constante. Un
planificador de un bucle tendría que colocar su cuerpo en esas celdas.

### El rearm de los datos es universal (M5)

Aquí no hay ninguna restricción: `crazy(29524, X) = extract2(X)` y
`crazy(E, E) = 29524` valen para **las 59049 palabras**, 0 discrepancias. Es
decir: la celda de época que consume un payload se puede devolver a su máscara
`29524` **exactamente**, siempre. La compatibilidad con el puntero es lo único
que hay que resolver (el rearm necesita volver a `d = T`, y el puntero ya sabe
hacerlo: `DLOAD` lee `mem[W] = b` y el incremento automático lleva `d` a `T`).

### La celda sucesora puede ser el salto de retorno (M6)

Tras ejecutar el payload, el PC cae en `T+1`. Si esa celda debe devolver al
programa, su valor queda forzado a `v = (4 - (T+1)) mod 94` (opcode `JMP`):
para T = 100, 106 y 112 son 91, 85 y 79 — tres valores distintos, porque las
tres épocas no comparten residuo. Eso no rompe la cadena del puntero: la cadena
usa `mem[T+1] = v` para saltar a `v+1`, y `v+1` (92, 86, 80) cae en la zona de
dato y está libre. El papel de la celda sucesora es, por tanto, per-época y
compilable, no un obstáculo.

### El salto de retorno no llega con una celda sembrada (M7)

El `JMP` lee `c = mem[d]` y continúa en `c+1`. El destino del salto de retorno
tiene que estar en una celda que contenga `destino-1`. Una celda sembrada es
imprimible (33..126), luego con ella **sólo se alcanzan destinos 34..127** — y
la imagen actual mide 340 bytes, así que el cuerpo del programa (que vive por
encima de 127) queda fuera de alcance. Por encima hace falta **escribir la
palabra exacta en runtime**: la condición `swap01(destino-1)` en una órbita
imprimible se cumple en **36 destinos** entre 35 y 3999 (122, 364, 365, 608,
851, 1090…), o sea hay destinos utilizables muy por encima del tamaño actual de
la imagen — pero con una densidad de ~1 por cada 100 direcciones, y ese destino
es una propiedad del **programa**, no de la petición.

### El diario no cabe en la zona de dato (M8)

Re-ejecutar una celda de código exige su valor original; la vía de un `CRAZY`
no necesita diario (la palabra de control es una constante), pero la vía de dos
pasos sí necesita una celda de diario por celda re-ejecutable. La zona de dato
tiene 86 celdas y el cuerpo del bucle actual ronda las 200.

## Conclusión

La barrera del frente «rearm para una segunda petición en la misma ejecución»
**no** está en el rearm del dato (es universal y exacto, M5) ni en el puntero
(ya funciona, `epoch_resolver_epoch_select_v1`), sino en tres condiciones
concretas y medibles:

1. las celdas de código que el bucle re-ejecute tienen que vivir en la tabla de
   posiciones (M4: 34 celdas de 400) o usar la palabra de control 29403 (M3: 26
   celdas de 300);
2. el salto de retorno tiene que apuntar a un destino alcanzable: por encima
   de 127 eso exige escribir la palabra exacta en runtime (M7);
3. el cuerpo del bucle tiene que caber en la zona de dato si usa la vía de dos
   pasos (M8: no cabe el actual).

Con esas tres condiciones medidas, el siguiente paso es un planificador que
respete la tabla de posiciones: ése es el trabajo que queda, y este pack deja la
tabla y las constantes exactas para hacerlo.

## Lo que este pack NO demuestra

- **NOT_DEMONSTRATED**: un bucle que atienda una segunda petición. Este pack
  mide sus condiciones, no lo construye.
- **NOT_DEMONSTRATED**: que las 26 celdas de M3 y las 34 de M4 basten juntas
  para alojar un cuerpo de bucle real (el cuerpo actual ronda las 200 celdas y
  las tablas dan 26 y 34 posiciones utilizables).
- **NOT_DEMONSTRATED**: el rearm de la celda de época *dentro* de un programa
  completo. La operación está medida (M5, exhaustiva) y el puntero que la
  alcanza está medido (`epoch_resolver_epoch_select_v1`), pero la composición
  de ambas no está construida.

## Reproducción

```
cd vm_malbolge/evidence/epoch_rearm_barrier_v1
python3 build.py .          # escribe position_table.json
python3 probe.py            # exit 0; escribe results.json
python3 manifest.py         # regenera manifest.json
```

## Corrección posterior (2026-11-10, auditoría — sólo se añade; no se reescribe lo anterior)

Auditoría independiente en [`epoch_audit_v1/AUDIT.md`](../epoch_audit_v1/AUDIT.md).
La reproducción y los hashes son correctos y M1, M2, M3 (26), M4 (34) y el alcance
sembrado de M7 se reproducen. Hay que corregir el alcance de estas afirmaciones:

* **M3/M4 no son una barrera de Classic.** Valen para el modelo en el que la palabra
  se carga con **un** `ROT` desde una celda sembrada. Con un `CRAZY` de
  preparación (`a = crazy(x, y)` con `x` e `y` en órbitas imprimibles) la palabra de
  control es materializable en 839/839 pares y `swap01(v)` en 3200/3200. La tabla
  de posiciones no restringe a un planificador; el coste de esa vía queda
  `NOT_DEMONSTRATED`.
* **M8 no es una medición**: el cuerpo de 200 celdas y `capacity_sufficient=False`
  están escritos a mano en `probe.py`. Pasa a `NOT_DEMONSTRATED`.
* Los docstrings de `probe.py` y `build.py` (65%, "0 en órbita imprimible", 452
  direcciones) no coinciden con lo medido (35%, 26, 36). Los números válidos son
  los de `stdout.raw.txt`.
* La "palabra de control única 29403" depende de tomar la primera solución: hay 4
  palabras posibles. El 26 se mantiene.

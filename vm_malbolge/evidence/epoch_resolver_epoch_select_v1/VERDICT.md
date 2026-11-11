# epoch_resolver_epoch_select_v1 — la petición elige la ÉPOCA y el PAYLOAD

## Hipótesis y resultado

H1: en una única VM Classic, una petición recibida por `stdin` durante la
ejecución puede elegir **a la vez** (a) la celda de época donde se ejecuta el
programa y (b) el payload de 10 trits que se ejecuta en ella, con **una sola
imagen** y sin ramas por valor. H0: alguna de las dos propiedades falla.

**PASS.** Con una imagen fija de 340 bytes, las 7 instancias escriben el payload
exacto en la celda de época seleccionada y lo ejecutan allí (OUT = V % 256 en
pc = T), con la celda de época elegida por el byte de la petición y no por el
programa. Cuatro motores independientes coinciden: trazador del repo, trazador de
`native_classic`, oráculo del repo y el runner C original (el runner C se detiene
en la guarda de imprimibilidad cuando el payload no es imprimible, exactamente en
el paso predicho por la traza del oráculo — ver `c_printable_guard_v1`).

La celda sucesora de la época es la misma del pack anterior
(`epoch_resolver_request_v1`, T = 100, sucesora 101 = 74). Lo nuevo es que el
programa ya no decide T: lo decide la petición.

## El mecanismo

La petición son **21 bytes**:

    byte 0       : b, el byte de época. La celda de época es T = b + 1.
    bytes 1..10  : 2 si el trit p del payload es 1, si no 0   -> control de P
    bytes 11..20 : 2 si el trit p del payload no es 0, si no 0 -> control de M

El puntero (`W` = celda 52) es el de `epoch_algebra_v3`, pero con la máscara
`29524` (no imprimible) en vez de `121`:

| # | instrucción | efecto | `d` después |
|---|---|---|---|
| 1 | `IN` | `a = b` | — |
| 2 | `CRAZY` (A1) | `A1 = crazy(b, 29524) = swap01(b)` | 49 |
| 3 | `CRAZY` (W) | `W = crazy(swap01(b), 29524) = b` **exacto** | 53 |
| 4 | `DLOAD` | `d = mem[W] = b` | `b+1 = T` |
| 5 | `CRAZY` (T) | `T = crazy(swap01(V), 29524) = V` **exacto** | `T+1` |
| 6 | `DLOAD` | `d = mem[T+1] = v` | `v+1` |
| 7 | `DLOAD` | `d = mem[v+1] = W-1 = 51` | `W = 52` |
| 8 | `JMP` | `c = mem[W] = b` -> ejecución en `b+1 = T` | 53 |

El paso 4 es el truco: el `DLOAD` deja `d = b` y el incremento automático de `d`
lo lleva a `b+1 = T`, de modo que el `CRAZY` siguiente escribe **justo** en la
celda de época sin ninguna comparación por valor.

La celda sucesora `T+1` hace dos papeles a la vez:

1. su valor `v` cumple `(v + T+1) % 94 = 81`, o sea decodifica **END** cuando el
   PC llega a ella tras ejecutar el payload;
2. `v+1` es una celda que contiene `W-1 = 51`, de modo que la cadena
   `DLOAD -> DLOAD` (pasos 6-7) devuelve el puntero a `W` sin ramas.

La cadena de instrucciones es **idéntica** en las tres épocas: sólo cambian los
valores de las celdas de dato.

### Tabla de épocas

| T | b = T-1 | sucesora | valor v | celda v+1 | ¿END? | ¿cadena a W? |
|---:|---:|---:|---:|---:|:---:|:---:|
| 100 | 99 | 101 | 74 | 75 | sí | sí |
| 106 | 105 | 107 | 68 | 69 | sí | sí |
| 112 | 111 | 113 | 62 | 63 | sí | sí |

Las épocas **no** comparten residuo (100 ≡ 6, 106 ≡ 12, 112 ≡ 18 módulo 94).
En `epoch_algebra_v3` las tres estaban alineadas a 94 porque el valor de la
sucesora tenía que servir a la vez de END y de trampolín a `W`: eso imponía
`T ≡ 81 - W (mod 94)` y, con la máscara imprimible `121`, las épocas quedaban en
{36, 130, 224}. Aquí la máscara `29524` no es imprimible, así que la celda de
época hay que fabricarla en runtime y debe quedar en la zona de dato alcanzable
por saltos imprimibles (`34 <= T <= 126`). En ese rango caben épocas de residuos
distintos, y cada una necesita su propio valor de sucesor `v ≡ 80 - T (mod 94)`.
La cadena de dos `DLOAD` es lo que rompe el acoplamiento.

## Medición por instancia

Las 7 instancias comparten la **misma imagen** (`resolver_epoch.mb`, 340 bytes,
sha256 `41cdbc79…`); lo único que cambia es la petición.

| instancia | época T | b | payload V | P | M | payload escrito | OUT | pc | END | pasos | C (pasos) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| e100_p93 | 100 | 99 | 93 | 29617 | 29617 | 93 ✓ | `5d` | 100 | 101 | 218 | 218 (completo) |
| e100_p281 | 100 | 99 | 281 | 29803 | 29804 | 281 ✓ | `19` | 100 | 101 | 218 | 217 (guarda) |
| e100_p29797 | 100 | 99 | 29797 | 58775 | 59048 | 29797 ✓ | `65` | 100 | 101 | 218 | 217 (guarda) |
| e106_p275 | 106 | 105 | 275 | 29797 | 29798 | 275 ✓ | `13` | 106 | 107 | 218 | 217 (guarda) |
| e106_p29791 | 106 | 105 | 29791 | 58775 | 59045 | 29791 ✓ | `5f` | 106 | 107 | 218 | 217 (guarda) |
| e112_p269 | 112 | 111 | 269 | 29767 | 29780 | 269 ✓ | `0d` | 112 | 113 | 218 | 217 (guarda) |
| e112_p29785 | 112 | 111 | 29785 | 58769 | 59039 | 29785 ✓ | `59` | 112 | 113 | 218 | 217 (guarda) |

En las 7 instancias: los 21 bytes se leen **en orden**, `W` contiene el byte de
época **exacto**, `P` y `M` quedan exactos, el payload se escribe **exacto** en
la celda de época elegida, **las otras dos celdas de época siguen con la máscara
29524** (el payload no se derrama), el `OUT` se emite en `pc = T` y el programa
termina con `END` en `T+1`.

El runner C coincide byte a byte con el oráculo cuando el payload es imprimible
(e100_p93: 218 pasos, salida `5d`); con payloads no imprimibles se detiene en la
guarda de imprimibilidad en el paso 217, **exactamente** el paso que predice la
traza del oráculo (`c_printable_guard_v1`).

## La época y el payload están acoplados (medido)

El opcode de una palabra en una celda es `(V + T) % 94`. Como `T` lo elige la
petición, **la misma palabra no es el mismo opcode en otra época**:

| payload | @100 | @106 | @112 |
|---|---:|---:|---:|
| 93 / 281 / 29797 | **5** (OUT) | 11 | 17 |
| 275 / 29791 | 93 | **5** (OUT) | 11 |
| 269 / 29785 | 87 | 93 | **5** (OUT) |

Los opcodes 11, 17, 87 y 93 no son opcodes válidos de Classic: en el oráculo son
instrucciones sin efecto (`else: pass`), así que el programa sigue a la celda
sucesora y termina con `END` **sin emitir nada**. Es decir: un payload elegido
para una época no es "transportable" a otra — la pareja (época, payload) es lo
que la petición elige, y por eso la interfaz honesta es la de 21 bytes y no la
de "payload fijo + época variable".

## Controles negativos

| control | mutación | resultado medido |
|---|---|---|
| A | **sólo** el byte de época (99 -> 105) | el payload 29797 se escribe en 106 (no en 100, que sigue con la máscara 29524); el opcode en 106 pasa a 11 y **no** se emite OUT; estado HALTED |
| B | **sólo** un dígito de control (byte 1) | el payload pasa de 29797 a 29798 **en la misma época** (100); estado HALTED |
| C | byte de época fuera de catálogo (50) | el payload **no** aterriza en ninguna celda de época (medido, lista vacía); el programa termina HALTED en 237 pasos |

El control C no tiene puerta de paso: se mide que la máquina no tiene época
para un puntero fuera de catálogo (la calibración de la tabla es parte del
diseño, no una consecuencia automática de la aritmética).

## Lemas

1. **Descomposición (exhaustivo, 59049 palabras, 0 discrepancias).**
   `V = crazy(M, P)` con `P = 29524 + Σ_{trit_p(V)=1} 3^p` y
   `M = 29524 + Σ_{trit_p(V)≠0} 3^p`, ambas en `{1,2}^10`.
2. **Resultado negativo del semigrupo.** El semigrupo de composiciones de
   `crazy` sobre un trit tiene exactamente **15 mapas**, y el mapa
   "trit -> dígito de control" que haría falta (`(0,2,0)` o `(0,2,2)`) **no** es
   alcanzable (el `(0,0,2)` sí lo es). Por eso la petición lleva dígitos de
   control y no los 10 trits: es una limitación de la álgebra, no del programa.
3. **Tabla de épocas.** Las tres filas cumplen `(v+T+1)%94 = 81`, `v+1` encadena
   con `W` y `b = T-1`.

## Espacio de diseño (medido)

En la zona de dato (`34 <= T <= 126`), las épocas que admiten un sucesor
imprimible `v ≡ 80 - T (mod 94)` con `v+1 <= 126` son **92**. Este pack
implementa **3** de ellas: una tríada sin conflictos de valores (cada época
necesita su celda sucesora y su propia celda de trampolín). El conjunto completo
de 92 (o incluso de 3 en general) **no** está demostrado: no se ha construido la
selección de celdas sin conflictos ni medido su coste de rutado.

## Lo que este pack NO demuestra

- **NOT_DEMONSTRATED**: rearmar la época para una **segunda** petición en la
  misma ejecución (`epoch_rearm_primitive_v1` sigue sin componerse con esta
  selección). El programa actual consume 21 bytes y termina.
- **NOT_DEMONSTRATED**: las 92 épocas candidatas; sólo 3 están implementadas y
  medidas.
- **NOT_DEMONSTRATED**: byte de época arbitrario (fuera de catálogo) — medido
  que no selecciona ninguna época.
- **NOT_DEMONSTRATED**: un payload que sea `OUT` en las tres épocas a la vez.
  Medido (lema de opcodes triples): con estas tres épocas (residuos 6, 12, 18
  módulo 94) hay **0** residuos `r` para los que `r`, `r+6` y `r+12` sean
  opcodes válidos; con tres épocas alineadas a 94 (`epoch_algebra_v3`) hay **8**
  (uno por cada opcode válido). Es el precio del desacoplamiento por la
  cadena de dos `DLOAD`.

## Reproducción

```
cd vm_malbolge/evidence/epoch_resolver_epoch_select_v1
python3 build.py .          # reconstruye resolver_epoch.mb + build_index.json
python3 probe.py            # exit 0; escribe results.json
python3 manifest.py         # regenera manifest.json
```

## Corrección posterior (2026-11-10, adición — sólo se añade; no se reescribe lo anterior)

El punto «`NOT_DEMONSTRATED`: rearmar la época para una **segunda** petición en la
misma ejecución» sigue vigente como afirmación de este pack — este pack consume 21
bytes y termina. Lo que se ha añadido desde entonces es la **medición de la
barrera**, en [`epoch_rearm_barrier_v1/`](../epoch_rearm_barrier_v1/):

* el **rearm de una celda de dato es universal y exacto**
  (`crazy(29524,X) = extract2(X)` y `crazy(E,E) = 29524` sobre las 59049 palabras,
  0 discrepancias): la celda de época que consume un payload puede volver a su
  máscara `29524` siempre;
* el **rearm de una celda de código** (necesario para re-ejecutar el cuerpo del
  programa) sí tiene una vía, pero acotada: el cifrado XLAT2 posterior a la
  ejecución se deshace con un único `CRAZY` en 839 de los 2400 pares
  (opcode, celda), y la palabra de control de esa restauración sólo es
  materializable en 26 celdas (siempre la misma palabra, 29403);
* el salto de retorno con una celda sembrada sólo alcanza destinos 34..127, y la
  imagen actual mide 340 bytes.

Ninguna de esas mediciones cambia lo que este pack midió: aquí la época la elige
la petición y el payload también, una vez.

## Corrección posterior 2 (2026-11-10, auditoría — sólo se añade; no se reescribe lo anterior)

Auditoría independiente en [`epoch_audit_v1/AUDIT.md`](../epoch_audit_v1/AUDIT.md).
Un intérprete escrito sin código del repo reproduce las 7 instancias y los tres
controles, y la reproducción es byte a byte. Correcciones de alcance:

* **Dialecto**: 24 de las 340 celdas (la zona de dato) no decodifican a un opcode
  válido en su posición, y 6 de los 7 payloads se ejecutan desde celdas no
  imprimibles. El resultado vale en **Classic permisivo** (cargador sin validación,
  ejecución de cualquier valor). Para el intérprete de Olmstead de 1998 queda
  `NOT_DEMONSTRATED`.
* **"4 motores coinciden"**: en 6/7 instancias el runner C para en la guarda; la
  ejecución del payload la confirman sólo motores Python (los dos trazadores
  comparten el bucle de `probe.py`), más el intérprete de la auditoría.
* **Control C**: un barrido de los 256 bytes de época confirma que ningún byte
  fuera de catálogo aterriza en una celda de época, pero 30 de 253 sí producen
  salida (b = 50 es uno de los silenciosos).
* **Lema del semigrupo**: 15 mapas es correcto en el modelo de un operando. Con dos
  operandos el mapa `(0,2,0)` es alcanzable (`crazy(a=1, mem=crazy(a=2, mem=x))`),
  así que la limitación es del modelo y no "del álgebra"; la ruta práctica
  (constante 59048) queda `NOT_DEMONSTRATED`.
* `manifest.json` no se regeneró tras la corrección anterior: el hash de este
  VERDICT no coincide con el registrado, por diseño append-only.

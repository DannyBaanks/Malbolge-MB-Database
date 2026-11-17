# Capacidades de Malbolge y MBIR

## UNIECO: eco binario con EOF y relocalización

Una imagen Classic de **33 822 bytes** instala su núcleo de eco dentro de Malbolge, es aceptada por el cargador histórico de Olmstead y termina por sí misma al llegar a EOF. En las pruebas nativas reprodujo exactamente 261 entradas: vacío, NUL, una mezcla binaria, los 256 valores individuales, la secuencia `00..ff` y un flujo de 10 000 bytes. El modelo scratch también terminó con salida exacta en los cinco vectores principales; un control de cargador inválido y otro de instalación alterada fallaron como se esperaba. Son resultados para las entradas medidas, no una prueba de todos los flujos posibles.

El compilador experimental [`compile_bf.py`](vm_malbolge/evidence/unieco_bf_compile_v1/compile_bf.py) acepta el patrón Brainfuck `,+[-.,+]` con celdas de 16 bits y EOF=65535, y lo compila mediante una **plantilla Malbolge autenticada**. Rechaza otros programas y convenciones: no es un compilador general de Brainfuck ni demuestra equivalencia de estados internos. La imagen relocaliza un núcleo de la referencia PureEpoch/BolgeForge; el EOF del bucle compacto de la candidata anterior sigue `NOT_DEMONSTRATED`.

Para comparar trazas, el código fuente actualizado de REA ofrece `eof_mode=olmstead_1998`. Con ese modo, la imagen compilada produjo `00 0a 80 ff` y `HALTED` en una prueba acotada. El runner C de este repositorio puede detener el host al agotarse la entrada, de modo que su etiqueta `HALTED` por sí sola no demuestra un halt autónomo; su prueba de 10 000 bytes agotó el tiempo límite.

Imagen, controles, hashes y resultados: [`veredicto`](vm_malbolge/evidence/unieco_bf_compile_v1/VERDICT.md), [`manifiesto`](vm_malbolge/evidence/unieco_bf_compile_v1/manifest.json) y [`guía de uso`](vm_malbolge/evidence/unieco_bf_compile_v1/GUIA.md).

> **Récord vigente (2026-10-17): quine clásica de 53,562 bytes** — la quine más pequeña producida y verificada por este ecosistema, **6,290 bytes menor** que la quine de referencia de Matthias Lutter (59,852 B). Sintetizada por **BolgeForge**, verificada byte a byte con triple motor C independiente. Detalles, hashes y reproducción: [`quine/README.md`](quine/README.md).

---

## Lo que SÍ hace ya (DEMONSTRATED)

### 1. Bucle de Captura y Ejecución en Malbolge Puro (Hito A04)
Implementado en ensamblador de bajo nivel HeLL ([`vm_malbolge/src/mbir_a04_gate.hell`](vm_malbolge/src/mbir_a04_gate.hell)) a través del generador canónico ([`vm_malbolge/tools/mbir_a04_gate_gen.py`](vm_malbolge/tools/mbir_a04_gate_gen.py)):
- **`01 <operand>` (`PUSH_CONST`)**: Ingiere el opcode de stdin, reconoce la instrucción, captura el siguiente byte como operando, lo almacena en la celda dedicada `stack_top` mediante la involución Crazy `C1/C2`, reinicia el acarreo y los flags de desvío, y salta de regreso al bucle principal de despacho.
- **`10` (`OUT_BYTE`)**: Reconoce la instrucción, recupera el byte almacenado en la celda dedicada `stack_top`, lo emite por la salida estándar (`OUT`), reinicia el estado y regresa al bucle principal.
- **`00` (`HALT`)**: Reconoce el byte nulo de terminación y detiene la máquina inmediatamente sin emitir salida.
- **Persistencia entre ciclos**: El operando sobrevive intacto al bucle de despacho hasta que una instrucción posterior lo consume.
- **Paridad bit a bit y conteo de pasos exacto (7/7 PASS)** verificado de forma idéntica en:
  - Oráculo Clásico en Python ([`tools/oracle_classic.py`](tools/oracle_classic.py))
  - Runner nativo de Malbolge en C ([`runners/malbolge-original/malbolge`](runners/malbolge-original/malbolge))
  - Oráculo de referencia MBIR en Zig ([`mbir-zig`](mbir/zig/README.md))

| Vector | Operaciones | Salida | Pasos Malbolge | Veredicto |
|---|---|---|---|---|
| `01 41 10 00` | PUSH_CONST 'A', OUT_BYTE, HALT | `41` (`A`) | **61,199** | **MATCH / PASS** |
| `01 42 10 00` | PUSH_CONST 'B', OUT_BYTE, HALT | `42` (`B`) | **61,199** | **MATCH / PASS** |
| `00` | HALT directo | *(vacía)* | **55,194** | **MATCH / PASS** |
| `01 41 00` | PUSH_CONST 'A', HALT (sin OUT_BYTE) | *(vacía)* | **58,964** | **MATCH / PASS** |
| `01 7a 10 00` | PUSH_CONST 'z', OUT_BYTE, HALT | `7a` (`z`) | **61,199** | **MATCH / PASS** |
| `01 00 10 00` | PUSH_CONST `0x00`, OUT_BYTE, HALT | `00` | **61,199** | **MATCH / PASS** |
| `01 ff 10 00` | PUSH_CONST `0xff`, OUT_BYTE, HALT | `ff` | **61,199** | **MATCH / PASS** |

### 2. Bucle Multi-Ciclo Reentrante (Hito A05)
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_a05_multicycle.hell`](vm_malbolge/src/mbir_a05_multicycle.hell)) a través de ([`vm_malbolge/tools/mbir_a05_multicycle_gen.py`](vm_malbolge/tools/mbir_a05_multicycle_gen.py)):
- **Teorema del Reset Universal 3-Crazy**: Se descubrió y verificó exhaustivamente que `crz(C0, crz(C2, crz(C1, X))) == 29524 (C1)` para **TODOS** los 59,049 valores de Malbolge. Permite limpiar y re-inicializar incondicionalmente las celdas de almacenamiento tras cada `OUT_BYTE`.
- **Arquitectura Optimizada**: Eliminación de variables legadas (`tmp1..tmp4`) y comprobación EOF muerta, reduciendo el binario compilado de 52,623 a **40,309 bytes** (ahorrando >12,000 bytes bajo el límite de memoria) y recortando ~20,000 pasos de inicialización.
- **Multiplexación de Flags**: Celdas de datos comparten sólo 3 flags en `.CODE`, respetando la física de Malbolge (un único ciclo de 2 elementos en XLAT2: `F <-> J`).
- **Escalabilidad y Cero Deriva**: 8/8 vectores PASS con paridad bit a bit en el Oráculo Python, Runner C nativo y Zig (`mbir-zig`). Escala a exactamente **+6,046 pasos por iteración** sin deriva de fase, permitiendo secuencias arbitrarias de N caracteres (ej. "AB", "ABC", "hello").

### 3. Pila Concurrente LIFO de 2 Ranuras (Hito A05b)
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_a05_lifo.hell`](vm_malbolge/src/mbir_a05_lifo.hell)) a través del generador canónico ([`vm_malbolge/tools/mbir_a05_lifo_gen.py`](vm_malbolge/tools/mbir_a05_lifo_gen.py)):
- **Máquina de Estados de Profundidad de Pila (FSM)**: Mediante dos sitios de flag de código (`SLOT0_FLAG` y `SLOT1_FLAG`), la VM emula dinámicamente un puntero de pila de 2 posiciones:
  - Nivel 0 (vacía): `SLOT0 = Nop, SLOT1 = Nop`
  - Nivel 1 (1 elemento): `SLOT0 = MovD, SLOT1 = Nop` (ocupando Ranura 0: `stack_top`)
  - Nivel 2 (2 elementos concurrentes): `SLOT0 = MovD, SLOT1 = MovD` (Ranura 0 y Ranura 1: `stack_top_1`)
- **Inversión LIFO Genuina**: `PUSH 'A'`, `PUSH 'B'`, `OUT`, `OUT`, `HALT` (`01 41 01 42 10 10 00`) emite **`42 41` ("BA")** en riguroso orden LIFO.
- **Preservación de Estado**: Desapilar el tope deja intacto el elemento de la ranura 0 (`01 41 01 42 10 00` -> `42`).
- **Tamaño de Binario**: 51,877 bytes compilado con LMAO (cómodamente dentro del límite estricto de 59,049 palabras de Malbolge Classic).
- **Paridad 7/7 MATCH** en Zig Oracle, Python Classic Oracle y Runner nativo C (`vm_malbolge/evidence/mbir_a05_lifo_smoke.json`).

### 4. Kernel Aritmético y ALU Unificada (Hitos P0, P1 y ALU)
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_alu.hell`](vm_malbolge/src/mbir_alu.hell)) a través del generador canónico ([`vm_malbolge/tools/mbir_alu_gen.py`](vm_malbolge/tools/mbir_alu_gen.py)):
- **Hito P0 (`ADD` 0x02)**: Sumador ternario de 2 operandos desapilados concurrentemente de la pila LIFO, evaluando suma aritmética con acarreo y apilando el resultado en `stack_top` (7/7 PASS, [`vm_malbolge/P0_STATUS.md`](vm_malbolge/P0_STATUS.md)).
- **Hito P1 (`SUB` 0x03)**: Restador ternario de 2 operandos desapilados (`a - b`), evaluando resta con detección de subdesbordamiento (7/7 PASS, [`vm_malbolge/P1_STATUS.md`](vm_malbolge/P1_STATUS.md)).
- **ALU Unificada**: Cohabitación simultánea de `ADD` (0x02) y `SUB` (0x03) en la misma imagen ejecutable binaria ([`vm_malbolge/src/mbir_alu.mb`](vm_malbolge/src/mbir_alu.mb)), pesando **54,691 bytes** (dejando 4,358 bytes de margen bajo el límite de 59,049 palabras).
- **Despacho Secuencial de 5 Opcodes**: Clasificación unificada para `HALT` (0x00), `PUSH_CONST` (0x01), `ADD` (0x02), `SUB` (0x03) y `OUT_BYTE` (0x10).
- **Expresiones Aritméticas Encadenadas**: Soporte verificado para secuencias continuas como `(1 + 1) - 1 = 1`, `(1 + 1) - 2 = 0` y `(2 - 1) + 1 = 2`.
- **Paridad 14/14 PASS**: Paridad diferencial bit a bit ciclo por ciclo entre el runner de C nativo y el oráculo Python ([`vm_malbolge/evidence/mbir_alu_smoke.json`](vm_malbolge/evidence/mbir_alu_smoke.json)).
- **Límite de dominio (2026-11-06)**: el kernel clasifica el segundo operando en tres clases y materializa el resultado con constantes `ROT` fijas, por lo que la aritmética entera se reproduce solo en un subconjunto acotado del dominio; los operandos $\ge 3$ no están cubiertos. Véase la sección "Domain Limit" de [`vm_malbolge/ALU_STATUS.md`](vm_malbolge/ALU_STATUS.md) y la medida [`vm_malbolge/evidence/mbir_alu_domain_limit.json`](vm_malbolge/evidence/mbir_alu_domain_limit.json).

### 5. Kernel de Comparación Lógica: CMP_EQ (Hito P2)
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_p2_cmp.hell`](vm_malbolge/src/mbir_p2_cmp.hell)) a través de ([`vm_malbolge/tools/mbir_p2_cmp_gen.py`](vm_malbolge/tools/mbir_p2_cmp_gen.py)):
- **Evaluación Booleana de 2 Fases**: Desapila `op2 = b` de la ranura 1 y `op1 = a` de la ranura 0, evalúa igualdad binaria exacta (`a == b -> 1`, `a != b -> 0`) y apila el resultado booleano de 1 byte en la ranura 0 mientras restablece la ranura 1 a vacía.
- **Propiedades de Igualdad Verificadas**:
  - Reflexividad / Auto-igualdad: `2 == 2 -> 1` (`01`)
  - Desigualdad de predecesor: `2 == 1 -> 0` (`00`)
  - Desigualdad con cero: `2 == 0 -> 0` (`00`)
  - Desigualdad multi-unidad: `4 == 2 -> 0` (`00`)
- **Tamaño de Binario y Margen**: **57,511 bytes** (< 59,049 con 1,538 bytes de margen) usando exactamente 6 flags de código reutilizados sin flags espurios.
- **Paridad 7/7 PASS**: 100% coincidencia bit a bit ciclo por ciclo contra el runner C nativo y oráculo Python ([`vm_malbolge/evidence/mbir_p2_cmp_smoke.json`](vm_malbolge/evidence/mbir_p2_cmp_smoke.json), [`vm_malbolge/P2_STATUS.md`](vm_malbolge/P2_STATUS.md)).

### 5b. Kernel de Orden Relacional: CMP_LT (Hito P2 relacional) — **12/12 DEMONSTRATED**
Herramientas y forquilla propias: ensamblador HeLL [`vm_malbolge/src/mbir_cmp_lt.hell`](vm_malbolge/src/mbir_cmp_lt.hell) con su generador [`vm_malbolge/tools/mbir_cmp_lt_gen.py`](vm_malbolge/tools/mbir_cmp_lt_gen.py) (bifurcación de `mbir_p2_cmp_gen.py`; la imagen `CMP_EQ` congelada no se tocó), y el harness diferencial [`vm_malbolge/tests/lt_harness.py`](vm_malbolge/tests/lt_harness.py): **9 pares ordenados sobre `{0,1,2}`** (imprime `01` sii `a < b`, si no `00`) **más 3 líneas base** (`PUSH`/`OUT` → `41`, LIFO → `4241`, `HALT` → vacío). Cada vector corre en los dos motores — oráculo Python [`tools/oracle_classic.py`](tools/oracle_classic.py) y runner nativo C [`runners/malbolge-original/malbolge`](runners/malbolge-original/malbolge) — se compara salida **y** número de pasos.

**Estado vigente (2026-11-05): `12/12 DEMONSTRATED` en ambos motores.** Imagen canónica [`vm_malbolge/src/mbir_cmp_lt.mb`](vm_malbolge/src/mbir_cmp_lt.mb) (57.511 B, 1.538 B de margen bajo el límite de 59.049), construida con LMAO v0.6.0 desde `mbir_cmp_lt.hell`, blob sha256 `79160ecf906ce3a4…`, copia inmutable en [`vm_malbolge/evidence/artifacts/lt_pass12.mb`](vm_malbolge/evidence/artifacts/lt_pass12.mb). Manifiesto de referencia: [`vm_malbolge/evidence/lt_12_12_harness.json`](vm_malbolge/evidence/lt_12_12_harness.json) (Finding 74, 2026-10-14). Reverificación independiente de hoy: [`vm_malbolge/evidence/lt_12_12_reverify_2026-11-05.json`](vm_malbolge/evidence/lt_12_12_reverify_2026-11-05.json) — 12/12 en ambos motores con **los mismos recuentos de pasos** que el manifiesto original (78.906 / 81.977 / 81.317 / …).

**Causa raíz del bloqueo y su resolución (Finding 74).** La fuga de estado estaba en la rama `b=1`: el flag `SUBROUTINE_FLAG3`, reutilizado allí como variable de condición, está reservado por el núcleo de la VM (`exit_decrement_loop`) para gobernar el retorno del tercer decremento de la decodificación de opcodes; al quedar en estado `MovD` (opcode 40) perturbaba el despacho del `OUT` siguiente. La resolución fue un flag dedicado e independiente `LT_B1` en `.CODE` (más la purga del símbolo inerte `COUNTER2_1`, que además liberaba el conflicto de colocación de memoria en LMAO) y un enrutamiento por subdesbordamiento limpio: `b=0` → `diff_is_2` (`00`); `b=1` → `diff_is_1` arma `LT_B1`; `b=2` → `op2_is_2` deja `LT_B1` inerte; y en la fase de `a` el flag decide entre `a=0` (`01`) y `a≥1` (`00`) para `b=1`, o `a<2` (`01`) frente a `a=2` (`00`) para `b=2`. Bitácora completa y append-only: [`vm_malbolge/LT_STATUS.md`](vm_malbolge/LT_STATUS.md) §11.

**Recorrido histórico hasta el 11/12 (conservado; fue la base de la resolución):**
- **Techo de esa etapa: 11/12 con paridad exacta entre motores.** Ocho imágenes `.mb` commiteadas, cada una con su manifiesto JSON de harness en [`vm_malbolge/evidence/`](vm_malbolge/evidence/):

| imagen | sha256 (blob == fichero de trabajo) | resultado | entrada(s) que falla(n) |
|---|---|---|---|
| `lt_head11_probe.mb` | `2838e63c02507e85…` | 11/12 | `cmp_lt(0,1)` → `00` |
| `lt_f59_cand_A.mb` | `a96dd7615a6e8d60…` | 11/12 | `cmp_lt(2,2)` → `02` |
| `lt_f59_cand_B.mb` | `4c1a9b1a9300bec5…` | 11/12 | `cmp_lt(1,2)` → `00` |
| `lt_f59_cand_C.mb` | `b7bb3a82d55e5f4f…` | 11/12 | `cmp_lt(2,2)` → `01` |
| `lt_f59_cand_D.mb` | `1f7b7bdc534019e2…` | 11/12 | `cmp_lt(2,2)` → `02` |
| `lt_f62_line448_decop1.mb` | `f1420e49584fddb9…` | 11/12 | `cmp_lt(0,1)` → `00` |
| `lt_f62_line448_rfcwns2.mb` | `9bbfb6692ead5d9a…` | 11/12 | `cmp_lt(0,1)` → `00` |
| `lt_a7c9_probe.mb` | `21680622b6a3d165…` | 9/12 | `(0,1)`, `(0,2)`, `(1,2)` → `00` |

- **Las tres líneas base pasan en los dos motores sobre la bifurcación**, o sea el núcleo de la VM (bucle de despacho, pila LIFO de 2 ranuras, `OUT`) sigue intacto; el fallo es de clasificación/salida del comparador, no del intérprete.
- **Paridad de motores re-medida el 2026-10-14** sobre la imagen base del Hallazgo 72: los doce vectores dan la misma salida y el mismo número de pasos en ambos motores **incluida la entrada que falla** (`cmp_lt(2,2)` → `01` con 79.790 pasos en el oráculo y en el nativo). La discordancia de modelos queda descartada como explicación del 11/12.
- **El lema de instancia de build (F62) vuelve a medirse el 2026-10-14:** recompilar `vm_malbolge/evidence/lt_f59_cand_C.hell` con LMAO v0.6.0 produce una tercera instancia (`fb0a775d16657dcd…`) que difiere de la commiteada (`b7bb3a82d55e5f4f…`) en los mismos 503 bytes de la cola `56920..57507`, y el harness la puntúa **11/12 con la firma idéntica de salida y pasos en los doce vectores**. Tres instancias distintas — commiteada, copia de trabajo de F72 (`f67ec678d56db73c…`) y recompilación de hoy — una sola clase de comportamiento.
- **Evidencia cruda de las re-medidas de esa etapa:** [`vm_malbolge/evidence/lt_recheck_2026-10-14.txt`](vm_malbolge/evidence/lt_recheck_2026-10-14.txt) (sha256 `4f41eb03aa61c9dc…`) — salida verbatim del harness sobre las cuatro imágenes, con hash de fichero de trabajo y de blob en cada una. Ahí quedó medido que, **en aquel entonces**, la imagen canónica de la bifurcación `vm_malbolge/src/mbir_cmp_lt.mb` seguía en 8/12 (fallaban `(0,1)`, `(0,2)`, `(1,2)` → `00` y `(2,2)` → `01`, con paridad entre motores en las cuatro): los 11/12 de esa etapa no vivían en el `.hell` de la bifurcación sino en las imágenes de `vm_malbolge/evidence/artifacts/`. La imagen canónica de hoy es **otra** (Finding 74): 12/12.
- **Leyes estructurales verificadas** (cada una con su censo o su ejecución, en [`vm_malbolge/LT_STATUS.md`](vm_malbolge/LT_STATUS.md)): ley del veredicto — el dígito impreso es función pura del contenido de la única celda que lee el `ROT` compartido (`0/3/6 → 00/01/02`), F47/F48/F56/F58; techo de tabla — `trit0(A)=0` no puede emitir un trit `0`, F57; escaneo exhaustivo de los 3^10 valores — ninguna celda codifica la tabla `LT` en el instante de decisión, F59; techo de solo-lectura a toda profundidad de pliegue y colapso a constante del mejor encaje, F60/F63; **el comparador nunca se calcula** — ni un pliegue ni una composición de dos reproducen `a+b·LT` sobre los nueve pares con la tabla `_CRAZY` real, F61; lema de instancia de build — seis compiladas seguidas del mismo `.hell` dan seis `.mb` con sha distintos y una única firma de comportamiento (los 503 bytes que distinguen a `lt_f59_cand_C.mb` de la copia de trabajo están todos en la cola `56920..57507`, que nunca es `pc` ni operando de lectura), F62; ley del acumulador separante, F70; el veredicto no viaja en los datos sino en la **paridad de traducción** de la celda de código 58156, y el flag se escribe una sola vez con el mismo `a_in` en los nueve vectores, F71; `(0,1)` y `(2,2)` **son un solo cálculo** — 0 pasos de divergencia de punteros en 79.790 y los 7 pliegues `a`-divergentes caen íntegros en el relleno (0 en región editable), F72.
- **Negativos cuantificados y conservados:** el espacio completo de ediciones de un carácter sobre la base 11/12 es 5.234.616 variantes (cota inferior; ≈3.900 CPU-horas) y **no se ha barrido**; sí están barridas y cerradas las 5.580 ediciones vivo-directas y las 186 ediciones de semilla simple (5.766 variantes, **0 arreglos**), con un único acierto aparente que resultó degenerado — halta en 2 pasos e imprime `00` a los doce vectores, o sea 6/12 — y la palanca global de semilla invertida en bloque (155 variantes matan la máquina, 12 basura, 19 conservan el `01` errado).
- **Redirección del problema abierto:** en las imágenes A y D el vector `(2,2)` **ya imprime el símbolo propio `02`**, así que en esas bases lo que falta es mapear un `2` ya selectivo a `0`, no construir la tabla.

**Lo que NO está demostrado (hoy):** el dominio fuera de `{0,1,2}^2` — cualquier operando ≥ 3 — sigue **`NOT_DEMONSTRATED`** por diseño del hito: el kernel clasifica $b$ en tres clases (`0`, `1`, `2`) sobre aritmética ternaria, así que `a<b` con operandos mayores exige otro comparador. Tampoco está demostrado que `CMP_LT` conviva en una **sola imagen** con la ALU de 14 vectores y el `CMP_EQ` (ver "Lo que FALTA", punto 2). Todo el resto de aquella etapa quedó **cerrado por medida** y se conserva como negativo, no como tarea abierta: barridos de ediciones de un carácter y de la pareja de semillas (F72, F73), transferencia íntegra de la batería de F72 a las bases A y D, y el lema de familia de F73 §7 (`(0,1)` y `(2,2)` son un solo cálculo en las tres bases 11/12).

### 5c. Kernel de Orden Relacional: CMP_GT (Hito P2 relacional inverso) — **12/12 DEMONSTRATED**
Imagen canónica [`vm_malbolge/src/mbir_cmp_gt.mb`](vm_malbolge/src/mbir_cmp_gt.mb) (57.511 B, 1.538 B de margen), construida con LMAO v0.6.0 desde `mbir_cmp_gt.hell` con su generador [`vm_malbolge/tools/mbir_cmp_gt_gen.py`](vm_malbolge/tools/mbir_cmp_gt_gen.py), y harness propio [`vm_malbolge/tests/gt_harness.py`](vm_malbolge/tests/gt_harness.py): 9 pares ordenados sobre `{0,1,2}` (imprime `01` sii `a > b`, si no `00`) más las mismas 3 líneas base. **12/12 en ambos motores** con paridad bit a bit, Finding 75 (2026-10-15); blob sha256 `1f17062a9585beb…`, copia inmutable en [`vm_malbolge/evidence/artifacts/gt_pass12.mb`](vm_malbolge/evidence/artifacts/gt_pass12.mb) y manifiesto en [`vm_malbolge/evidence/gt_12_12_harness.json`](vm_malbolge/evidence/gt_12_12_harness.json). Reverificación independiente de hoy: [`vm_malbolge/evidence/gt_12_12_reverify_2026-11-05.json`](vm_malbolge/evidence/gt_12_12_reverify_2026-11-05.json). Arquitectura (flag dedicado `GT_B1`, enrutamiento simétrico por subdesbordamiento) y evidencia completa: [`vm_malbolge/GT_STATUS.md`](vm_malbolge/GT_STATUS.md).

### 6. Stored-Program Loader y Ejecución Desacoplada por PC (Hito M2)
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_m2_loader.hell`](vm_malbolge/src/mbir_m2_loader.hell)) a través de ([`vm_malbolge/tools/mbir_m2_loader_gen.py`](vm_malbolge/tools/mbir_m2_loader_gen.py)):
- **Celdas de RAM en Memoria (`prog_0..prog_3`)**: Los bytes del programa se leen primero de STDIN durante una fase dedicada de carga y se comprometen en celdas de RAM independientes usando el teorema de escritura Crazy dual incondicional: `crz(crz(B, C1), C1)`.
- **Desacoplamiento Total de Ejecución por PC**: STDIN se consume completamente hasta el delimitador de carga. Finalizada la carga, el Program Counter (`PC`) asume el control del despacho, leyendo secuencialmente los opcodes de la memoria RAM para gobernar la máquina de pila.
- **Extracción de Operandos Inmediatos Doble-C2**: Los operandos embebidos en el flujo de instrucciones se recuperan de las celdas de memoria de forma no destructiva aplicando la identidad conjugada ternaria: `crz(C2, crz(C2, cell)) == B (mod 256)`.
- **Tamaño de Binario y Eficiencia**: **40,309 bytes** (< 59,049 con un margen holgado de **18,740 bytes**).
- **Paridad 4/4 PASS**: 100% coincidencia bit a bit ciclo por ciclo frente al runner C nativo y el oráculo Python ([`vm_malbolge/evidence/mbir_m2_loader_smoke.json`](vm_malbolge/evidence/mbir_m2_loader_smoke.json), [`vm_malbolge/M2_LOADER_STATUS.md`](vm_malbolge/M2_LOADER_STATUS.md)).

### 6b. ALU de programa almacenado (Hito M2 ALU)
Una imagen aparte carga un programa de 7 bytes y ejecuta un solo `ADD` (0x02) o `SUB` (0x03) con operandos en `{0,1,2,3,4}` ([`vm_malbolge/src/mbir_m2_alu.hell`](vm_malbolge/src/mbir_m2_alu.hell), [`vm_malbolge/tools/mbir_m2_alu_gen.py`](vm_malbolge/tools/mbir_m2_alu_gen.py)):
- **8/8 PASS** en el oráculo Python y el runner C, con el mismo número de pasos y el byte crudo esperado.
- **Tamaño**: 56,361 bytes (margen 2,688 bajo 59,049).
- **Alcance**: un solo tiro. No es un restador general, no encadena operaciones y no cubre los 14 vectores de la ALU por STDIN.
- Evidencia: [`vm_malbolge/evidence/mbir_m2_alu_smoke.json`](vm_malbolge/evidence/mbir_m2_alu_smoke.json), [`vm_malbolge/M2_ALU_STATUS.md`](vm_malbolge/M2_ALU_STATUS.md).

### 6c. Salto, condicional y llamada sobre RAM (Hito M2 CF)
Una imagen aparte carga un programa de 11 bytes y ejecuta cinco formas fijas ([`vm_malbolge/src/mbir_m2_cf.hell`](vm_malbolge/src/mbir_m2_cf.hell), [`vm_malbolge/tools/mbir_m2_cf_gen.py`](vm_malbolge/tools/mbir_m2_cf_gen.py)):
- **JMP `0x0C`** emite el inmediato guardado en RAM. Dos inmediatos distintos (`0x41` y `0x58`) salen con el mismo número de pasos.
- **JZ** (opcode `0x01`) emite un byte si la condición es 0 y otro si es 1.
- **CALL `0x0E`** emite el byte del destino y después el byte que sigue a la llamada. Una sola trama.
- **5/5 PASS** en el oráculo Python y el runner C. Tamaño 55,819 bytes (margen 3,230).
- En esta imagen el destino del JMP no elige la instrucción y no hay contador de programa general; el track de despacho computado sí enruta por opcode y llega a N=5 encadenadas (secciones 14d–14e).
- Evidencia: [`vm_malbolge/evidence/mbir_m2_cf_smoke.json`](vm_malbolge/evidence/mbir_m2_cf_smoke.json), [`vm_malbolge/M2_CF_STATUS.md`](vm_malbolge/M2_CF_STATUS.md).

### 6d. Control de Flujo con Comparación Relacional en RAM (Hito M2 CF + CMP_EQ)
Imagen canónica que unifica flujo de control almacenado con comparación relacional de igualdad en memoria ([`vm_malbolge/src/mbir_m2_cf_cmp.hell`](vm_malbolge/src/mbir_m2_cf_cmp.hell), [`vm_malbolge/tools/mbir_m2_cf_cmp_gen.py`](vm_malbolge/tools/mbir_m2_cf_cmp_gen.py), [`vm_malbolge/tests/m2_cf_cmp_harness.py`](vm_malbolge/tests/m2_cf_cmp_harness.py)):
- **JMP `0x0C`**: Emite el inmediato cargado en RAM saltando HALT (`0x41` y `0x58` pasan en 66,846 pasos).
- **JZ / JNZ `0x01`**: Salto condicional evaluando `prog_1` (`0` -> `prog_8` en 62,123 pasos; `1` -> `prog_7` en 62,718 pasos).
- **CALL `0x0E`**: Invoca subrutina emitiendo `prog_8` ('B') y retorna emitiendo `prog_4` ('A') en 68,060 pasos.
- **CMP_EQ `0x04`**: Compara en memoria `prog_1` contra `prog_4`:
  - `1 == 1` toma el salto y emite `prog_8` (0x42 'B', 64,572 pasos).
  - `1 != 2` no toma el salto y emite `prog_7` (0x43 'C', 65,124 pasos).
- **7/7 PASS con Paridad Dual 100% Bit-Exacta**: Tanto en el oráculo Python (`oracle_classic.py`) como en el runner C nativo (`malbolge`).
- **Tamaño y Margen**: 56,947 bytes (**2,102 bytes de margen** bajo el límite de 59,049 de Malbolge clásico $3^{10}$).
- Evidencia: [`vm_malbolge/evidence/mbir_m2_cf_cmp_smoke.json`](vm_malbolge/evidence/mbir_m2_cf_cmp_smoke.json), [`vm_malbolge/M2_CF_CMP_STATUS.md`](vm_malbolge/M2_CF_CMP_STATUS.md).

### 7. Tabla de Clasificación de los 18 Opcodes de MBIR
- Generador mecánico ([`vm_malbolge/tools/mbir_dispatch_gen.py`](vm_malbolge/tools/mbir_dispatch_gen.py)) que produce ensamblador HeLL para clasificar los 18 opcodes (`0x00`..`0x11`) en Malbolge puro usando cadenas de decremento digital root y sitios `SUBROUTINE_FLAGn` con paridad 21/21 verificada.

### 8. Primitivas Celulares y de Entrada Secuencial Demostradas
- Sonda de segunda lectura explícita con retorno `MOVED` ([`vm_malbolge/src/cell_stack_second_read.hell`](vm_malbolge/src/cell_stack_second_read.hell), 12/12 PASS).
- Bucle de entrada reutilizable hasta 16 bytes con parada en EOF ([`vm_malbolge/src/cell_stack_loop_echo.hell`](vm_malbolge/src/cell_stack_loop_echo.hell), 8/8 PASS).
- Almacenamiento y recuperación mediante celdas dedicadas `stack_scratch` / `stack_top` independientes.

### 9. Herramientas y Substratos Externos
- Binarios nativos compilados para Linux (LMAO, runner clásico, zig-oracle), eliminando dependencia de emulación Wine.
- Registro consolidado de 13 motores externos de la familia `-bolge` en [`registry/substrates.json`](registry/substrates.json) (Rustbolge, Swiftbolge, Javolge, Fortranbolge, Cobolge, Zigbolge, Pibolge, Pibolge19, Wasmbolge, MalbolgeEngineCPP, malbolge-free, malbolge-oracle, MalboGost).

### 10. Frontend Python P3 (variables y control de flujo, en el host)
[`python/src/p3_compiler.py`](python/src/p3_compiler.py) baja un subconjunto de Python a MBIR versión 0 y lo ejecuta en la VM de referencia [`mbir/mbir_ref.py`](mbir/mbir_ref.py). El parseo es `ast.parse`. No llama a `eval` ni a `exec`, y no sustituye una operación por su resultado.

- Asignación a un nombre, `print` de una expresión, `+` `-` `*` con vuelta en 256, una comparación (`==`, `<`, `>`), `if` / `else` / `elif` y `while`.
- `print` emite el byte crudo. `print(2 + 3)` da `05`. `print(200 + 100)` da `44`. `print(1 - 2)` da `255`.
- `if 5 > 3` deja en el blob `CMP_GT`, `JUMP_IF_FALSE` y los bytes de los dos brazos. El `while` que imprime 3, 2 y 1 tiene una sola `OUT_BYTE` y para a los 40 pasos.
- **15/15 HALT** en la VM de referencia. Esos 15 casos siguen dentro del harness.
- Esto corre en el host. No es un intérprete dentro de Malbolge, y no existe `python.mb`.
- Evidencia: [`python/evidence/P3/run_p3_compiler.json`](python/evidence/P3/run_p3_compiler.json), [`python/STATUS.md`](python/STATUS.md).

### 11. Frontend Python P4 (funciones, en el host)
[`python/src/p4_compiler.py`](python/src/p4_compiler.py) añade `def`, la llamada y `return` encima de P3. El cuerpo es un marco nuevo: los parámetros son los locales 0..n-1 y `RETURN` deja el valor en la pila. Los cuerpos van antes del módulo porque la dirección de `CALL` es un byte. Una llamada directa a sí misma se rechaza.

- `print(add(2, 3))` para en 10 pasos con el byte `05`. El blob es `JUMP`, dos `LOAD_LOCAL`, `ADD`, `RETURN`, `PUSH 2`, `PUSH 3`, `CALL`, `OUT_BYTE`, `HALT`.
- Dos llamadas comparten ese único `ADD`.
- **12/12 HALT** en la VM de referencia. Esos 12 casos siguen dentro del harness.
- Esto corre en el host. La recursión es P5. No existe `python.mb`.
- Evidencia: [`python/evidence/P4/run_p4_compiler.json`](python/evidence/P4/run_p4_compiler.json), [`python/STATUS.md`](python/STATUS.md).

### 12. Frontend Python P5 (recursión, en el host)
[`python/src/p5_compiler.py`](python/src/p5_compiler.py) permite que una función se llame a sí misma. Cada llamada tiene su marco. P4 sigue rechazando esa llamada.

- `print(fib(6))` para en 251 pasos con el byte `08`. El blob tiene tres `CALL` y un `ADD`. El 8 no está empujado.
- `fact(5)` conserva el `MUL` y saca el byte 120. `down(3)` emite `03 02 01 00` con un solo `OUT_BYTE` dentro de la función.
- **8/8 HALT** en la VM de referencia. El harness de la pista queda en **85/85**.
- Esto corre en el host. No hay lexer dentro de Malbolge, ni `python.mb`.
- Evidencia: [`python/evidence/P5/run_p5_compiler.json`](python/evidence/P5/run_p5_compiler.json), [`python/STATUS.md`](python/STATUS.md).

### 16. Una operación compartida con cuatro y cinco llamadores secuenciales (G5b P2–P5)

Una sola ejecución recorrió `ll → lr → rl → rr` y llamó cuatro veces a la operación compartida (`pc=38058`) con la misma variable (`d=40006`). Los retornos visitaron `15000 → 15004 → 15008 → 15012`; la salida fue `62e66ee6`. Olmstead, clasesbolge, el trazador local y REA coincidieron.

Un control que omite el ajuste de la bandera raíz en `lr` visita `15000 → 15012` y produce `62e6`, detectando el fallo. Esto demuestra solo la secuencia de cuatro llamadores preparada, una variable y un sitio compartido. [Puertas, resultados, trazas y reproducción](vm_malbolge/evidence/g5b_flag_return_v2/VERDICT.md).

P3 repite el caso en el orden cruzado `rr → ll → rl → lr`. La operación y variable siguen en `pc=38058` y `d=40006`; los cuatro retornos llegan a `15000 → 15004 → 15008 → 15012` y la salida vuelve a ser `62e66ee6`. Olmstead, `clasesbolge`, el trazador local y REA coinciden; una segunda generación reproduce exactamente la imagen positiva. El control agrega un ajuste de raíz al primer `rr`, desvía la única llamada a la continuación terminal `lr` (`15012`) y emite `62`. P3 por sí solo mide ese orden, no las otras permutaciones; P4 las barre. [Puertas, resultados, trazas REA, hashes y reproducción G5b P3](vm_malbolge/evidence/g5b_flag_return_v3/VERDICT.md).

P4 barre las 24 permutaciones posibles de los cuatro llamadores. En todas, el sitio `pc=38058` y la variable `d=40006` se comparten; hay cuatro retornos (`15000 → 15004 → 15008 → 15012`) y la salida es `62e66ee6`. Olmstead, `clasesbolge` y el trazador local coinciden en 48/48 ejecuciones; REA confirma las 24 órdenes con eventos completos. Dos procesos de generación reproducen cada imagen byte a byte, y cada orden produce una imagen distinta. El control negativo P3 mantiene una llamada y salida `62`. El resultado cubre solo estos cuatro llamadores, una variable y un sitio compartido. [Puertas, resultados, 24 trazas REA, hashes y reproducción G5b P4](vm_malbolge/evidence/g5b_flag_return_v4/VERDICT.md).

P5 añade una quinta hoja al dividir `ll` en `lll` y `llr` mediante una bandera adicional. En el orden `lll → rr → lr → rl → llr`, cinco llamadas pasan por `pc=38058` con la misma variable (`d=40006`), visitan `15000 → 15004 → 15008 → 15012 → 15016` y producen `62e66ee66e`. Olmstead, `clasesbolge` y el trazador local coinciden; dos generaciones reproducen la imagen byte a byte. El control que agrega la bandera en el primer `lll` selecciona el retorno terminal `15016`, hace una llamada y produce `62`. REA confirma terminación y salida, pero el límite de 4096 eventos trunca la captura antes de las rutas; su cobertura del sitio y retornos queda NOT_DEMONSTRATED. No se ha medido el orden de las 120 permutaciones posibles ni otros tamaños de conjunto. [Puertas, resultado, trazas REA y reproducción G5b P5](vm_malbolge/evidence/g5b_flag_return_v5/VERDICT.md).

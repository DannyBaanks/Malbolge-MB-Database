# Malbolge MB Database

Base de datos reproducible y laboratorio de investigación para programas Malbolge sustanciales, runtimes de lenguajes de alto nivel alojados sobre Malbolge, y el middleware **MBIR** (*Malbolge Bytecode Intermediate Representation*) que conecta frontends con substratos de ejecución.

> **Récord vigente (2026-10-16): quine clásica de 54,134 bytes** — la quine más pequeña producida y verificada por este ecosistema, **5,718 bytes menor** que la quine de referencia de Matthias Lutter (59,852 B). Sintetizada por **BolgeForge**, verificada byte a byte con doble motor C independiente. Detalles, hashes y reproducción: [`quine/README.md`](quine/README.md).

---

## Misión y Arquitectura

Investigar, construir, ejecutar y conservar programas `.mb` — especialmente intérpretes y runtimes de otros lenguajes implementados sobre Malbolge. MBIR es el boundary de intercambio neutral entre un frontend/adaptador y un substrato de ejecución; no pretende ser una VM omnilingüe mágica ni un truco superficial.

```text
Código fuente (ej. Python)
        │
        ▼
 Frontend / Compilador (ej. MalPy AST -> Bytecode MBIR)
        │
        ▼
   Stream MBIR (Contrato neutral v0: 18 opcodes congelados)
        │
 ┌──────┴───────────────────────────────────────────────────────┐
 │                                                              │
 ▼                                                              ▼
Intérprete VM Malbolge (.hell -> LMAO -> .mb)       Substratos Externos (-bolge)
 (Classic 3^10 / Unshackled 3^19)                    (Rustbolge, Zigbolge, Pibolge...)
```

---

## Principio Central: Disciplina Anti-Fake

**NUNCA ADIVINAR. CERO ALUCINACIONES.**

Si una propiedad no está demostrada de forma reproducible por código ejecutable, tests, trazas de pasos, hashes criptográficos SHA-256 y ejecuciones en oráculos independientes:

```text
NOT_DEMONSTRATED
```

- README ≠ evidencia.
- Nombre de carpeta ≠ evidencia.
- Reclamar soporte ≠ implementación demostrada.
- Para demostrar `print(2 + 3)`, **NO** se acepta un `.mb` que imprima directamente `5` por hardcodeo. Debe existir la cadena operacional demostrable (`PUSH 2`, `PUSH 3`, `ADD`, `PRINT`) con validación de operandos alterados.

---

## Estado Actual del Proyecto

| Componente | Estado | Hito Actual | Evidencia Canónica |
|---|---|---|---|
| **Quine Clásica (BolgeForge)** | `DEMONSTRATED` | **Quine de 54,134 B que imprime su propia fuente (récord: −5,718 B vs la referencia Lutter de 59,852 B)** | [`quine/quine_54134_m284.mb`](quine/quine_54134_m284.mb), [`quine/evidence/quine_54134_verification.json`](quine/evidence/quine_54134_verification.json) |
| **Contrato MBIR v0** | `DEMONSTRATED` | 18 opcodes congelados | `docs/MBIR_CONTRACT.md`, 23/23 tests `mbir/tests/test_mbir.py` |
| **VM de Referencia MBIR (Python)** | `DEMONSTRATED` | Soporte fib(6), llamadas, saltos, I/O | `mbir/mbir_ref.py`, 28/28 tests `mbir/tests/test_mbir_ref.py` |
| **Oráculo Nativo MBIR (Zig)** | `DEMONSTRATED` | Ejecución MBIR nativa y oráculo diferencial | `mbir/zig/` (`mbir-zig`) |
| **Frontend Python (MalPy / MBIR)** | `FRONTEND_DEMONSTRATED` | P5 (recursión directa → `CALL`/`RETURN` en la VM de referencia del host). | `python/src/p5_compiler.py`, `python/evidence/P5/`, suite en `python/tests/` |
| **Toolchain Nativo Linux** | `WORKING` | Ensamblado y ejecución 100% nativa sin Wine | LMAO v0.6.0 (`third_party/lmao/bin/lmao`), Runner C (`runners/malbolge-original/malbolge`) |
| **Malbolge VM Runtime (A04)** | `DEMONSTRATED` | **Bucle de ejecución y pila de 1 profundidad** | `vm_malbolge/src/mbir_a04_gate.hell`, `vm_malbolge/evidence/mbir_a04_gate_smoke.json` (7/7 PASS) |
| **Malbolge VM Bucle Multi-Ciclo (A05)** | `DEMONSTRATED` | **Ejecución secuencial arbitraria sin corrupción ('AB', 'ABC', 'hello')** | `vm_malbolge/src/mbir_a05_multicycle.hell`, `vm_malbolge/evidence/mbir_a05_multicycle_smoke.json` (8/8 PASS) |
| **Malbolge VM Pila LIFO de 2 Ranuras (A05b)** | `DEMONSTRATED` | **Pila LIFO concurrente de 2 ranuras ('BA' invertido)** | `vm_malbolge/src/mbir_a05_lifo.hell`, `vm_malbolge/evidence/mbir_a05_lifo_smoke.json` (7/7 PASS) |
| **Malbolge VM Kernel Aritmético (P0 / ADD)** | `DEMONSTRATED` | **Sumador ternario de 2 operandos desapilados (`0x02`)** | `vm_malbolge/P0_STATUS.md`, `vm_malbolge/evidence/mbir_p0_add_smoke.json` (7/7 PASS) |
| **Malbolge VM Kernel Aritmético (P1 / SUB)** | `DEMONSTRATED` | **Restador ternario de 2 operandos desapilados (`0x02`/`0x03`)** | `vm_malbolge/P1_STATUS.md`, `vm_malbolge/evidence/mbir_p1_sub_smoke.json` (7/7 PASS) |
| **Malbolge VM ALU Relacional Unificada (ALU_REL)** | `DEMONSTRATED` | **ALU + Comparador relacional (`ADD`, `SUB`, `CMP_EQ`) y expresiones encadenadas (25/25 PASS)** | `vm_malbolge/ALU_REL_STATUS.md`, `vm_malbolge/evidence/mbir_alu_rel_smoke.json` (25/25 PASS) |
| **Malbolge VM ALU Unificada (ADD + SUB)** | `DEMONSTRATED` | **ALU completa ejecutando ADD (`0x02`) y SUB (`0x03`) simultáneos** | `vm_malbolge/ALU_STATUS.md`, `vm_malbolge/evidence/mbir_alu_smoke.json` (14/14 PASS) |
| **Malbolge VM Kernel Comparación (P2 / CMP_EQ)** | `DEMONSTRATED` | **Igualdad booleana de 2 operandos desapilados (`0x02`)** | `vm_malbolge/P2_STATUS.md`, `vm_malbolge/evidence/mbir_p2_cmp_smoke.json` (7/7 PASS) |
| **Malbolge VM Orden Relacional (P2 / CMP_LT)** | `DEMONSTRATED` | **Menor Que estricto $a < b$ sobre $\{0,1,2\}^2$ + baselines con paridad dual** | `vm_malbolge/LT_STATUS.md`, `vm_malbolge/evidence/lt_12_12_harness.json` (12/12 PASS) |
| **Malbolge VM Orden Relacional (P2 / CMP_GT)** | `DEMONSTRATED` | **Mayor Que estricto $a > b$ sobre $\{0,1,2\}^2$ + baselines con paridad dual** | `vm_malbolge/GT_STATUS.md`, `vm_malbolge/evidence/gt_12_12_harness.json` (12/12 PASS) |
| **Malbolge VM Stored-Program Loader & PC (M2)** | `DEMONSTRATED` | **Cargador a RAM (`prog_0..3`) y ejecución desacoplada por PC** | `vm_malbolge/M2_LOADER_STATUS.md`, `vm_malbolge/evidence/mbir_m2_loader_smoke.json` (4/4 PASS) |
| **Malbolge VM ALU de programa almacenado (M2 ALU)** | `DEMONSTRATED` | **Un programa de 7 bytes cargado y un único `ADD`/`SUB` (8/8, un solo tiro)** | `vm_malbolge/M2_ALU_STATUS.md`, `vm_malbolge/evidence/mbir_m2_alu_smoke.json` |
| **Malbolge VM Salto/Condicional/Llamada en RAM (M2 CF)** | `DEMONSTRATED` | **Cinco formas fijas de `JMP`/`JZ`/`CALL` sobre bytecode cargado (5/5)** | `vm_malbolge/M2_CF_STATUS.md`, `vm_malbolge/evidence/mbir_m2_cf_smoke.json` |
| **Malbolge VM Control Flow + Relacional (M2 CF + CMP_EQ)** | `DEMONSTRATED` | **Siete formas de `JMP`/`JZ`/`CALL`/`CMP_EQ` en memoria con paridad dual (7/7)** | `vm_malbolge/M2_CF_CMP_STATUS.md`, `vm_malbolge/evidence/mbir_m2_cf_cmp_smoke.json` (7/7 PASS) |
| **Runtimes Swift, Rust, Java, C** | `NOT_STARTED` | Sin comenzar | Tracks registrados en `registry/languages.json` |

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
  - Oráculo de referencia MBIR en Zig ([`mbir-zig`](mbir/zig/zig-out/bin/mbir-zig))

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

### 5b. Kernel de Orden Relacional: CMP_LT (Hito P2 relacional) — **PARCIAL, mejor 11/12**
Herramientas y forquilla propias: ensamblador HeLL [`vm_malbolge/src/mbir_cmp_lt.hell`](vm_malbolge/src/mbir_cmp_lt.hell) con su generador [`vm_malbolge/tools/mbir_cmp_lt_gen.py`](vm_malbolge/tools/mbir_cmp_lt_gen.py) (bifurcación de `mbir_p2_cmp_gen.py`; la imagen `CMP_EQ` congelada no se tocó), y el harness diferencial [`vm_malbolge/tests/lt_harness.py`](vm_malbolge/tests/lt_harness.py): **9 pares ordenados sobre `{0,1,2}`** (imprime `01` sii `a < b`, si no `00`) **más 3 líneas base** (`PUSH`/`OUT` → `41`, LIFO → `4241`, `HALT` → vacío). Cada vector corre en los dos motores — oráculo Python [`tools/oracle_classic.py`](tools/oracle_classic.py) y runner nativo C [`runners/malbolge-original/malbolge`](runners/malbolge-original/malbolge) — y se compara salida **y** número de pasos.

**Lo que está demostrado (medido, con hash):**
- **Techo actual: 11/12 con paridad exacta entre motores.** Ocho imágenes `.mb` commiteadas, cada una con su manifiesto JSON de harness en [`vm_malbolge/evidence/`](vm_malbolge/evidence/):

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
- **Evidencia cruda de las re-medidas de hoy:** [`vm_malbolge/evidence/lt_recheck_2026-10-14.txt`](vm_malbolge/evidence/lt_recheck_2026-10-14.txt) (sha256 `4f41eb03aa61c9dc…`) — salida verbatim del harness sobre las cuatro imágenes, con hash de fichero de trabajo y de blob en cada una. Ahí queda medido además que **la imagen canónica de la bifurcación `vm_malbolge/src/mbir_cmp_lt.mb` sigue en 8/12** (fallan `(0,1)`, `(0,2)`, `(1,2)` → `00` y `(2,2)` → `01`, con paridad entre motores en las cuatro): los 11/12 no viven en el `.hell` de la bifurcación sino en las imágenes de `vm_malbolge/evidence/artifacts/`.
- **Leyes estructurales verificadas** (cada una con su censo o su ejecución, en [`vm_malbolge/LT_STATUS.md`](vm_malbolge/LT_STATUS.md)): ley del veredicto — el dígito impreso es función pura del contenido de la única celda que lee el `ROT` compartido (`0/3/6 → 00/01/02`), F47/F48/F56/F58; techo de tabla — `trit0(A)=0` no puede emitir un trit `0`, F57; escaneo exhaustivo de los 3^10 valores — ninguna celda codifica la tabla `LT` en el instante de decisión, F59; techo de solo-lectura a toda profundidad de pliegue y colapso a constante del mejor encaje, F60/F63; **el comparador nunca se calcula** — ni un pliegue ni una composición de dos reproducen `a+b·LT` sobre los nueve pares con la tabla `_CRAZY` real, F61; lema de instancia de build — seis compiladas seguidas del mismo `.hell` dan seis `.mb` con sha distintos y una única firma de comportamiento (los 503 bytes que distinguen a `lt_f59_cand_C.mb` de la copia de trabajo están todos en la cola `56920..57507`, que nunca es `pc` ni operando de lectura), F62; ley del acumulador separante, F70; el veredicto no viaja en los datos sino en la **paridad de traducción** de la celda de código 58156, y el flag se escribe una sola vez con el mismo `a_in` en los nueve vectores, F71; `(0,1)` y `(2,2)` **son un solo cálculo** — 0 pasos de divergencia de punteros en 79.790 y los 7 pliegues `a`-divergentes caen íntegros en el relleno (0 en región editable), F72.
- **Negativos cuantificados y conservados:** el espacio completo de ediciones de un carácter sobre la base 11/12 es 5.234.616 variantes (cota inferior; ≈3.900 CPU-horas) y **no se ha barrido**; sí están barridas y cerradas las 5.580 ediciones vivo-directas y las 186 ediciones de semilla simple (5.766 variantes, **0 arreglos**), con un único acierto aparente que resultó degenerado — halta en 2 pasos e imprime `00` a los doce vectores, o sea 6/12 — y la palanca global de semilla invertida en bloque (155 variantes matan la máquina, 12 basura, 19 conservan el `01` errado).
- **Redirección del problema abierto:** en las imágenes A y D el vector `(2,2)` **ya imprime el símbolo propio `02`**, así que en esas bases lo que falta es mapear un `2` ya selectivo a `0`, no construir la tabla.

**Lo que NO está demostrado:** `12/12` — **`NOT_DEMONSTRATED`**. No existe imagen que pase los doce vectores; no se ha barrido el espacio completo de una edición ni la pareja de semillas del relleno; la batería del Hallazgo 72 todavía no se ha transferido a las bases A y D; y `CMP_GT` no se ha empezado. El acuerdo entre los dos motores sobre la base 11/12 no demuestra paridad de la familia entera ni cierra la objeción de F71 §10.

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
- El destino del JMP no elige la instrucción, y no hay un contador de programa general.
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

---

## Hito: Quine Clásica Más Pequeña — 54,134 B (BolgeForge)

**La quine Malbolge clásica más pequeña producida y verificada por este ecosistema: 54,134 bytes, 5,718 bytes menos que la quine de referencia de Matthias Lutter (59,852 B).** Sintetizada por **BolgeForge** (subsistema de síntesis del monorepo ISyCo) y verificada byte a byte con **doble motor C independiente**.

| m | Artefacto | Bytes | Δ vs Lutter | SHA-256 |
|---|---|---|---|---|
| **284** | [`quine/quine_54134_m284.mb`](quine/quine_54134_m284.mb) **(récord)** | **54,134** | **−5,718** | `1808fd4d…` |
| 287 | [`quine/ladder/quine_54706_m287.mb`](quine/ladder/quine_54706_m287.mb) | 54,706 | −5,146 | `3da997b9…` |
| 293 | [`quine/ladder/quine_55850_m293.mb`](quine/ladder/quine_55850_m293.mb) | 55,850 | −4,002 | `1719515d…` |
| 308 | [`quine/ladder/quine_58709_m308.mb`](quine/ladder/quine_58709_m308.mb) | 58,709 | −1,143 | `67628cf1…` |

- Las cuatro quines fueron re-verificadas el 2026-10-16: `mb_ref` coincide **byte a byte** (0 diferencias) y el runner C de este repositorio coincide en los **primeros N bytes** (añade un `0x0A` final de convención propia, igual que en los vectores M2); `steps` reportados en stderr (`steps: 62902924 | status: HALTED` para el récord, ~22 min).
- Procedencia: BolgeForge `synthesize_v2.py` — grafo de 26 macros de auto-modificación verificadas puras encadenadas por Dijkstra, generador analítico de constantes y búsqueda runtime de la macro `inc`; bitácora completa en `NOTES.md` del monorepo ISyCo.
- Alrededor de la escalera corre el programa de investigación **REVERSE_SELF_MODIFICATION**: la traza del récord (B0) muestra que 24,009 de 24,090 celdas ejecutadas terminan en `final == X^k(init)` con `X = xlat2` (LCM 3,060), y el demo B1 de 44 bytes imprime un byte **imposible** (0xFD) mediante auto-modificación de una sola celda.
- Detalles completos, protocolo de verificación, mapa técnico de la construcción y límites: [`quine/README.md`](quine/README.md).

> **Alcance del claim (anti-fake):** la comparación es contra la referencia Lutter (59,852 B) y la escalera propia; no hay barrido externo exhaustivo de todas las quines clásicas publicadas. Descenso por debajo de m=284: `NOT_DEMONSTRATED` (piso del stream sintetizado; caminos de rescate en `NOTES.md` §Next steps).

---

## Lo que FALTA por hacer (Roadmap / NOT_DEMONSTRATED)

1. **Control de Flujo Completo en Malbolge VM**
   - JMP, JZ, CALL y la comparación relacional `CMP_EQ` en RAM ya están demostrados en el Hito M2 CF + CMP_EQ (7/7, 56,947 bytes). Sigue faltando un contador de programa general para código arbitrario, usar el destino del JMP como selector dinámico arbitrario, y una pila de llamadas de más de una trama.
2. **Integración Completa del Pipeline de Ejecución (M2 + ALU + CMP)**
   - Sigue sin existir una sola imagen que cargue el programa en RAM y además ejecute la ALU de 14 vectores y el `CMP_EQ`. Una sonda sobre `mbir_alu.hell` (12 banderas y 8 celdas de scratch) no ensambló: el inicializador se quedó sin sitio en la celda 57855. Quince `C1` sueltos sí entraron. Detalle: [`vm_malbolge/M2_FULL_STATUS.md`](vm_malbolge/M2_FULL_STATUS.md).
3. **Pila Dinámica de Profundidad > 2**
   - Para expresiones complejas que requieran evaluar árboles sintácticos de mayor profundidad o direccionamiento indexado.
4. **Operadores de Orden Relacional (`CMP_LT`, `CMP_GT`)**
   - `CMP_LT` ya no es "sin comenzar": está bifurcado, con harness propio de 12 vectores y **11/12 como mejor resultado medido en ambos motores** (sección 5b). Lo que falta es el último vector, y `12/12` sigue **`NOT_DEMONSTRATED`**: las rutas de solo-lectura, de pliegue único/doble y de semilla simple están cerradas por medida (F57, F59-F63, F70-F72), no por opinión.
   - `CMP_GT` (clasificación ternaria del signo de subdesbordamiento para la desigualdad estricta inversa) no se ha empezado.
5. **Frontends que todavía no existen**
   - Pistas `swift/`, `rust/`, `java/`, `c/` marcadas como `NOT_STARTED`.
   - En Python, P5 ya baja la recursión directa a MBIR en el host (sección 12). P6, el lexer dentro de Malbolge, se probó y no quedó demostrado: al volver a `ENTRY` el clasificador de un byte no emite el segundo token, y el runner C no coincide con el oráculo ([`python/P6_STATUS.md`](python/P6_STATUS.md)). P7 (parser) y P8 (`python.mb`) no se empezaron.
6. **Conexión Operacional de los 13 Substratos -bolge**
   - Aunque los 13 substratos están indexados y referenciados, falta conectar adaptadores backend de emisión automática para cada uno.

---

## Pistas de Lenguaje (Language Tracks)

| Lenguaje | Archivo Target | Variante | Estado | Hito más alto | Evidencia |
|---|---|---|---|---|---|
| **Python** | `python.mb` | Unshackled (primario) | `REFERENCE_FRONTEND` | P5 (recursión en el host) | `python/STATUS.md`, `python/evidence/P5/` |
| **Swift** | `swift.mb` | Unshackled (primario) | `NOT_STARTED` | — | — |
| **Rust** | `rust.mb` | Unshackled (primario) | `NOT_STARTED` | — | — |
| **Java** | `java.mb` | Unshackled (primario) | `NOT_STARTED` | — | — |
| **C** | `c.mb` | Unshackled (primario) | `NOT_STARTED` | — | — |

---

## Estructura del Repositorio

```text
MALBOLGE-MB-DATABASE/
├── README.md              ← Este documento (visión general, estado y capacidades)
├── DATABASE.md            ← Mapa de navegación y metadata del laboratorio
├── LICENSE                ← Licencia MIT
├── registry/              ← Registros estructurados (lenguajes, substratos externos, artefactos)
├── docs/                  ← Contrato MBIR, modelo de evidencia, variantes de Malbolge
├── mbir/                  ← Especificación MBIR, suite de pruebas y oráculo en Zig
├── runners/               ← Entornos y runners reproducibles de Malbolge (Classic, Unshackled)
├── third_party/           ← Herramientas externas (compilador LMAO)
├── tools/                 ← Utilidades de pruebas cruzadas y oráculo clásico en Python
├── quine/                 ← Quine clásica récord 54,134 B (BolgeForge): artefacto, escalera y evidencia
├── vm_malbolge/           ← Implementación de la VM en ensamblador HeLL/Malbolge
│   ├── src/               ← Código fuente HeLL y binarios .mb (m2_loader, alu, p2_cmp, a05_lifo...)
│   ├── tools/             ← Generadores de código HeLL y scripts de prueba diferencial
│   ├── evidence/          ← Manifiestos JSON con evidencia firmada y hashes SHA-256
│   ├── M2_LOADER_STATUS.md ← Bitácora técnica y paridad del Hito M2 (Stored-Program Loader & PC)
│   ├── M2_ALU_STATUS.md   ← Bitácora del ALU de programa almacenado (8/8, un solo tiro)
│   ├── ALU_STATUS.md      ← Bitácora técnica y paridad de la ALU Unificada (ADD + SUB)
│   ├── P2_STATUS.md       ← Bitácora técnica y paridad del Hito P2 (CMP_EQ)
│   ├── LT_STATUS.md       ← Bitácora del Hito P2 relacional (CMP_LT): Findings 1-72, mejor 11/12, 12/12 NOT_DEMONSTRATED
│   ├── P1_STATUS.md       ← Bitácora técnica y paridad del Hito P1 (SUB)
│   ├── P0_STATUS.md       ← Bitácora técnica y paridad del Hito P0 (ADD)
│   ├── A05_STATUS.md      ← Bitácora técnica de la Pila LIFO A05b y bucle A05
│   └── A04_STATUS.md      ← Bitácora técnica y registro de paridad del Hito A04
└── python/                ← Pista Python. P5: src/p5_compiler.py y evidence/P5/
```

---

## Cómo Reproducir y Ejecutar

### 1. Verificar el Stored-Program Loader & PC (Hito M2)
Para cargar un programa de bytecode MBIR completo desde STDIN a la memoria RAM de Malbolge y ejecutarlo mediante el Program Counter (`PC`):

```bash
# Vector 1 M2: Carga en RAM y ejecución por PC de PUSH 'A', OUT, HALT -> Emite 'A' (41343 pasos)
echo -ne "\x01\x41\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_m2_loader.mb

# Vector 2 M2: Carga en RAM y ejecución por PC de PUSH 'B', OUT, HALT -> Emite 'B' (41343 pasos)
echo -ne "\x01\x42\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_m2_loader.mb

# Vector 3 M2: HALT inmediato en carga -> Salida vacía (42062 pasos)
echo -ne "\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_m2_loader.mb
```

### 2. Verificar la ALU Unificada: ADD (0x02) y SUB (0x03)
Para ejecutar operaciones aritméticas individuales o secuencias complejas encadenadas en la misma imagen de VM en Malbolge puro:

```bash
# Suma: PUSH 2, PUSH 3, ADD, OUT, HALT -> Emite 0x05 (2 + 3 = 5)
echo -ne "\x01\x02\x01\x03\x02\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_alu.mb | xxd

# Resta: PUSH 4, PUSH 2, SUB, OUT, HALT -> Emite 0x02 (4 - 2 = 2)
echo -ne "\x01\x04\x01\x02\x03\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_alu.mb | xxd

# Expresión encadenada: (1 + 1) - 1 = 1
echo -ne "\x01\x01\x01\x01\x02\x01\x01\x03\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_alu.mb | xxd
```

### 3. Verificar el Kernel de Comparación: CMP_EQ (Hito P2)
Para evaluar igualdad booleana en Malbolge puro desapilando 2 operandos de la pila:

```bash
# Vector 1 P2: 2 == 2 -> Emite 0x01 (true)
echo -ne "\x01\x02\x01\x02\x02\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_p2_cmp.mb | xxd

# Vector 2 P2: 2 == 1 -> Emite 0x00 (false)
echo -ne "\x01\x02\x01\x01\x02\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_p2_cmp.mb | xxd

# Vector 4 P2: 4 == 2 -> Emite 0x00 (false)
echo -ne "\x01\x04\x01\x02\x02\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_p2_cmp.mb | xxd
```

### 4. Verificar la Pila LIFO de 2 Ranuras (Hito A05b)
Para verificar la inversión LIFO y desapilado frente al runner C real:

```bash
# Vector Clave A05b: PUSH 'A', PUSH 'B', OUT, OUT, HALT -> Emite "BA" (4241) en orden LIFO
echo -ne "\x01\x41\x01\x42\x10\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_a05_lifo.mb

# Vector A05b: PUSH 'A', PUSH 'B', OUT, HALT -> Emite "B" (42) del tope de la pila
echo -ne "\x01\x41\x01\x42\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_a05_lifo.mb
```

### 5. Verificar el Bucle Multi-Ciclo Reentrante (Hito A05)
```bash
# Vector Multi-Ciclo: PUSH 'A', OUT, PUSH 'B', OUT, HALT -> Emite "AB" (4142)
echo -ne "\x01\x41\x10\x01\x42\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_a05_multicycle.mb
```

### 6. Ejecutar la Suite de Pruebas de MBIR
```bash
# Validar el encoder/decoder y conformidad de MBIR
python3 -m unittest discover -s mbir/tests

# Validar el oráculo en Zig nativo
./mbir/zig/zig-out/bin/mbir-zig --help
```

### 7. Verificar los frontends Python P3, P4 y P5 (host)
Cada compilador escribe de nuevo su JSON de evidencia. El harness cubre P1, P2, P3, P4 y P5.

```bash
python3 python/src/p3_compiler.py
python3 python/src/p4_compiler.py
python3 python/src/p5_compiler.py
python3 python/tests/test_harness.py
```

### 8. Verificar el Orden Relacional CMP_LT (Hito P2 relacional, mejor 11/12)
El harness corre los 12 vectores (9 pares ordenados + 3 líneas base) en el oráculo Python **y** en el runner
nativo C, y compara salida y número de pasos. Tarda un minuto porque el oráculo es un intérprete en Python.

```bash
# Imagen commiteada de la base 11/12 (Hallazgo 59/62). Sale 0 sólo si se alcanza 12/12.
python3 vm_malbolge/tests/lt_harness.py vm_malbolge/evidence/artifacts/lt_f59_cand_C.mb

# Cualquier otra imagen de la familia: A, B, D y las dos rutas F62 fallan UNA sola entrada distinta.
python3 vm_malbolge/tests/lt_harness.py vm_malbolge/evidence/artifacts/lt_f59_cand_A.mb

# Reconstruir desde el HeLL de una imagen de evidencia (LMAO v0.6.0, modo normal con depuración)
./third_party/lmao/bin/lmao -d -o /tmp/imagen.mb vm_malbolge/evidence/lt_f59_cand_C.hell
```

### 9. Verificar la Quine Clásica Récord (54,134 B)

La quine imprime su propio código fuente byte a byte; la verificación es un `cmp` entre la salida del runner y el archivo. El runner C de este repositorio añade un `0x0A` final de convención propia (igual que en los vectores M2), así que se comparan los primeros N bytes con `cmp -n`.

```bash
# Salida identica en los primeros 54,134 bytes (los pasos van en stderr: steps: 62902924 | status: HALTED)
./runners/malbolge-original/malbolge quine/quine_54134_m284.mb > /tmp/quine.out
cmp -n 54134 /tmp/quine.out quine/quine_54134_m284.mb   # 0 bytes de diferencia

# Escalera completa (m=287, 293, 308): mismo protocolo
for f in quine/ladder/*.mb; do
  ./runners/malbolge-original/malbolge "$f" > /tmp/out.mb 2>/tmp/steps.txt
  cmp -n "$(wc -c < "$f")" /tmp/out.mb "$f" && echo "$f OK"
done
```

La quine tarda ~22 minutos en el runner C de este repositorio (~63M pasos); el oráculo `mb_ref` de BolgeForge la resuelve en ~0.2 s con paridad byte a byte completa. Detalles, hashes y límites: [`quine/README.md`](quine/README.md).

Aviso de hashes (Hallazgo 62): las compilaciones de LMAO **no son deterministas en bytes** — seis builds
sucesivos del mismo `.hell` dan seis `.mb` con sha256 distinto y una única firma de comportamiento, porque la
cola `56904..57507` nunca es `pc` ni operando de lectura. La identidad canónica de una imagen es
`(sha256 del .hell, firma de los 12 vectores, sha256 de la instancia)`, no el sha del `.mb`. Además este
repositorio se maneja con `core.autocrlf=true`: para un artefacto commiteado hay que citar el hash del **blob**
(`git show HEAD:<ruta> | sha256sum`) junto al del fichero de trabajo.

# Malbolge MB Database

Base de datos reproducible y laboratorio de investigación para programas Malbolge sustanciales, runtimes de lenguajes de alto nivel alojados sobre Malbolge, y el middleware **MBIR** (*Malbolge Bytecode Intermediate Representation*) que conecta frontends con substratos de ejecución.

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
| **Contrato MBIR v0** | `DEMONSTRATED` | 18 opcodes congelados | `docs/MBIR_CONTRACT.md`, 23/23 tests `mbir/tests/test_mbir.py` |
| **VM de Referencia MBIR (Python)** | `DEMONSTRATED` | Soporte fib(6), llamadas, saltos, I/O | `mbir/mbir_ref.py`, 28/28 tests `mbir/tests/test_mbir_ref.py` |
| **Oráculo Nativo MBIR (Zig)** | `DEMONSTRATED` | Ejecución MBIR nativa y oráculo diferencial | `mbir/zig/` (`mbir-zig`) |
| **Frontend Python (MalPy)** | `FRONTEND_DEMONSTRATED` | P2 (Python AST → Bytecode MalPy) | `python/src/compiler.py`, suite en `python/tests/` |
| **Toolchain Nativo Linux** | `WORKING` | Ensamblado y ejecución 100% nativa sin Wine | LMAO v0.6.0 (`third_party/lmao/bin/lmao`), Runner C (`runners/malbolge-original/malbolge`) |
| **Malbolge VM Runtime (A04)** | `DEMONSTRATED` | **Bucle de ejecución y pila de 1 profundidad** | `vm_malbolge/src/mbir_a04_gate.hell`, `vm_malbolge/evidence/mbir_a04_gate_smoke.json` (7/7 PASS) |
| **Malbolge VM Bucle Multi-Ciclo (A05)** | `DEMONSTRATED` | **Ejecución secuencial arbitraria sin corrupción ('AB', 'ABC', 'hello')** | `vm_malbolge/src/mbir_a05_multicycle.hell`, `vm_malbolge/evidence/mbir_a05_multicycle_smoke.json` (8/8 PASS) |
| **Malbolge VM Pila LIFO de 2 Ranuras (A05b)** | `DEMONSTRATED` | **Pila LIFO concurrente de 2 ranuras ('BA' invertido)** | `vm_malbolge/src/mbir_a05_lifo.hell`, `vm_malbolge/evidence/mbir_a05_lifo_smoke.json` (7/7 PASS) |
| **Malbolge VM Kernel Aritmético (P0 / ADD)** | `DEMONSTRATED` | **Sumador ternario de 2 operandos desapilados (`0x02`)** | `vm_malbolge/P0_STATUS.md`, `vm_malbolge/evidence/mbir_p0_add_smoke.json` (7/7 PASS) |
| **Malbolge VM Kernel Aritmético (P1 / SUB)** | `DEMONSTRATED` | **Restador ternario de 2 operandos desapilados (`0x02`/`0x03`)** | `vm_malbolge/P1_STATUS.md`, `vm_malbolge/evidence/mbir_p1_sub_smoke.json` (7/7 PASS) |
| **Malbolge VM ALU Unificada (ADD + SUB)** | `DEMONSTRATED` | **ALU completa ejecutando ADD (`0x02`) y SUB (`0x03`) simultáneos** | `vm_malbolge/ALU_STATUS.md`, `vm_malbolge/evidence/mbir_alu_smoke.json` (14/14 PASS) |
| **Malbolge VM Kernel Comparación (P2 / CMP_EQ)** | `DEMONSTRATED` | **Igualdad booleana de 2 operandos desapilados (`0x02`)** | `vm_malbolge/P2_STATUS.md`, `vm_malbolge/evidence/mbir_p2_cmp_smoke.json` (7/7 PASS) |
| **Malbolge VM Stored-Program Loader & PC (M2)** | `DEMONSTRATED` | **Cargador a RAM (`prog_0..3`) y ejecución desacoplada por PC** | `vm_malbolge/M2_LOADER_STATUS.md`, `vm_malbolge/evidence/mbir_m2_loader_smoke.json` (4/4 PASS) |
| **Runtimes Swift, Rust, Java, C** | `NOT_STARTED` | Sin comenzar | Tracks registrados en `registry/languages.json` |

---

## Lo que SÍ hace ya (DEMONSTRATED)

### 1. Bucle de Captura y Ejecución en Malbolge Puro (Hito A04)
Implementado en ensamblador de bajo nivel HeLL ([`vm_malbolge/src/mbir_a04_gate.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/mbir_a04_gate.hell)) a través del generador canónico ([`vm_malbolge/tools/mbir_a04_gate_gen.py`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/tools/mbir_a04_gate_gen.py)):
- **`01 <operand>` (`PUSH_CONST`)**: Ingiere el opcode de stdin, reconoce la instrucción, captura el siguiente byte como operando, lo almacena en la celda dedicada `stack_top` mediante la involución Crazy `C1/C2`, reinicia el acarreo y los flags de desvío, y salta de regreso al bucle principal de despacho.
- **`10` (`OUT_BYTE`)**: Reconoce la instrucción, recupera el byte almacenado en la celda dedicada `stack_top`, lo emite por la salida estándar (`OUT`), reinicia el estado y regresa al bucle principal.
- **`00` (`HALT`)**: Reconoce el byte nulo de terminación y detiene la máquina inmediatamente sin emitir salida.
- **Persistencia entre ciclos**: El operando sobrevive intacto al bucle de despacho hasta que una instrucción posterior lo consume.
- **Paridad bit a bit y conteo de pasos exacto (7/7 PASS)** verificado de forma idéntica en:
  - Oráculo Clásico en Python ([`tools/oracle_classic.py`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/tools/oracle_classic.py))
  - Runner nativo de Malbolge en C ([`runners/malbolge-original/malbolge`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/runners/malbolge-original/malbolge))
  - Oráculo de referencia MBIR en Zig ([`mbir-zig`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/mbir/zig/zig-out/bin/mbir-zig))

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
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_a05_multicycle.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/mbir_a05_multicycle.hell)) a través de ([`vm_malbolge/tools/mbir_a05_multicycle_gen.py`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/tools/mbir_a05_multicycle_gen.py)):
- **Teorema del Reset Universal 3-Crazy**: Se descubrió y verificó exhaustivamente que `crz(C0, crz(C2, crz(C1, X))) == 29524 (C1)` para **TODOS** los 59,049 valores de Malbolge. Permite limpiar y re-inicializar incondicionalmente las celdas de almacenamiento tras cada `OUT_BYTE`.
- **Arquitectura Optimizada**: Eliminación de variables legadas (`tmp1..tmp4`) y comprobación EOF muerta, reduciendo el binario compilado de 52,623 a **40,309 bytes** (ahorrando >12,000 bytes bajo el límite de memoria) y recortando ~20,000 pasos de inicialización.
- **Multiplexación de Flags**: Celdas de datos comparten sólo 3 flags en `.CODE`, respetando la física de Malbolge (un único ciclo de 2 elementos en XLAT2: `F <-> J`).
- **Escalabilidad y Cero Deriva**: 8/8 vectores PASS con paridad bit a bit en el Oráculo Python, Runner C nativo y Zig (`mbir-zig`). Escala a exactamente **+6,046 pasos por iteración** sin deriva de fase, permitiendo secuencias arbitrarias de N caracteres (ej. "AB", "ABC", "hello").

### 3. Pila Concurrente LIFO de 2 Ranuras (Hito A05b)
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_a05_lifo.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/mbir_a05_lifo.hell)) a través del generador canónico ([`vm_malbolge/tools/mbir_a05_lifo_gen.py`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/tools/mbir_a05_lifo_gen.py)):
- **Máquina de Estados de Profundidad de Pila (FSM)**: Mediante dos sitios de flag de código (`SLOT0_FLAG` y `SLOT1_FLAG`), la VM emula dinámicamente un puntero de pila de 2 posiciones:
  - Nivel 0 (vacía): `SLOT0 = Nop, SLOT1 = Nop`
  - Nivel 1 (1 elemento): `SLOT0 = MovD, SLOT1 = Nop` (ocupando Ranura 0: `stack_top`)
  - Nivel 2 (2 elementos concurrentes): `SLOT0 = MovD, SLOT1 = MovD` (Ranura 0 y Ranura 1: `stack_top_1`)
- **Inversión LIFO Genuina**: `PUSH 'A'`, `PUSH 'B'`, `OUT`, `OUT`, `HALT` (`01 41 01 42 10 10 00`) emite **`42 41` ("BA")** en riguroso orden LIFO.
- **Preservación de Estado**: Desapilar el tope deja intacto el elemento de la ranura 0 (`01 41 01 42 10 00` -> `42`).
- **Tamaño de Binario**: 51,877 bytes compilado con LMAO (cómodamente dentro del límite estricto de 59,049 palabras de Malbolge Classic).
- **Paridad 7/7 MATCH** en Zig Oracle, Python Classic Oracle y Runner nativo C (`vm_malbolge/evidence/mbir_a05_lifo_smoke.json`).

### 4. Kernel Aritmético y ALU Unificada (Hitos P0, P1 y ALU)
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_alu.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/mbir_alu.hell)) a través del generador canónico ([`vm_malbolge/tools/mbir_alu_gen.py`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/tools/mbir_alu_gen.py)):
- **Hito P0 (`ADD` 0x02)**: Sumador ternario de 2 operandos desapilados concurrentemente de la pila LIFO, evaluando suma aritmética con acarreo y apilando el resultado en `stack_top` (7/7 PASS, [`vm_malbolge/P0_STATUS.md`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/P0_STATUS.md)).
- **Hito P1 (`SUB` 0x03)**: Restador ternario de 2 operandos desapilados (`a - b`), evaluando resta con detección de subdesbordamiento (7/7 PASS, [`vm_malbolge/P1_STATUS.md`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/P1_STATUS.md)).
- **ALU Unificada**: Cohabitación simultánea de `ADD` (0x02) y `SUB` (0x03) en la misma imagen ejecutable binaria ([`vm_malbolge/src/mbir_alu.mb`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/mbir_alu.mb)), pesando **54,691 bytes** (dejando 4,358 bytes de margen bajo el límite de 59,049 palabras).
- **Despacho Secuencial de 5 Opcodes**: Clasificación unificada para `HALT` (0x00), `PUSH_CONST` (0x01), `ADD` (0x02), `SUB` (0x03) y `OUT_BYTE` (0x10).
- **Expresiones Aritméticas Encadenadas**: Soporte verificado para secuencias continuas como `(1 + 1) - 1 = 1`, `(1 + 1) - 2 = 0` y `(2 - 1) + 1 = 2`.
- **Paridad 14/14 PASS**: Paridad diferencial bit a bit ciclo por ciclo entre el runner de C nativo y el oráculo Python ([`vm_malbolge/evidence/mbir_alu_smoke.json`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/evidence/mbir_alu_smoke.json)).

### 5. Kernel de Comparación Lógica: CMP_EQ (Hito P2)
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_p2_cmp.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/mbir_p2_cmp.hell)) a través de ([`vm_malbolge/tools/mbir_p2_cmp_gen.py`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/tools/mbir_p2_cmp_gen.py)):
- **Evaluación Booleana de 2 Fases**: Desapila `op2 = b` de la ranura 1 y `op1 = a` de la ranura 0, evalúa igualdad binaria exacta (`a == b -> 1`, `a != b -> 0`) y apila el resultado booleano de 1 byte en la ranura 0 mientras restablece la ranura 1 a vacía.
- **Propiedades de Igualdad Verificadas**:
  - Reflexividad / Auto-igualdad: `2 == 2 -> 1` (`01`)
  - Desigualdad de predecesor: `2 == 1 -> 0` (`00`)
  - Desigualdad con cero: `2 == 0 -> 0` (`00`)
  - Desigualdad multi-unidad: `4 == 2 -> 0` (`00`)
- **Tamaño de Binario y Margen**: **57,511 bytes** (< 59,049 con 1,538 bytes de margen) usando exactamente 6 flags de código reutilizados sin flags espurios.
- **Paridad 7/7 PASS**: 100% coincidencia bit a bit ciclo por ciclo contra el runner C nativo y oráculo Python ([`vm_malbolge/evidence/mbir_p2_cmp_smoke.json`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/evidence/mbir_p2_cmp_smoke.json), [`vm_malbolge/P2_STATUS.md`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/P2_STATUS.md)).

### 6. Stored-Program Loader y Ejecución Desacoplada por PC (Hito M2)
Implementado en ensamblador HeLL ([`vm_malbolge/src/mbir_m2_loader.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/mbir_m2_loader.hell)) a través de ([`vm_malbolge/tools/mbir_m2_loader_gen.py`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/tools/mbir_m2_loader_gen.py)):
- **Celdas de RAM en Memoria (`prog_0..prog_3`)**: Los bytes del programa se leen primero de STDIN durante una fase dedicada de carga y se comprometen en celdas de RAM independientes usando el teorema de escritura Crazy dual incondicional: `crz(crz(B, C1), C1)`.
- **Desacoplamiento Total de Ejecución por PC**: STDIN se consume completamente hasta el delimitador de carga. Finalizada la carga, el Program Counter (`PC`) asume el control del despacho, leyendo secuencialmente los opcodes de la memoria RAM para gobernar la máquina de pila.
- **Extracción de Operandos Inmediatos Doble-C2**: Los operandos embebidos en el flujo de instrucciones se recuperan de las celdas de memoria de forma no destructiva aplicando la identidad conjugada ternaria: `crz(C2, crz(C2, cell)) == B (mod 256)`.
- **Tamaño de Binario y Eficiencia**: **40,309 bytes** (< 59,049 con un margen holgado de **18,740 bytes**).
- **Paridad 4/4 PASS**: 100% coincidencia bit a bit ciclo por ciclo frente al runner C nativo y el oráculo Python ([`vm_malbolge/evidence/mbir_m2_loader_smoke.json`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/evidence/mbir_m2_loader_smoke.json), [`vm_malbolge/M2_LOADER_STATUS.md`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/M2_LOADER_STATUS.md)).

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

### 7. Tabla de Clasificación de los 18 Opcodes de MBIR
- Generador mecánico ([`vm_malbolge/tools/mbir_dispatch_gen.py`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/tools/mbir_dispatch_gen.py)) que produce ensamblador HeLL para clasificar los 18 opcodes (`0x00`..`0x11`) en Malbolge puro usando cadenas de decremento digital root y sitios `SUBROUTINE_FLAGn` con paridad 21/21 verificada.

### 8. Primitivas Celulares y de Entrada Secuencial Demostradas
- Sonda de segunda lectura explícita con retorno `MOVED` ([`vm_malbolge/src/cell_stack_second_read.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/cell_stack_second_read.hell), 12/12 PASS).
- Bucle de entrada reutilizable hasta 16 bytes con parada en EOF ([`vm_malbolge/src/cell_stack_loop_echo.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/cell_stack_loop_echo.hell), 8/8 PASS).
- Almacenamiento y recuperación mediante celdas dedicadas `stack_scratch` / `stack_top` independientes.

### 9. Herramientas y Substratos Externos
- Binarios nativos compilados para Linux (LMAO, runner clásico, zig-oracle), eliminando dependencia de emulación Wine.
- Registro consolidado de 13 motores externos de la familia `-bolge` en [`registry/substrates.json`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/registry/substrates.json) (Rustbolge, Swiftbolge, Javolge, Fortranbolge, Cobolge, Zigbolge, Pibolge, Pibolge19, Wasmbolge, MalbolgeEngineCPP, malbolge-free, malbolge-oracle, MalboGost).

---

## Lo que FALTA por hacer (Roadmap / NOT_DEMONSTRATED)

1. **Control de Flujo Completo en Malbolge VM**
   - Las cinco formas fijas de JMP, JZ y CALL ya están en el Hito M2 CF (5/5, 55,819 bytes). Sigue faltando un contador de programa general, usar el destino del JMP como selector, y una pila de llamadas de más de una trama.
2. **Integración Completa del Pipeline de Ejecución (M2 + ALU + CMP)**
   - El Hito M2 ALU ya cubre un solo `ADD` o `SUB` cargado en RAM, con operandos en `{0,1,2,3,4}` (8/8, 56,361 bytes). Sigue faltando una sola imagen que cargue el programa y ejecute la ALU de 14 vectores (con cadenas) y el `CMP_EQ` del Hito P2, bajo el límite de 59,049. Esa imagen M2 ALU ya rechazó 15 celdas extra en el presupuesto de inicialización.
3. **Pila Dinámica de Profundidad > 2**
   - Para expresiones complejas que requieran evaluar árboles sintácticos de mayor profundidad o direccionamiento indexado.
4. **Operadores de Orden Relacional (`CMP_LT`, `CMP_GT`)**
   - Clasificación ternaria del signo de subdesbordamiento para comparaciones por desigualdad estricta.
5. **Frontends de Otros Lenguajes**
   - Pistas `swift/`, `rust/`, `java/`, `c/` marcadas como `NOT_STARTED`.
   - En la pista `python/`: P3 (variables y control de flujo en MalPy), P4 (funciones), P5 (recursión), P6 (lexer autónomo en Malbolge).
6. **Conexión Operacional de los 13 Substratos -bolge**
   - Aunque los 13 substratos están indexados y referenciados, falta conectar adaptadores backend de emisión automática para cada uno.

---

## Pistas de Lenguaje (Language Tracks)

| Lenguaje | Archivo Target | Variante | Estado | Hito más alto | Evidencia |
|---|---|---|---|---|---|
| **Python** | `python.mb` | Unshackled (primario) | `REFERENCE_FRONTEND` + `A04_RUNNER_DEMONSTRATED` | P2 (Frontend) / A04 (Runtime) | `python/STATUS.md`, `vm_malbolge/A04_STATUS.md` |
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
├── vm_malbolge/           ← Implementación de la VM en ensamblador HeLL/Malbolge
│   ├── src/               ← Código fuente HeLL y binarios .mb (m2_loader, alu, p2_cmp, a05_lifo...)
│   ├── tools/             ← Generadores de código HeLL y scripts de prueba diferencial
│   ├── evidence/          ← Manifiestos JSON con evidencia firmada y hashes SHA-256
│   ├── M2_LOADER_STATUS.md ← Bitácora técnica y paridad del Hito M2 (Stored-Program Loader & PC)
│   ├── M2_ALU_STATUS.md   ← Bitácora del ALU de programa almacenado (8/8, un solo tiro)
│   ├── ALU_STATUS.md      ← Bitácora técnica y paridad de la ALU Unificada (ADD + SUB)
│   ├── P2_STATUS.md       ← Bitácora técnica y paridad del Hito P2 (CMP_EQ)
│   ├── P1_STATUS.md       ← Bitácora técnica y paridad del Hito P1 (SUB)
│   ├── P0_STATUS.md       ← Bitácora técnica y paridad del Hito P0 (ADD)
│   ├── A05_STATUS.md      ← Bitácora técnica de la Pila LIFO A05b y bucle A05
│   └── A04_STATUS.md      ← Bitácora técnica y registro de paridad del Hito A04
└── python/                ← Pista Python -> MalPy -> MBIR
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

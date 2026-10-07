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
| **Malbolge VM Pila Concurrente / ADD (A05b/P0)** | `NOT_DEMONSTRATED` | En diseño | Pila concurrente multicelda y suma aritmética |
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

### 3. Tabla de Clasificación de los 18 Opcodes de MBIR
- Generador mecánico ([`vm_malbolge/tools/mbir_dispatch_gen.py`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/tools/mbir_dispatch_gen.py)) que produce ensamblador HeLL para clasificar los 18 opcodes (`0x00`..`0x11`) en Malbolge puro usando cadenas de decremento digital root y sitios `SUBROUTINE_FLAGn` con paridad 21/21 verificada.

### 4. Primitivas Celulares y de Entrada Secuencial Demostradas
- Sonda de segunda lectura explícita con retorno `MOVED` ([`vm_malbolge/src/cell_stack_second_read.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/cell_stack_second_read.hell), 12/12 PASS).
- Bucle de entrada reutilizable hasta 16 bytes con parada en EOF ([`vm_malbolge/src/cell_stack_loop_echo.hell`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/vm_malbolge/src/cell_stack_loop_echo.hell), 8/8 PASS).
- Almacenamiento y recuperación mediante celdas dedicadas `stack_scratch` / `stack_top` independientes.

### 5. Herramientas y Substratos Externos
- Binarios nativos compilados para Linux (LMAO, runner clásico, zig-oracle), eliminando dependencia de emulación Wine.
- Registro consolidado de 13 motores externos de la familia `-bolge` en [`registry/substrates.json`](file:///home/danny/Development/ISyCo%20Git/MALBOLGE-MB-DATABASE/registry/substrates.json) (Rustbolge, Swiftbolge, Javolge, Fortranbolge, Cobolge, Zigbolge, Pibolge, Pibolge19, Wasmbolge, MalbolgeEngineCPP, malbolge-free, malbolge-oracle, MalboGost).

---

## Lo que FALTA por hacer (Roadmap / NOT_DEMONSTRATED)

1. **Hito A05b: Pila Concurrente Multicelda (Profundidad > 1)**
   - El soporte multi-ciclo permite N operaciones secuenciales `PUSH -> OUT`, pero almacenar múltiples elementos simultáneamente antes de hacer pop (`01 41 01 42 10 10 00` -> `BA`) requiere un puntero de pila sobre slots de memoria indexados.
2. **Operaciones Aritméticas y Lógicas en Malbolge Puro**
   - Implementar los manejadores operacionales para `ADD` (0x02) y `SUB` (0x03) en la VM HeLL/Malbolge reutilizando los patrones de sumador y acarreo ternario.
3. **Cargador de Programa Completo desde Stdin**
   - Actualmente las instrucciones se procesan en streaming directo desde stdin. Falta el cargador que lea N bytes de un binario MBIR completo a un array de memoria en Malbolge antes de transferir el control al contador de programa (`PC`).
4. **Control de Flujo en Malbolge VM**
   - Soporte para saltos (`JMP`, `JZ`, `JNZ`) y llamadas a subrutinas (`CALL`, `RET`) interpretando el bytecode desde el array de memoria.
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
│   ├── src/               ← Código fuente HeLL (incluyendo mbir_a04_gate.hell)
│   ├── tools/             ← Generadores de sondas y oráculo diferencial (mbir_a04_gate_gen.py)
│   ├── evidence/          ← Manifiestos JSON con evidencia firmada y hashes SHA-256
│   └── A04_STATUS.md      ← Bitácora técnica y registro de paridad del Hito A04
└── python/                ← Pista Python -> MalPy -> MBIR
```

---

## Cómo Reproducir y Ejecutar

### 1. Verificar el Oráculo Diferencial de A04
Para compilar la sonda HeLL y ejecutar los vectores de prueba frente al oráculo Zig, el oráculo Python y el runner C real:

```bash
# Vector 1: PUSH_CONST 'A', OUT_BYTE, HALT -> Emite 'A' (61,199 pasos)
python3 vm_malbolge/tools/mbir_zig_oracle.py \
  --hell vm_malbolge/src/mbir_a04_gate.hell \
  --mbir-hex 01411000

# Vector 2: PUSH_CONST 'B', OUT_BYTE, HALT -> Emite 'B' (61,199 pasos)
python3 vm_malbolge/tools/mbir_zig_oracle.py \
  --hell vm_malbolge/src/mbir_a04_gate.hell \
  --mbir-hex 01421000

# Vector 3: HALT directo -> Salida vacía (55,194 pasos)
python3 vm_malbolge/tools/mbir_zig_oracle.py \
  --hell vm_malbolge/src/mbir_a04_gate.hell \
  --mbir-hex 00

# Vector 4: PUSH_CONST 'A', HALT (sin OUT_BYTE) -> Salida vacía (58,964 pasos)
python3 vm_malbolge/tools/mbir_zig_oracle.py \
  --hell vm_malbolge/src/mbir_a04_gate.hell \
  --mbir-hex 014100
```

### 2. Ejecutar la Suite de Pruebas de MBIR
```bash
# Validar el encoder/decoder y conformidad de MBIR
python3 -m unittest discover -s mbir/tests

# Validar el oráculo en Zig nativo
./mbir/zig/zig-out/bin/mbir-zig --help
```

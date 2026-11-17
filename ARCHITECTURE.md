# Arquitectura del laboratorio

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
├── quine/                 ← Quine clásica récord 53,562 B (BolgeForge): artefacto, escalera y evidencia
├── vm_malbolge/           ← Implementación de la VM en ensamblador HeLL/Malbolge
│   ├── src/               ← Código fuente HeLL y binarios .mb (m2_loader, alu, p2_cmp, a05_lifo...)
│   ├── tools/             ← Generadores de código HeLL y scripts de prueba diferencial
│   ├── evidence/          ← Manifiestos JSON con evidencia firmada y hashes SHA-256
│   ├── M2_LOADER_STATUS.md ← Bitácora técnica y paridad del Hito M2 (Stored-Program Loader & PC)
│   ├── M2_ALU_STATUS.md   ← Bitácora del ALU de programa almacenado (8/8, un solo tiro)
│   ├── ALU_STATUS.md      ← Bitácora técnica y paridad de la ALU Unificada (ADD + SUB)
│   ├── P2_STATUS.md       ← Bitácora técnica y paridad del Hito P2 (CMP_EQ)
│   ├── LT_STATUS.md       ← Bitácora del Hito P2 relacional (CMP_LT): Findings 1-73 + §11, 12/12 DEMONSTRATED
│   ├── GT_STATUS.md       ← Bitácora del Hito P2 relacional inverso (CMP_GT): Finding 75, 12/12 DEMONSTRATED
│   ├── P1_STATUS.md       ← Bitácora técnica y paridad del Hito P1 (SUB)
│   ├── P0_STATUS.md       ← Bitácora técnica y paridad del Hito P0 (ADD)
│   ├── A05_STATUS.md      ← Bitácora técnica de la Pila LIFO A05b y bucle A05
│   └── A04_STATUS.md      ← Bitácora técnica y registro de paridad del Hito A04
└── python/                ← Pista Python. P5: src/p5_compiler.py y evidence/P5/
```

---

## Anexo: Análisis de arquitectura de dos sistemas (extractor + PureEpoch como middleware)

Se propuso una arquitectura de dos componentes: un sistema A que extraiga un valor de una celda de Malbolge, un sistema B (PureEpoch) que lo "busque" y lo devuelva, y el sistema A que vuelva a meter el valor conocido en una celda.

**Descartado** (conclusión original; conservada como registro histórico). El bloqueante no está en encontrar el valor, sino en la inexistencia de la instrucción `mem[d] = valor_conocido` en Malbolge Classic. Incluso con un sistema externo que encuentre el valor, no hay instrucción Malbolge para escribirlo en una celda de datos. PureEpoch puede precomputar transiciones de estado para valores conocidos en tiempo de compilación (rearme de instrucciones automutadas), pero no puede actuar como middleware que escriba valores decididos en runtime. Documentado en [`vm_malbolge/evidence/dos_sistemas_middleware_analisis.md`](vm_malbolge/evidence/dos_sistemas_middleware_analisis.md).

**Corrección medida (2026-11-07): la causa raíz queda refutada.** La escritura de un
valor exacto en runtime **sí** existe: con la máscara imprimible `121` (involución de
`crazy` para todo valor de byte) la secuencia `mem[scratch] = crazy(V,121)` y
`mem[destino] = crazy(mem[scratch],121) = V` escribe un valor arbitrario recibido por
`stdin` en una celda arbitraria — 768 escrituras medidas (256 payloads × 3 épocas), **0
discrepancias** — y con ese puntero se salta a la celda elegida en runtime
(36/130/224). Evidencia: [`vm_malbolge/evidence/epoch_algebra_v3/`](vm_malbolge/evidence/epoch_algebra_v3/).
Lo que sigue abierto es la **búsqueda** de la transición (no hay síntesis general), no
la escritura.

# Malbolge MB Database v2.0 — Base de Datos Reproducible y Laboratorio MBIR

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/DannyBaanks/Malbolge-MB-Database)
[![Quine Record](https://img.shields.io/badge/record-53562%20bytes%20quine-brightgreen.svg)]()
[![MBIR](https://img.shields.io/badge/IR-MBIR%20v0%20(18%20opcodes)-blueviolet.svg)]()

Base de datos reproducible y laboratorio de investigación para programas Malbolge sustanciales, runtimes de lenguajes de alto nivel alojados sobre Malbolge, y el middleware **MBIR** (*Malbolge Bytecode Intermediate Representation*) que conecta frontends con substratos de ejecución.

Núcleo de almacenamiento y catálogo de la **Suite de Datos y Runtimes v2.0** del ecosistema Malbolge de ISyCo.

> **Récord vigente (2026-10-17): quine clásica de 53,562 bytes** — la quine más pequeña producida y verificada por este ecosistema, **6,290 bytes menor** que la quine de referencia de Matthias Lutter (59,852 B). Sintetizada por **BolgeForge**, verificada byte a byte con triple motor C independiente. Detalles, hashes y reproducción: [`quine/README.md`](quine/README.md).

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
| **Quine Clásica (BolgeForge)** | `DEMONSTRATED` | **Quine de 53,562 B que imprime su propia fuente (récord: −6,290 B vs la referencia Lutter de 59,852 B)** | [`quine/quine_53562_m281.mb`](quine/quine_53562_m281.mb), [`quine/evidence/quine_53562_verification.json`](quine/evidence/quine_53562_verification.json) |
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
| **Malbolge VM Nativo sin LMAO (M2 Native)** | `DEMONSTRATED` | **Primera imagen Classic emitida sin LMAO: 2 rutas (`ADD`→`5`, `CMP_EQ`→`1`) despachadas por clave aritmética, loader estricto ACCEPT en 3 motores** | `vm_malbolge/M2_NATIVE_STATUS.md`, `vm_malbolge/evidence/native_2routes_build.json` |
| **Malbolge VM Nativo 3 rutas (M2 Native)** | `DEMONSTRATED` | **Una imagen sin LMAO con `ADD` + `CMP_EQ` + `CMP_LT` (gaps de 27 celdas), 3/3 PASS en oráculo, runner C y loader estricto** | `vm_malbolge/M2_NATIVE_STATUS.md`, `vm_malbolge/evidence/native_3routes_build.json` |
| **Comparador relacional dominio decimal (M2 Native)** | `DEMONSTRATED` | **`CMP_LT(d, 5)` para los diez dígitos `0..9` en una sola imagen: sale de `{0,1,2}`, 10/10 PASS en 3 motores** | `vm_malbolge/M2_NATIVE_STATUS.md`, `vm_malbolge/evidence/native_cmp_decimal_build.json` |
| **Límite del cargador almacenado (semántica)** | `DEMONSTRATED` (negativo) | **El puntero de datos avanza +1 por instrucción, pero ningún opcode escribe un valor arbitrario: el cargador byte-exacto no es expresable como receta fija** | `vm_malbolge/evidence/native_probe_d.json` |
| **Malbolge VM ALU de programa almacenado (M2 ALU)** | `DEMONSTRATED` | **Un programa de 7 bytes cargado y un único `ADD`/`SUB` (8/8, un solo tiro)** | `vm_malbolge/M2_ALU_STATUS.md`, `vm_malbolge/evidence/mbir_m2_alu_smoke.json` |
| **Malbolge VM Salto/Condicional/Llamada en RAM (M2 CF)** | `DEMONSTRATED` | **Cinco formas fijas de `JMP`/`JZ`/`CALL` sobre bytecode cargado (5/5)** | `vm_malbolge/M2_CF_STATUS.md`, `vm_malbolge/evidence/mbir_m2_cf_smoke.json` |
| **Malbolge VM Control Flow + Relacional (M2 CF + CMP_EQ)** | `DEMONSTRATED` | **Siete formas de `JMP`/`JZ`/`CALL`/`CMP_EQ` en memoria con paridad dual (7/7)** | `vm_malbolge/M2_CF_CMP_STATUS.md`, `vm_malbolge/evidence/mbir_m2_cf_cmp_smoke.json` (7/7 PASS) |
| **PureEpoch Suite (M1..M3, Torus, Boss 1..3)** | `DEMONSTRATED` | **12 artefactos: bucle autónomo `while x > 0` sin trucos de host, máquina de Turing, cascada bizantina, préstamo toroidal y checkpoints in-band** | [`pureepoch/README.md`](pureepoch/README.md), 18/18 tests [`pureepoch/tests/test_pureepoch.py`](pureepoch/tests/test_pureepoch.py) |
| **Oráculo Classic: parada en EOF** | `DEMONSTRATED` | **El oráculo para en EOF igual que el runner C (`stop_on_eof`). Sin ese arreglo, todo programa con bucle de fetch diverge: el oráculo seguía con `a=59048` y emitía `ff` hasta el límite de pasos** | [`tools/oracle_classic.py`](tools/oracle_classic.py), [`vm_malbolge/evidence/BUG_ORACULO_EOF.md`](vm_malbolge/evidence/BUG_ORACULO_EOF.md) |
| **Andamio iterante en el corpus (frentes 3 y 5)** | `DEMONSTRATED` | **El bloqueante "no existe imagen Classic que itere sobre flujo" queda refutado: `cat_compact.mal` (7.596 celdas) verificado en los motores de este repo, y `example_simple_cat.hell` ensamblado y commiteado** | [`vm_malbolge/evidence/frentes3y5_bloqueante_CORRECCION.md`](vm_malbolge/evidence/frentes3y5_bloqueante_CORRECCION.md), [`vm_malbolge/src/simple_cat_lmao.mb`](vm_malbolge/src/simple_cat_lmao.mb) |
| **Bucle de fetch nativo con estado entre bytes** | `DEMONSTRATED` | **Vuelta real que regresa al mismo despacho con una celda de estado que sobrevive a todos los bytes leídos: 9/9 acuerdo byte a byte y 4.096 bytes aleatorios exactos en oráculo y runner C** | [`vm_malbolge/src/mbir_native_fold_loop.mb`](vm_malbolge/src/mbir_native_fold_loop.mb), [`vm_malbolge/evidence/native_fold_loop.md`](vm_malbolge/evidence/native_fold_loop.md) |
| **Pila LIFO de 2 ranuras (one-shot, sin LMAO)** | `DEMONSTRATED` | **Dos bytes almacenados en dos celdas y emitidos en orden inverso (`AB`→`6368`, `BA`→`6769`): 8/8 y loader estricto completo** | [`vm_malbolge/src/mbir_stack2_oneshot.mb`](vm_malbolge/src/mbir_stack2_oneshot.mb), [`vm_malbolge/evidence/stack2_oneshot.md`](vm_malbolge/evidence/stack2_oneshot.md) |
| **Despacho computado por el dato** | `DEMONSTRATED` | **Máquina de bytecode que enruta por opcode con un salto computado: `mem[P] = crazy(opcode, V)` es la dirección. `01 41 F2`→`68` (el POP emite lo que el PUSH guardó). 8/8 casos y 111/111 combinaciones de barrido** | [`vm_malbolge/src/mbir_dispatch2.mb`](vm_malbolge/src/mbir_dispatch2.mb), [`vm_malbolge/evidence/dispatch2.md`](vm_malbolge/evidence/dispatch2.md) |
| **Bytecode de N instrucciones encadenadas** | `DEMONSTRATED` | **El programa vive en el flujo: 3 instrucciones de longitud variable (`PUSH 0x35 operando`, `POP 0x41`) encadenadas por tres despachos, 9/9 en oráculo y runner C. La ventana de ~284 celdas no era el límite: con empaquetado exacto y protocolo libre se llega a N=4 y N=5 sin rotaciones (fila siguiente)** | [`vm_malbolge/src/mbir_dispatchN.mb`](vm_malbolge/src/mbir_dispatchN.mb), [`vm_malbolge/evidence/dispatchN.md`](vm_malbolge/evidence/dispatchN.md) |
| **Empaquetado exacto: N=4 y N=5 sin rotaciones** | `DEMONSTRATED` | **Dos imágenes con coste de rotación cero: N=4 con el protocolo original y colas `7,1,4,10`; N=5 con `PUSH 0xff`/`POP 0x35` (bandas adyacentes, ventana total 486 celdas) y colas `1,2,5,6,9`. 9/9 cada una en oráculo y runner C. El bloque real (destino incluido) es `6+t` (push) / `5+t` (pop) y el único choque de punteros es `t_j = t_i + 2`** | [`vm_malbolge/src/mbir_dispatch4_pack.mb`](vm_malbolge/src/mbir_dispatch4_pack.mb), [`vm_malbolge/src/mbir_dispatch5.mb`](vm_malbolge/src/mbir_dispatch5.mb), [`vm_malbolge/evidence/dispatch_pack.md`](vm_malbolge/evidence/dispatch_pack.md) |
| **Celda-puntero escrita en runtime (salida del bloqueante de la pila)** | `DEMONSTRATED` | **Una celda sembrada con `v0` se transforma con `CRAZY` durante la ejecución y un `MOVD` posterior la usa como dirección: salida `f0`; el control con `CRAZY→NOP` sigue otra ruta y emite `d4`. 9/9 variantes en oráculo y runner C, loader estricto completo** | [`vm_malbolge/src/mbir_pointer_cell_rt.mb`](vm_malbolge/src/mbir_pointer_cell_rt.mb), [`vm_malbolge/evidence/pointer_cell_rt.md`](vm_malbolge/evidence/pointer_cell_rt.md) |
| **Bucle de pila por fases: escritura y lectura de la misma celda** | `DEMONSTRATED` | **La celda `W` no se restaura: avanza por su ciclo de `XLAT2` y decodifica `CRAZY` en la iteración 0 (escritura) y `ROT` en la 1 (lectura) sobre la misma celda `S`, repitiendo cada 9. Sin celda-puntero de fase ni colisión de pares. 8/8 positivo y 8/8 control (W inerte), 4096 bytes aleatorios incluidos** | [`vm_malbolge/src/mbir_stack_loop_phase.mb`](vm_malbolge/src/mbir_stack_loop_phase.mb), [`vm_malbolge/evidence/stack_loop_phase.md`](vm_malbolge/evidence/stack_loop_phase.md) |
| **Pila LIFO de profundidad 2 en bucle real (fases por ciclo de cifrado)** | `DEMONSTRATED` | **Dos ranuras y orden LIFO dentro de un bucle: push `S1` (fase 0), push `S2` (fase 3), pop `S2` (fase 4), pop `S1` (fase 5). Las fases las elige el ciclo de `XLAT2` de cada celda de trabajo (`W1`@71 = `CRAZY`@0/`ROT`@5, `W2`@83 = `CRAZY`@3/`ROT`@4); ninguna se restaura. 8/8 positivo y 8/8 control (células inertes), 2048 bytes aleatorios incluidos** | [`vm_malbolge/src/mbir_stack_loop_lifo2.mb`](vm_malbolge/src/mbir_stack_loop_lifo2.mb), [`vm_malbolge/evidence/stack_loop_lifo2.md`](vm_malbolge/evidence/stack_loop_lifo2.md) |
| **Línea de épocas (v1): selector de dos rutas reutilizable** | `CONDITIONAL_PASS` | **Una imagen Classic atiende solicitudes `01`/`02`, selecciona la ruta en runtime, rearma el marcador de la ruta con diez `ROT` y vuelve al mismo `IN`: 9 flujos + 128 solicitudes pseudoaleatorias, oráculo y runner C byte a byte** | [`vm_malbolge/evidence/epoch_selector_reusable_v1/`](vm_malbolge/evidence/epoch_selector_reusable_v1/), [`epoch_selector_store_v1/`](vm_malbolge/evidence/epoch_selector_store_v1/) (selector + almacén exacto rearmable) |
| **Línea de épocas (v2): journal con selección por estado** | `CONDITIONAL_PASS` | **Journal M1b de PureEpoch adaptado (`SAVE → clobber → 10×ROT → RESTORE`) con la ruta elegida por el estado de fase (`EPOCH_PHASE`): 9 flujos + 128 solicitudes y 3 controles negativos (journal, restore, fase)** | [`vm_malbolge/evidence/epoch_journal_state_v2/`](vm_malbolge/evidence/epoch_journal_state_v2/) |
| **Línea de épocas (v3): resolvedor algebraico de épocas en runtime** | `PASS` | **La petición por `stdin` elige la celda de época (36/130/224, 94 de separación, mismo residuo), se escribe el valor **exacto** con la involución de `crazy` (máscara imprimible `121`) y se salta a esa celda para ejecutarla: 768 escrituras exactas (256 payloads × 3 épocas, 0 discrepancias), 18 pasos, 3 motores, 5 controles negativos** | [`vm_malbolge/evidence/epoch_algebra_v3/`](vm_malbolge/evidence/epoch_algebra_v3/) |
| **Alcanzabilidad de palabras (torus_reach_v1)** | `PASS` | **La "dependencia circular" exacta: `D(crazy(a,v)) ⊆ D(a) U D(v)` (un trit 2 no se crea donde ningún operando lo tiene), probada enumerando los 9 pares de trits + 200k palabras. La salida existe: el acumulador es fuente independiente de 2s y `ROT` los recoloca. Testigos con replay independiente: `29524 = crazy(54,54)` (3 ops, `54` imprimible), `0 = crazy(29524,29524)`, inducciones `Q`/`U`/`F` sobre los 1023 subconjuntos, fórmula general (209 palabras, 0 fallos) y **`59048` (diez 2s) por tres rutas** (constructivo 1038 ops, compacto 7, fiel a la VM 11). `{0,29524}` es la única componente cerrada (operador restringido); el cierre hacia atrás de `29524` cubre las 59049 palabras. Relleno de memoria medido en 5 direcciones con 3 motores: crazy-fill, no cero. Upgrade de máscara: `121` involutivo en 7776/59049 palabras, `29524` en todas. 6 mutantes rechazados** | [`vm_malbolge/evidence/torus_reach_v1/`](vm_malbolge/evidence/torus_reach_v1/) |
| **Construcción nativa autónoma de 29524 y 59048 (epoch_mask_native_v1)** | `PASS` | **`a` arranca en 0 y `DLOAD` no toca `a`: el primer `CRAZY` con `a=0` sobre una celda imprimible sin trit 2 (`36 = 1100_3`) escribe **`29524`** en memoria; diez bloques desenrollados `[DLOAD, ROT, CRAZY]` añaden un trit 2 por `ROT` de la celda `54` y dejan **`59048 = 29524 + (3^0+…+3^9)`** (`OUT = 0xa8`, 34 pasos, HALTED). Sin stdin, sin bucles ni saltos, 43 bytes imprimibles. La instancia `bootstrap_only` deja la celda con `29524` (`OUT = 0x54`): la única máscara involutiva de palabra completa queda disponible en memoria. 3 motores byte a byte en 6 instancias, 4 controles negativos divergen** | [`vm_malbolge/evidence/epoch_mask_native_v1/`](vm_malbolge/evidence/epoch_mask_native_v1/) |
| **Payload de 10 trits con máscara fabricada (epoch_resolver_word_v1)** | `PASS` | **Con la máscara `29524` fabricada en runtime (en lugar de la imprimible `121`, que sólo cubría 7776/59049 palabras) la escritura exacta cubre **cualquier palabra de 10 trits**: el resolvedor escribe `V = 29797` (trits 2 en las posiciones 1, 3 y 5 — la 5 fuera del alcance de `121`) **exacto** en la celda de época y la ejecuta (`OUT = 0x65` en `pc = T = 100`, `END` en `T+1`, 277 pasos). El puntero de petición se escribe exacto desde el byte de stdin (`W = 99`). Payload construido en memoria desde 29524 añadiendo un trit 2 por posición con `rot^r(54)`. Dos instancias legítimas (salto estático y salto por puntero de runtime) verifican igual; dos controles negativos (`121` → la escritura **falla**; payload sin el trit de la posición 5 → otro opcode). Tres motores Python coinciden. Divergencia medida y acotada del runner C en la fase final, documentada** | [`vm_malbolge/evidence/epoch_resolver_word_v1/`](vm_malbolge/evidence/epoch_resolver_word_v1/) |
| **Guarda de imprimibilidad del runner C (c_printable_guard_v1)** | `PASS` | **Causa raíz de la divergencia del runner C en `epoch_resolver_word_v1`: `vm_run` comprueba `mem[pc] ∈ 33..126` **antes de decodificar** y termina si no lo es (`1cd4`–`1cda` → `HALT`), mientras el intérprete canónico ejecuta cualquier valor y sólo condiciona a la imprimibilidad el cifrado posterior. Programas mínimos de 44 celdas con una sola forma aterrizan en `pc = 41` con `29524` y con `0` (el C para en 4 y 6 pasos, exactamente los predichos por el trazador) y con `33` y `126` (recorre los 6 pasos hasta `END`): la guarda cubre exactamente el rango imprimible. Aplicada a las cuatro instancias ya publicadas del resolvedor, la predicción del oráculo coincide con el contador del C **exacto** (276, 273, 272, 176). El runner C queda caracterizado como variante **restringida**, no como motor divergente** | [`vm_malbolge/evidence/c_printable_guard_v1/`](vm_malbolge/evidence/c_printable_guard_v1/) |
| **Payload de 10 trits elegido por la petición (epoch_resolver_request_v1)** | `PASS` | **Una única imagen de 293 bytes atiende payloads distintos: la petición lleva 20 dígitos de control y el programa construye `P` y `M` en memoria (el acumulador gira un `ROT` entre escrituras para ir avanzando la ventana de posición, con `ROT` final que restaura el marco), `V = crazy(M,P)` y la época recibe el payload **exacto** (93, 187, 281, 29797), cada uno ejecutado en `pc = T = 100` con su `OUT` (`0x5d`, `0xbb`, `0x19`, `0x65`), 171 pasos, HALTED. La descomposición `V = crazy(M,P)` con `P` y `M` en `{1,2}^10` vale para las **59049** palabras (exhaustivo, 0 discrepancias). **Resultado negativo con prueba exhaustiva**: el semigrupo de `crazy` sobre un trit tiene 15 mapas y el mapa trit→dígito de control (`(0,2,0)`/`(0,2,2)`) **no** es alcanzable, así que la interfaz lleva dígitos de control y no los 10 trits. Control negativo: alterar un byte de la petición cambia el payload escrito. Dos motores Python coinciden byte a byte** | [`vm_malbolge/evidence/epoch_resolver_request_v1/`](vm_malbolge/evidence/epoch_resolver_request_v1/) |
| **Rearm de máscara: dos escrituras exactas en una ejecución (epoch_rearm_primitive_v1)** | `PASS` | **Bootstrap sin celda cero y sin máscara imprimible involutiva (`a=0`, `crazy(0,36)=29524`); escritura exacta con la máscara `29524`: `crazy(V,29524)=swap(V)` en el scratch y `crazy(swap(V),29524)=V` en el destino (`OUT = f2 ff` con payloads 242 y 255 de stdin). **Rearm medido**: `crazy(29524,X)=extract2(X)` y `crazy(E,E)=29524` devuelven la celda consumida a su valor de máscara (`B = 29524` justo antes de la segunda escritura). Recarga sin consumo: `29524` es todo 1s, invariante bajo `ROT`. Planificador que simula el recorrido de `d` y falla si una celda de salto necesitaría dos valores. 3 motores byte a byte en 5 instancias, 4 controles negativos divergen** | [`vm_malbolge/evidence/epoch_rearm_primitive_v1/`](vm_malbolge/evidence/epoch_rearm_primitive_v1/) |
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

### 13. PureEpoch: Ejecución Stateful, Bucles Autónomos y Tolerancia Bizantina
La suite [`pureepoch/`](pureepoch/) aporta 12 artefactos autónomos verificados en Malbolge Classic:
- **Boss 3 (El Santo Grial de Malbolge):** Bucle dinámico `while x > 0` autónomo ([`pureepoch/programs/boss3_autonomous_loop.mal`](pureepoch/programs/boss3_autonomous_loop.mal)). No requiere modificación de memoria desde Python (`vm.mem[...] = ...` auditado y eliminado). Despacho ternario universal `rot(crazy(N, 67))` y generación in-band de la constante `'1'`. Pasa 100% bit-exacto en los oráculos C nativo e histórico en todos los vectores ($N \in \{0, 1, 2, 3, 7, \text{EOF}\}$).
- **Boss 2 (Turing-completo en Malbolge):** Intérprete Brainfuck ejecutable sobre celdas `[65..69]` de memoria baja ([`pureepoch/programs/boss2_brainfuck.mal`](pureepoch/programs/boss2_brainfuck.mal)).
- **Boss 1 (Tolerancia a Fallas Bizantinas):** Cascada jerárquica con recuperación escalonada en diarios anidados ($J_1 \to J_2$) ante mutación hostil ([`pureepoch/programs/boss1_byzantine.mal`](pureepoch/programs/boss1_byzantine.mal)).
- **Torus G-T2 & G-T3:** Préstamo y devolución de celdas en el espacio muerto $\mathcal{D} \setminus \mathcal{C} \setminus \mathcal{E}$ entre límites de épocas ([`pureepoch/programs/torus_borrow_e_t2.mal`](pureepoch/programs/torus_borrow_e_t2.mal), [`pureepoch/programs/torus_e_t3_normal.mal`](pureepoch/programs/torus_e_t3_normal.mal)).
- **Épocas M1..M3:** Involución de mutación de 10 rotaciones, checkpoints en diario y encadenamiento autónomo de 2 y 3 fases continuas.
- Suite verificada en [`pureepoch/tests/test_pureepoch.py`](pureepoch/tests/test_pureepoch.py) (18/18 PASS).

### 14. Frentes 3 y 5: bucle con estado, pila LIFO y despacho computado

Campaña sobre los dos frentes `NOT_DEMONSTRATED` que pedían una imagen Classic que
itere sobre un flujo de bytes y una pila de profundidad 2. Cuatro resultados, todos
con doble motor (oráculo Python con `stop_on_eof=True` y runner C nativo):

**a) La primitiva de bucle, explicada.** Traza paso a paso de `simple_cat` más la
medición de `XLAT2`: el cifrado tiene ciclos mezclados y **solo 70 (`F`) y 74 (`J`)
forman un 2-ciclo** (2 valores de 94, 0 puntos fijos), y la celda de un `JMP` nunca
se cifra porque `c` se reasigna al destino antes del cifrado. De ahí la receta:
instrucción con valor en 2-ciclo + `JMP` que la apunta (la cifra dos veces y vuelve
a su valor). Consecuencia medida: **2 direcciones utilizables por opcode** dentro de
una ventana de 94 — MOVD 60/64, IN 43/47, ROT 59/63, CRAZY 82/86, OUT 119/123,
NOP 88/92. Detalle: [`vm_malbolge/evidence/native_fold_loop.md`](vm_malbolge/evidence/native_fold_loop.md).

**b) Bucle de fetch nativo con estado entre bytes** ([`mbir_native_fold_loop.mb`](vm_malbolge/src/mbir_native_fold_loop.mb), 130 B, sin LMAO). Una vuelta
`IN → MOVD → CRAZY(estado) → OUT → MOVD(rebobina)` que regresa al mismo despacho
(celda 43) y mantiene una celda de estado a través de todos los bytes leídos. La
semántica es precalculable (`estado = crazy(byte, estado)`), así que la salida se
verifica contra un modelo: **9/9 flujos** y **4.096 bytes aleatorios exactos**
(61.444 pasos, HALTED).

**c) Pila LIFO de 2 ranuras, one-shot** ([`mbir_stack2_oneshot.mb`](vm_malbolge/src/mbir_stack2_oneshot.mb)). Lee dos bytes, los guarda en dos celdas
distintas y los emite en orden inverso: `AB`→`6368`, `BA`→`6769` (el orden se
invierte con la entrada), `0102`→`5556`. **8/8**, 32 pasos, y loader estricto
**completo**: todas las celdas de código y de dato decodifican a opcode válido en su
propia dirección. La lectura exacta se hace con 10 pares `MOVD`/`ROT` porque
`rot^10` es la identidad.

**d) Despacho computado por el dato** ([`mbir_dispatch2.mb`](vm_malbolge/src/mbir_dispatch2.mb)). Máquina de bytecode de dos instrucciones con
codificación de longitud variable — `PUSH` = `01 operando`, `POP` = `F2` — que
**enruta según el opcode**: en un programa one-shot `mem[P] = crazy(a, mem[P])` es
función pura del byte leído, así que eligiendo `V` con
`crazy(0x01, V) = landing_push - 1` y `crazy(0xF2, V) = landing_pop - 1`, el `JMP`
que lee `mem[P]` salta al manejador correcto. **Sin cadena de comparaciones ni
contador: el dato es la dirección.** `01 41 F2`→`68` (el POP emite lo que el PUSH
guardó), `F2 01 43`→`21` (enrutado correcto), `01 41 01 42`→vacío. **8/8 casos y
111/111 combinaciones** de un barrido con operandos `00..1F`, `7F`, `80`, `C3`,
`FE`, `FF`.

**Obstrución probada (no supuesta) para la versión con bucle de (c) y (d):** dos
instrucciones que dejan `d` en la misma celda comparten sus celdas de puntero
`(S+1, S+2)`; el `CRAZY` (escritura) y el `ROT` (lectura) de una celda de pila
dejan ambos `d = S`, así que **una celda no puede escribirse y leerse en el mismo
ciclo**. Con el presupuesto de 2 direcciones por opcode, una pila con lectura y
escritura simultáneas no es construible con esta primitiva. Salidas documentadas:
celda-puntero escrita en tiempo de ejecución, o el selector buscado al estilo de
BolgeForge (paseo `j/*` que diverge sobre la celda modificada por `crazy`).

**Corrección al bloqueante declarado:** `frentes3y5_bloqueante.md` afirmaba que no
existía en el corpus una imagen Classic que iterara sobre flujo. Queda refutado en
[`frentes3y5_bloqueante_CORRECCION.md`](vm_malbolge/evidence/frentes3y5_bloqueante_CORRECCION.md): `cat_compact.mal` de BolgeForge
(7.596 celdas, commit `7b4fbac`) itera de verdad y se verificó con los motores de
este repo; el enunciado quedaba acotado al corpus `vm_malbolge`.

**e) Encadenado: N instrucciones desde el flujo** ([`mbir_dispatchN.mb`](vm_malbolge/src/mbir_dispatchN.mb)). La generalización de (d) a
N = 3 instrucciones encadenadas por tres despachos, con codificación de longitud
variable (`PUSH 0x35 operando`, `POP 0x41`) y la celda de pila sobreviviendo de una
instrucción a la siguiente: `35 41 41 35 42 41`→`78`, `41 35 41 41 35 42`→`0b48`,
`35 41 41 35`→`7898` (dos POP emiten `rot` y `rot²` del slot). **9/9** en los dos
motores. Detalle y el límite medido: [`vm_malbolge/evidence/dispatchN.md`](vm_malbolge/evidence/dispatchN.md).

**Corrección (empaquetado exacto, [`dispatch_pack.md`](vm_malbolge/evidence/dispatch_pack.md)).**
El «límite de la ventana» de (e) era un artefacto de empaquetado: exigir
separación uniforme 14 entre todos los destinos y usar colas `3k+1` no es
necesario. El bloque real (destino incluido) mide `6+t` celdas (push) y `5+t`
(pop) desde el destino, así que dos destinos a 12 celdas pueden ser legales si
el primer bloque es corto. Con el protocolo libre —`PUSH 0xff` cae en la banda
adyacente, `[29160, 29402]`, y `POP 0x35` en `[29403, 29645]`— el empaquetado
exacto da **N=4** con el protocolo original y **N=5** con el nuevo, ambos con
**coste de rotación cero** y 9/9 en los dos motores. La única regla de choque de
punteros es `t_j = t_i + 2` (celda `JMP` frente a celda de entrada del despacho
siguiente); por eso las colas pueden diferir en 1 o 3, no en 2.

---

### 15. Línea de épocas: selector, almacén, journal y resolvedor algebraico (v1 → v3)

Cuatro packs encadenados, todos en Malbolge Classic y sin intervención del host durante
la ejecución (el host solo aporta la entrada por `stdin` y recoge la salida):

| v | Pack | Qué demuestra | Veredicto |
|---|---|---|---|
| v1 | [`epoch_selector_reusable_v1/`](vm_malbolge/evidence/epoch_selector_reusable_v1/) | Selector de dos rutas reutilizable: la petición `01`/`02` elige la ruta **en runtime**, el marcador de la ruta se rearma con diez `ROT` y el control vuelve al mismo `IN`. 9 flujos + 128 solicitudes pseudoaleatorias (semilla 20261107) | `CONDITIONAL_PASS` (dominio `{01,02}`) |
| v1 | [`epoch_selector_store_v1/`](vm_malbolge/evidence/epoch_selector_store_v1/) | Selector **y** almacén exacto rearmable en una sola imagen Classic: el valor seleccionado se copia al almacén con dos `CRAZY` y se recupera exacto desde él | `CONDITIONAL_PASS` (dominio `{01,02}`) |
| v2 | [`epoch_journal_state_v2/`](vm_malbolge/evidence/epoch_journal_state_v2/) | Journal M1b de PureEpoch adaptado (`SAVE → clobber → 10×ROT → RESTORE`) con la **ruta elegida por el estado** (`EPOCH_PHASE`, ciclo `XLAT2` 70↔74), más un tercer control negativo que verifica el contrato de estado y no solo `stdout` | `CONDITIONAL_PASS` |
| v3 | [`epoch_algebra_v3/`](vm_malbolge/evidence/epoch_algebra_v3/) | **Resolvedor de épocas en runtime**: la petición (byte `b`) selecciona la celda de época `T = b+1` (36, 130, 224 — 94 de separación, mismo residuo), se escribe el valor **exacto** recibido por `stdin` con la involución de `crazy` (máscara imprimible `121`) y se salta a esa celda para ejecutarla | `PASS` |

El v3 es el primero que mueve la decisión **a la dirección física**: no hay ramas por
valor, la única decisión es la dirección leída del puntero. La traza muestra las cuatro
escrituras (`scratch → puntero exacto → scratch → celda de época exacta`) y que el `OUT`
se emite en el PC de la celda escrita. La exactitud está medida sobre **los 256 valores
de byte en las tres épocas** (768 escrituras, 0 discrepancias) y los tres motores
(trazador sobre las primitivas del oráculo, oráculo del repo y runner C original)
coinciden byte a byte en las 144 filas. Los cinco controles negativos fallan como se
espera: residuo desalineado (223 en vez de 224), scratch corrupto, puntero corrupto,
máscara rota y escritura a otro bloque.

**Correcciones de imposibilidad que este trabajo provoca.** Los tres documentos
[`pop_exacto_bloqueante.md`](vm_malbolge/evidence/pop_exacto_bloqueante.md),
[`pila_llamadas_bloqueante.md`](vm_malbolge/evidence/pila_llamadas_bloqueante.md) y
[`dos_sistemas_middleware_analisis.md`](vm_malbolge/evidence/dos_sistemas_middleware_analisis.md)
conservan su texto original y **añaden una corrección medida** (2026-11-07): queda
refutada la causa raíz "no existe asignación directa a memoria" —el doble `crazy` con
máscara `121` escribe un valor exacto y arbitrario en runtime—, y con ella el
"direccionamiento indexado" y el "salto dirigido por datos". **Sigue vigente** que `c`
no se puede leer ni guardar (de ahí que la pila de llamadas con direcciones de retorno
siga bloqueada) y que la máscara consumida obliga a rearmar la celda: el rearm con
journal está demostrado en v2 para celda fija, y **componer** journal y selección
dinámica de época es `NOT_DEMONSTRATED`.

---

## Hito: Quine Clásica Más Pequeña — 53,562 B (BolgeForge)

**La quine Malbolge clásica más pequeña producida y verificada por este ecosistema: 53,562 bytes, 6,290 bytes menos que la quine de referencia de Matthias Lutter (59,852 B).** Sintetizada por **BolgeForge** (subsistema de síntesis del monorepo ISyCo) y verificada byte a byte con **triple motor C independiente** (incluye un oráculo que se distribuye en `quine/evidence/mb_classic_indep.c` y verifica en ~0.25 s). Supera al récord anterior del mismo ecosistema (m=284, 54,134 B) por **572 bytes** e inaugura el descenso por debajo de m=284, que estaba en `NOT_DEMONSTRATED`.

| m | Artefacto | Bytes | Δ vs Lutter | SHA-256 |
|---|---|---|---|---|
| **281** | [`quine/quine_53562_m281.mb`](quine/quine_53562_m281.mb) **(récord)** | **53,562** | **−6,290** | `96b670b8…` |
| 284 | [`quine/quine_54134_m284.mb`](quine/quine_54134_m284.mb) (récord anterior) | 54,134 | −5,718 | `1808fd4d…` |
| 287 | [`quine/ladder/quine_54706_m287.mb`](quine/ladder/quine_54706_m287.mb) | 54,706 | −5,146 | `3da997b9…` |
| 293 | [`quine/ladder/quine_55850_m293.mb`](quine/ladder/quine_55850_m293.mb) | 55,850 | −4,002 | `1719515d…` |
| 308 | [`quine/ladder/quine_58709_m308.mb`](quine/ladder/quine_58709_m308.mb) | 58,709 | −1,143 | `67628cf1…` |

- El récord vigente (m=281, verificado 2026-10-17) y el anterior (m=284, 2026-10-16) fueron verificados con doble motor C independiente (el récord, con un tercero adicional distribuido en el repo): `mb_ref` coincide **byte a byte** (0 diferencias) y el runner C de este repositorio coincide en los **primeros N bytes** (añade un `0x0A` final de convención propia, igual que en los vectores M2); `steps` reportados en stderr (`steps: 62239852 | status: HALTED` para el récord, ~22 min). La escalera m=287/293/308 está verificada con `mb_ref` (0 diferencias).
- Procedencia: BolgeForge `synthesize_v2.py` — grafo de 26 macros de auto-modificación verificadas puras encadenadas por Dijkstra, generador analítico de constantes y búsqueda runtime de la macro `inc` (candidatos duros → BFS acotado → **fallback composite constructivo de 2 escrituras** para valores muertos, añadido 2026-10-17); bitácora completa en `NOTES.md` del monorepo ISyCo.
- Alrededor de la escalera corre el programa de investigación **REVERSE_SELF_MODIFICATION**: la traza del build m=284 (B0) muestra que 24,009 de 24,090 celdas ejecutadas terminan en `final == X^k(init)` con `X = xlat2` (LCM 3,060), y el demo B1 de 44 bytes imprime un byte **imposible** (0xFD) mediante auto-modificación de una sola celda.
- Detalles completos, protocolo de verificación, mapa técnico de la construcción y límites: [`quine/README.md`](quine/README.md).

> **Alcance del claim (anti-fake):** la comparación es contra la referencia Lutter (59,852 B) y la escalera propia; no hay barrido externo exhaustivo de todas las quines clásicas publicadas. El descenso por debajo de m=284 quedó **DEMONSTRATED** hasta m=281 (composite constructivo de la macro `inc`); por debajo de m=281: `NOT_DEMONSTRATED` (m=278 sigue bloqueado por el piso del stream sintetizado; el DP de cadena por sí solo no basta; candidatos inc-dead y palancas en `NOTES.md` §Next steps).

---

## Lo que FALTA por hacer (Roadmap / NOT_DEMONSTRATED)

1. **Control de Flujo Completo en Malbolge VM**
   - JMP, JZ, CALL y la comparación relacional `CMP_EQ` en RAM ya están demostrados en el Hito M2 CF + CMP_EQ (7/7, 56,947 bytes). Sigue faltando un contador de programa general para código arbitrario, usar el destino del JMP como selector dinámico arbitrario, y una pila de llamadas de más de una trama.
   - **(parcialmente cerrado) "usar el destino del JMP como selector dinámico arbitrario"**: ya está demostrado con un salto **computado por el dato** — `mbir_dispatch2.mb` enruta `PUSH`/`POP` sobre flujo haciendo que la dirección de salto sea `crazy(opcode, V)` escrita en una celda (8/8 + 111/111, sección 14d). El encadenado ya llega a **N=5 sin rotaciones** con empaquetado exacto ([`dispatch_pack.md`](vm_malbolge/evidence/dispatch_pack.md)); **N=6 queda excluido en los protocolos de mayor capacidad** por búsqueda exhaustiva ([`dispatch_pack_bound.json`](vm_malbolge/evidence/dispatch_pack_bound.json)), con el barrido de los 975 protocolos restantes abierto. Lo que sigue abierto del todo es la pila de llamadas, ahora con un bloqueante medido: **imposible en Malbolge Classic** porque el program counter `c` es un registro de solo escritura (se puede saltar a él con `JMP`, se auto-incrementa, pero nunca se puede leer ni guardar en una celda de datos). Sin guardar `c` no hay retorno de subrutina; sin retorno, no hay pila de llamadas. Bloqueante documentado en [`vm_malbolge/evidence/pila_llamadas_bloqueante.md`](vm_malbolge/evidence/pila_llamadas_bloqueante.md). **Actualización 2026-11-07:** el bloqueante se mantiene solo en su forma clásica (direcciones de retorno); la otra mitad de su causa raíz —"no existe asignación directa a memoria"— queda **refutada** por el resolvedor v3 (escritura exacta en runtime con doble `crazy` y máscara `121`, y salto dirigido por datos a la celda elegida por la petición). Ver [`epoch_algebra_v3/`](vm_malbolge/evidence/epoch_algebra_v3/) y la corrección medida del documento de bloqueante.
2. **Integración Completa del Pipeline de Ejecución (M2 + ALU + CMP)**
   - Sigue sin existir una sola imagen que cargue el programa en RAM y además ejecute la ALU de 14 vectores y el `CMP_EQ`. Una sonda sobre `mbir_alu.hell` (12 banderas y 8 celdas de scratch) no ensambló: el inicializador se quedó sin sitio en la celda 57855. Quince `C1` sueltos sí entraron. Detalle: [`vm_malbolge/M2_FULL_STATUS.md`](vm_malbolge/M2_FULL_STATUS.md).
   - **La causa está ahora medida y partida en dos**:
     - *Mitad cargador / PC de programa almacenado*: **límite semántico del emisor nativo**. `native_probe_d.json` midió que el puntero de datos avanza +1 por instrucción (trazo verificado contra `tools/oracle_classic.py:93-97`), pero **ningún opcode escribe un valor arbitrario**: el 39 solo rota lo que ya hay y el 62 mezcla (`mem[d] = crz(a, mem[d])`). Un cargador byte-exacto exigiría `a = find_a_for_crazy(contenido, X)` por byte, y esa transformación depende de la entrada, así que una receta fija no lo expresa.
     - *Mitad aritmética + comparación dentro de la misma imagen*: **límite de presupuesto en la imagen ALU/comparador**. `cmp_lt_extensibility_probe.json` midió que sobre `mbir_cmp_lt.hell` (margen 1.538 B) ya falla **un** flag nuevo de código, y las celdas de datos fallan de forma no monótona (2 OK, 4 FAIL, 8 OK, 16 FAIL).
     - **Pero la imagen del cargador SÍ tiene sitio** (`loader_budget_probe.json`): `mbir_m2_loader.hell` tiene 18.740 B de margen y admite **512 celdas de datos** y **8 flags de código** nuevos. Así que (b) no está bloqueado por el presupuesto del inicializador en el lado del cargador.
     - **Intento de merge medido** (`unified_merge_attempt.json`, generador `vm_malbolge/tools/unified_gen.py`): se extendió `mbir_m2_alu.hell` —que **ya** carga un programa de 7 bytes en RAM y ejecuta ADD/SUB (8/8)— con un caso de despacho `CMP_EQ`. El parche aplica limpio en 9 regiones y no añade más flags de los que el presupuesto permite (2), pero **LMAO rechaza el resultado**: `Free space exceeded` / `Cannot generate initialization code for cell 58969`, a 80 celdas del límite. Los flags caben; lo que no cabe es el **código de despacho** en los 2.688 células de margen restantes.
   - **Ruta constructiva vía cargador** (`mbir_m2_loader.hell`, 18.740 B de margen): se intentó agregar celdas de RAM y un bucle de ejecución sobre el andamio del loader. Se verificó que se pueden agregar celdas (`prog_4`, ensambla a 43,223 B) y bloques de ejecución, pero **no hay forma de hacer que el contenido de RAM se ejecute como instrucciones**: `JMP` lee `mem[d]` como valor de destino, no como dirección; no existe `mem[d] = c` ni `c = valor_conocido`; y las celdas de datos no están en 2-ciclo de `XLAT2` para repetirse. Bloqueante documentado en [`vm_malbolge/evidence/cargador_ruta_constructiva_bloqueada.md`](vm_malbolge/evidence/cargador_ruta_constructiva_bloqueada.md). Es la misma causa raíz que los otros frentes: sin asignación directa a memoria ni lectura del PC, no hay bucle fetch-decode-execute general.
   - **Lo que sí quedó demostrado**: la mitad aritmética, como imágenes Classic únicas sin LMAO y con loader estricto ACCEPT en tres motores — `mbir_native_3routes.mb` (`ADD` + `CMP_EQ` + `CMP_LT`) y `mbir_native_cmp_decimal.mb` (comparador de dominio `0..9`).
3. **Pila Dinámica de Profundidad > 2**
   - Para expresiones complejas que requieran evaluar árboles sintácticos de mayor profundidad o direccionamiento indexado.
   - **(avance) La profundidad 2 ya está demostrada** en la vía one-shot sin LMAO: `mbir_stack2_oneshot.mb` almacena dos bytes en dos celdas y los emite en orden inverso (8/8, loader estricto completo, sección 14c), y `mbir_dispatch2.mb` añade el enrutado por opcode sobre el flujo (sección 14d).
   - **(bloqueante REFUTADO) La versión con bucle de la pila**: el obstáculo medido en `stack2_oneshot.md` (una celda no puede escribirse con `CRAZY` y leerse con `ROT` en el mismo ciclo, porque ambas dejan `d` en la misma celda y compartirían las celdas-puntero `(S+1, S+2)`; más el presupuesto de 2 direcciones por opcode para la restauración por 2-ciclo) **ya no es un bloqueante**: una celda de trabajo que **no se restaura** avanza por su ciclo de `XLAT2` y cambia de opcode sola en cada iteración, de modo que la misma celda hace `CRAZY` en una iteración y `ROT` en otra. Es el estado de cifrado acting como selector de fase, sin celda-puntero de fase. Evidencia: [`vm_malbolge/evidence/stack_loop_phase.md`](vm_malbolge/evidence/stack_loop_phase.md) (escritura y lectura de la misma celda en iteraciones distintas, 8/8 + control) y [`vm_malbolge/evidence/stack_loop_lifo2.md`](vm_malbolge/evidence/stack_loop_lifo2.md) (**LIFO de profundidad 2 en bucle real**: push `S1`@0, push `S2`@3, pop `S2`@4, pop `S1`@5; 8/8 + control).
   - **(lo que sigue abierto, bloqueante medido)**: el pop es un `ROT` y deja la ranura rotada — un pop **exacto** (emitir el valor almacenado sin rotar) es **imposible en bucle**. Bloqueante medido y documentado en [`vm_malbolge/evidence/pop_exacto_bloqueante.md`](vm_malbolge/evidence/pop_exacto_bloqueante.md), con cuatro causas:
     1. *Sin lectura pura*: ninguna instrucción Malbolge lee `mem[d]` en `a` sin modificar `mem[d]` (`ROT` y `CRAZY` ambas alteran la celda).
     2. *rot^10 = identidad, rot^k ≠ identidad para k < 10*: un pop exacto requiere exactamente 10 `ROT` sobre la misma celda; verificado empírico para todo `[33,126]`.
     3. *Una celda no hace ROT en 2+ fases de su ciclo*: medido que ninguna dirección tiene `ROT` en 2+ posiciones de su ciclo de `XLAT2` sin `HALT`/`JMP`.
     4. *Sin contador estable*: distribuir 10 `ROT` en vueltas consecutivas requiere un contador, y cualquier celda de contador se cifra con `XLAT2`.
     El LIFO demostrado (`stack_loop_lifo2.md`) usa `ROT` como pop (valor rotado, no exacto); es lo máximo expresible en un bucle real **por la vía del pop por carga**.
   - **Actualización 2026-11-07 (matiz, no refutación):** las cuatro causas miden el **pop por carga** (extraer una ranura de dato arbitrario en `a` sin modificarla), que sigue bloqueado. La formulación general "un valor exacto no puede emitirse" queda **refutada**: con la máscara imprimible `121` el doble `crazy` escribe un valor exacto y arbitrario en la celda y **esa celda lo ejecuta** emitiendo el byte exacto, sin rotación (768 escrituras medidas, 0 discrepancias; [`epoch_algebra_v3/`](vm_malbolge/evidence/epoch_algebra_v3/)). Lo que queda pendiente es el **rearm** de la máscara consumida dentro de la misma ejecución (el journal de v2 lo resuelve para una celda fija; componer journal y selección dinámica sigue `NOT_DEMONSTRATED`).
   - Las fases inertes (1, 2, 6, 7, 8) no se pueden silenciar: `IN`/`OUT` siguen ejecutándose y emitiendo el byte en cada vuelta.
   - La profundidad 3 o mayor no está construida: en la clase de ciclo de 9 solo hay dos direcciones que den el calendario LIFO (71 y 83).
4. **Operadores de Orden Relacional (`CMP_LT`, `CMP_GT`)**
   - Ambos están **DEMONSTRATED 12/12** en los dos motores: `CMP_LT` (Finding 74, sección 5b) y `CMP_GT` (Finding 75, sección 5c).
   - **(a) quedó ABIERTO y ahora tiene un primer resultado**: el dominio `{0,1,2}` de esos kernels es un **techo duro** — la sonda `cmp_lt_extensibility_probe.json` midió que ni un flag nuevo de código cabe sobre `mbir_cmp_lt.hell` (margen de 1.538 bytes). Pero la vía nativa sí lo cruza: `mbir_native_cmp_decimal.mb` implementa `CMP_LT(d, 5)` para los **diez dígitos decimales `0..9`**, 10/10 PASS en oráculo, runner C y loader estricto.
   - **Restricción medida**: ese comparador cubre **un** operando variable contra la constante de referencia 5. El caso de **dos operandos variables** está bloqueado por tres rutas medidas y documentadas en `cmp2_two_operand_blocker.json`:
     - *Clave de enrutado de dos bytes*: como máximo **56 de 100** pares de dígitos alcanzan una dirección de ruta distinta (44 colisionarían).
     - *Cadena fija de operaciones* sobre el segundo operando: **no existe** — verificado con BFS exhaustiva sobre el conjunto alcanzable completo (**51.799 estados**, profundidad 30) para cinco valores de referencia. La razón es estructural: `CRAZY` es trit a trit y `ROT` solo rota trits, así que cada trit de la salida depende de un único trit de la entrada (función **separable**), y la comparación de dos dígitos no lo es.
     - *Despacho anidado*: la familia de claves da 10 direcciones distintas para **un** único `(c, r) = (85, 7)`, que ya usa el primer nivel.
5. **Frontends que todavía no existen**
   - Pistas `swift/`, `rust/`, `java/`, `c/` marcadas como `NOT_STARTED`.
   - En Python, P5 ya baja la recursión directa a MBIR en el host (sección 12). P6, el lexer dentro de Malbolge, se probó y no quedó demostrado: al volver a `ENTRY` el clasificador de un byte no emite el segundo token, y el runner C no coincide con el oráculo ([`python/P6_STATUS.md`](python/P6_STATUS.md)). **La causa de esa divergencia quedó identificada y corregida entretanto**: el oráculo no paraba en EOF (asignaba `a=59048` y seguía emitiendo `ff` hasta el límite de pasos), mientras el runner C para con `terminated=1`; con `stop_on_eof=True` los dos motores coinciden byte a byte sobre el andamio iterante (9/9). P7 (parser) y P8 (`python.mb`) no se empezaron.
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

### 8. Verificar el Orden Relacional CMP_LT (Hito P2 relacional, 12/12)
El harness corre los 12 vectores (9 pares ordenados + 3 líneas base) en el oráculo Python **y** en el runner
nativo C, y compara salida y número de pasos. Tarda un minuto porque el oráculo es un intérprete en Python.

```bash
# Imagen canónica 12/12 (Finding 74). Sale 0 sólo si se alcanza 12/12.
python3 vm_malbolge/tests/lt_harness.py vm_malbolge/src/mbir_cmp_lt.mb

# Copia inmutable de evidencia (blob sha256 79160ecf906ce3a4…).
python3 vm_malbolge/tests/lt_harness.py vm_malbolge/evidence/artifacts/lt_pass12.mb

# Reconstruir desde el HeLL canónico (LMAO v0.6.0, modo normal con depuración). Los builds son
# byte-nodeterministas pero invariantes en comportamiento (Finding 62): el hash identifica una instancia.
./third_party/lmao/bin/lmao -d -o /tmp/imagen.mb vm_malbolge/src/mbir_cmp_lt.hell

# Imágenes históricas de la etapa 11/12 (cada una falla UNA sola entrada distinta): negativo conservado.
python3 vm_malbolge/tests/lt_harness.py vm_malbolge/evidence/artifacts/lt_f59_cand_C.mb
```

### 8b. Verificar el Orden Relacional CMP_GT (Hito P2 relacional inverso, 12/12)
Mismo contrato de harness: 9 pares ordenados + 3 líneas base, salida y número de pasos en los dos motores.

```bash
# Imagen canónica 12/12 (Finding 75).
python3 vm_malbolge/tests/gt_harness.py vm_malbolge/src/mbir_cmp_gt.mb

# Copia inmutable de evidencia (blob sha256 1f17062a9585beb…).
python3 vm_malbolge/tests/gt_harness.py vm_malbolge/evidence/artifacts/gt_pass12.mb

# Reconstruir desde el HeLL canónico (misma nota de no-determinismo de bytes).
./third_party/lmao/bin/lmao -d -o /tmp/gt.mb vm_malbolge/src/mbir_cmp_gt.hell
```

### 9. Verificar la Quine Clásica Récord (53,562 B)

La quine imprime su propio código fuente byte a byte; la verificación es un `cmp` entre la salida del runner y el archivo. El runner C de este repositorio añade un `0x0A` final de convención propia (igual que en los vectores M2), así que se comparan los primeros N bytes con `cmp -n`.

```bash
# Salida identica en los primeros 53,562 bytes (los pasos van en stderr: steps: 62239852 | status: HALTED)
./runners/malbolge-original/malbolge quine/quine_53562_m281.mb > /tmp/quine.out
cmp -n 53562 /tmp/quine.out quine/quine_53562_m281.mb   # 0 bytes de diferencia

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


# PureEpoch: ejecuciones y épocas

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
| v4 | [`epoch_resolver_epoch_select_v1/`](vm_malbolge/evidence/epoch_resolver_epoch_select_v1/) | **La misma petición elige la época y el payload**: 21 bytes — el byte 0 fija la celda de época (`T = b+1` ∈ {100, 106, 112}) y 20 dígitos de control fijan el payload de 10 trits; puntero escrito **exacto** con la máscara `29524` (no imprimible), escritura **exacta** en `T` y salto a `T` sin ramas por valor. 7 instancias × 4 motores, 3 controles negativos | `PASS` |
| v5 | [`epoch_rearm_barrier_v1/`](vm_malbolge/evidence/epoch_rearm_barrier_v1/) | **Barrera medida del rearm**: qué se puede rearmar en Classic para servir una segunda petición en la misma ejecución. El rearm de **dato** es universal y exacto (59049/59049); el de **código** está acotado (839/2400 pares restaurables con un `CRAZY`, 26 con palabra de control materializable = 29403, 34 por la vía de dos pasos) y el salto de retorno con celda sembrada sólo alcanza 34..127 | `CONDITIONAL_PASS` (condiciones medidas) |

El v3 es el primero que mueve la decisión **a la dirección física**: no hay ramas por
valor, la única decisión es la dirección leída del puntero. La traza muestra las cuatro
escrituras (`scratch → puntero exacto → scratch → celda de época exacta`) y que el `OUT`
se emite en el PC de la celda escrita. La exactitud está medida sobre **los 256 valores
de byte en las tres épocas** (768 escrituras, 0 discrepancias) y los tres motores
(trazador sobre las primitivas del oráculo, oráculo del repo y runner C original)
coinciden byte a byte en las 144 filas. Los cinco controles negativos fallan como se
espera: residuo desalineado (223 en vez de 224), scratch corrupto, puntero corrupto,
máscara rota y escritura a otro bloque.

**v4 compone la selección con el payload elegido por la petición.** La imagen pasa de
293 a 340 bytes y la petición de 20 a 21 bytes: el byte 0 elige la celda de época
(`T = b+1` ∈ {100, 106, 112}) y los 20 dígitos de control eligen el payload de 10
trits. Como la máscara del payload (`29524`) no es imprimible, la celda de época hay
que fabricarla en runtime y debe caer en la zona de dato (34..126), lo que obliga a
desacoplar el valor de la celda sucesora: en v3 valía `44 = W-1` en las tres épocas
(alineadas a 94) y hacía de END **y** de trampolín a `W`; en v4 cada época tiene el
su suyo (`v ≡ 80 - T (mod 94)`) y una cadena de **dos** `DLOAD` devuelve el puntero a
`W`. La cadena de instrucciones es idéntica en las tres épocas: sólo cambian los
valores de dato. Medido: época y payload están acoplados (opcode `= (V+T)%94`; con
estas épocas hay 0 payloads válidos en las tres, contra 8 con épocas alineadas a 94),
y la zona de dato admite **92** épocas candidatas (este pack implementa 3). Los
controles separan las dos palancas: cambiar **sólo** el byte de época mueve el
payload de la celda 100 a la 106, cambiar **sólo** un dígito de control cambia el
payload sin mover la época, y un byte de época fuera de catálogo no selecciona
ninguna época. Sigue abierto el **rearm** para una segunda petición en la misma
ejecución (`NOT_DEMONSTRATED`).

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

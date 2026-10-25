# PureEpoch: Stateful Multi-Epoch Execution in Malbolge Classic

La pista **PureEpoch** introduce un paradigma de ejecución con estado persistente, preservación de memoria, tolerancia a fallas bizantinas, máquina de Turing demostrada y bucles autónomos dinámicos en **Malbolge Classic** ($3^{10} = 59,049$ celdas) **sin requerir trampas ni intervención del host**.

---

## 1. Principio Fundamental: De la Fragilidad Estática a Épocas Autónomas

Históricamente, los programas Malbolge han sido secuencias lineales frágiles: cada instrucción ejecutada se auto-modifica inmediatamente mediante la tabla `XLAT2`, y cada operación Crazy `*` muta la memoria de datos. Esto causaba que cualquier intento de bifurcación condicional o bucle resultara en el colapso destructivo del código.

PureEpoch resuelve esto a través de:
1. **Involución y Reversibilidad de Mutación (M1A):** Operar dentro de las órbitas cerradas de longitud finita de `XLAT2` (ciclos regenerativos como $F \leftrightarrow J$ y órbitas de rotación de 10 trits).
2. **Checkpoints en Diario In-Band (M1B/M1C):** Almacenar copias de seguridad de las celdas críticas en registros de diario (*journal*) y ejecutar restauración incondicional al detectar discrepancias o condiciones de parada.
3. **Encadenamiento Multi-Época (M2/M3):** Encadenar 2 y 3 fases de cómputo sucesivas donde la salida y estado de una época sirve de precondición para la siguiente, con auto-rearmado (*re-arm*) de portales de salto.
4. **Préstamo Celular Toroidal (Torus G-T2/G-T3):** Emplear celdas en el espacio muerto $\mathcal{D} \setminus \mathcal{C} \setminus \mathcal{E}$ (datos jamás leídos ni ejecutados por el flujo principal) para almacenar estado inter-época y devolver intacto el préstamo.
5. **Tolerancia a Fallas Bizantinas (Boss 1):** Mecanismos de recuperación en cascada con diarios jerárquicos ($J_1 \to J_2$).
6. **Completitud de Turing / Motor Brainfuck (Boss 2):** Intérprete funcional en Malbolge Classic que opera sobre celdas de memoria baja `[65..69]`, decodificando punteros y bucles de Brainfuck.
7. **El Santo Grial: Bucle Dinámico Autónomo `while x > 0` (Boss 3):**
   - **Cero Intervención de Host:** El host no escribe en memoria (`vm.mem[...] = ...` estrictamente prohibido y eliminado).
   - **Despacho Ternario Universal:** La función de entrada $\text{rot}(\text{crazy}(N, 67))$ mapea $\{\text{EOF}, 0, 1, 2, 3, 7\}$ a direcciones con separación $\ge 2$, bifurcando autónomamente a salida o bucle.
   - **Generador In-Band de Constantes:** La celda 49 ($113$) rotada dos veces produce el acumulador $a = 32817$, cuyo byte bajo $32817 \pmod{256} = 49 \implies \text{ASCII } '1'$ de forma 100% interna.

---

## 2. Inventario de Artefactos Demostrados

| Artefacto | Tamaño (B) | SHA-256 | Hito / Descripción | Pasos / Estado |
|---|---|---|---|---|
| [`pureepoch/programs/m1a_rot10.mal`](pureepoch/programs/m1a_rot10.mal) | 98 | `188f8e9e…` | **M1A:** Mutación reversible en órbita de 10 rotaciones | 43 / `HALTED` |
| [`pureepoch/programs/m1b_normal.mal`](pureepoch/programs/m1b_normal.mal) | 308 | `80e5cf6a…` | **M1B:** Checkpoint interno en diario | 14 / `HALTED` |
| [`pureepoch/programs/m1c_normal.mal`](pureepoch/programs/m1c_normal.mal) | 29,526 | `17ff6f32…` | **M1C:** Decisión in-band y rollback ante error | 66 / `HALTED` |
| [`pureepoch/programs/m1e_normal.mal`](pureepoch/programs/m1e_normal.mal) | 29,531 | `dc9ed4d8…` | **M1E:** Recuperación dependiente del estado previo | 570 / `HALTED` |
| [`pureepoch/programs/m2_normal.mal`](pureepoch/programs/m2_normal.mal) | 55,770 | `3ec16fd6…` | **M2:** Continuación autónoma de 2 épocas | 1,276 / `HALTED` |
| [`pureepoch/programs/m3_normal.mal`](pureepoch/programs/m3_normal.mal) | 55,770 | `7f95770a…` | **M3:** Cadena de propuestas de 3 épocas | 7,349 / `HALTED` |
| [`pureepoch/programs/quine94_ceiling_probe.mal`](pureepoch/programs/quine94_ceiling_probe.mal) | 94 | `65722e4a…` | **M3:** Sonda de techo quine de 94 bytes | 36 / `HALTED` |
| [`pureepoch/programs/torus_borrow_e_t2.mal`](pureepoch/programs/torus_borrow_e_t2.mal) | 677 | `c60a9b5b…` | **Torus T2:** Préstamo de celdas en $\mathcal{D} \setminus \mathcal{C} \setminus \mathcal{E}$ | 203 / `HALTED` |
| [`pureepoch/programs/torus_e_t3_normal.mal`](pureepoch/programs/torus_e_t3_normal.mal) | 29,842 | `14347b8d…` | **Torus T3:** Préstamo y devolución completa inter-época | 260 / `HALTED` |
| [`pureepoch/programs/boss1_byzantine.mal`](pureepoch/programs/boss1_byzantine.mal) | 29,531 | `63802e3c…` | **Boss 1:** Falla Bizantina en cascada ($J_1 \to J_2$) | 1,286 / `HALTED` |
| [`pureepoch/programs/boss2_brainfuck.mal`](pureepoch/programs/boss2_brainfuck.mal) | 1,303 | `ac46c907…` | **Boss 2:** Motor de ejecución Brainfuck (Turing-completo) | 1,205 / `HALTED` |
| [`pureepoch/programs/boss3_autonomous_loop.mal`](pureepoch/programs/boss3_autonomous_loop.mal) | 50,000 | `d2d6b91d…` | **Boss 3:** Bucle autónomo dinámico `while x > 0` | 9..23 / `HALTED` |

---

## 3. Verificación y Reproducción

Todos los programas de la suite PureEpoch se ejecutan directamente con el runner canónico C:

```bash
# 1. Verificar el Boss 3 (Santo Grial) con N=3 (emite 111):
echo -n "3" | ./runners/malbolge-original/malbolge pureepoch/programs/boss3_autonomous_loop.mal

# 2. Verificar el Boss 3 con N=0 (emite vacío):
echo -n "0" | ./runners/malbolge-original/malbolge pureepoch/programs/boss3_autonomous_loop.mal

# 3. Verificar el Boss 3 con N=7 (emite 1111111):
echo -n "7" | ./runners/malbolge-original/malbolge pureepoch/programs/boss3_autonomous_loop.mal

# 4. Verificar el motor Turing/Brainfuck (Boss 2):
./runners/malbolge-original/malbolge pureepoch/programs/boss2_brainfuck.mal < /dev/null | xxd

# 5. Ejecutar la suite de pruebas completa:
python3 -m pytest pureepoch/tests/test_pureepoch.py
```

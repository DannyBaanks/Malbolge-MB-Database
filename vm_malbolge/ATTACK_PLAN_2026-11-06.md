# Plan de ataque a los NOT_DEMONSTRATED — 2026-11-06

Este documento recoge las cuatro mediciones de la campaña A06 y el plan que
derivan. Es un documento de trabajo: cada conclusión apunta a su evidencia.

---

## Resumen ejecutivo

| # | Pregunta | Veredicto | Evidencia |
|---|---|---|---|
| E3 | ¿Qué revienta el inicializador de LMAO? | **Los flags de código, no las celdas de datos.** 64 celdas → OK (57.229 B); 2 flags → OK; 4 flags → FAIL | `evidence/e3_lmao_initializer_budget.json` |
| E4-bis | ¿Cabe el despachador nativo para las rutas que necesitamos? | **Sí para N=3.** 31 combinaciones `(c, rot)` dan 3 direcciones distintas con gap 27 = arena por ruta | `evidence/e4bis_dispatch_packing.json` |
| E0 | ¿Suma 3 dígitos el adder de LMAO con nuestro ensamblador? | pendiente de cierre (13/13 manuales PASS, 999+999=1998 incluido) | `evidence/e0_lmao_example_adder.json` |
| E1 | ¿Cómo se construye el comparador de operandos ≥ 3? | diseño listo, ver §3 | nota de diseño, este fichero |

---

## 1. E3 — el muro son los flags (corrige el diagnóstico anterior)

Medido sobre `mbir_alu.hell` comprometido (54.691 B) insertando, por separado,
celdas de datos y flags de código nuevos:

- **Celdas de datos**: 1, 2, 4, 8, 15, 16, 20, 24, 32, 48 y **64 celdas**
  compilan todas; el coste es suave (64 celdas ≈ 57.229 B, +2.538 B sobre la
  base). Un bloque de datos del tamaño de un cargador **no** es el obstáculo.
- **Flags de código**: 1 flag → 55.819 B OK; 2 flags → 54.697 B OK;
  **4 flags → `Memory usage conflict while generating initialization code`**;
  ≥ 8 → `Free space exceeded (Add Malbolge command)`.
- Cualquier combinación de ambos (4+8, 8+16, 12+24, …) falla.

**Consecuencia:** `M2_FULL_STATUS.md` atribuía el fallo al "presupuesto del
inicializador" en general. El presupuesto es holgado en datos y se agota
**específicamente por flags de código**: cada flag nuevo exige su ciclo de
traducción y sus tripletas de dirección. Esto también explica por qué la ALU
multiplexa sus 5 resultados sobre los seis flags ya existentes
(`SUBROUTINE_FLAG4..6`, `OP1_FLAG`) en lugar de añadir uno por resultado: no
hay sitio para más.

## 2. E4-bis — el emisor nativo cabe para nuestras rutas

El despachador nativo de BolgeForge selecciona la ruta con la clave
`dest = op(rot^r(op(a, c)), 48)`, donde `a = 48 + dígito`. El bloqueo
documentado del "producto" (100 recetas → 56 direcciones únicas, gap 0) hizo
suponer que la arquitectura no escala. Medido el caso real (N pequeño):

| N rutas | Combinaciones válidas | Mejor gap | Destinos |
|---|---|---|---|
| 2 | 756 | 19.683 | `[21, 19704]` |
| **3** | **31** | **27** | `[990, 1017, 1044]` |
| 4 | 10 | 27 | `[747, 828, 855, 882]` |
| 5 | 10 | 27 | `[747, 774, 828, 855, 882]` |

El gap de 27 celdas coincide con la arena que el emisor consume por ruta
(setup `3k+3` + receta ≤ 26 celdas), así que **tres rutas son colocables por
separado**. El bloqueo del producto es un artefacto de N=100, no del
despachador.

## 3. E1 — diseño del comparador con operandos ≥ 3

Análisis estático de `third_party/lmao/example_adder.hell` (GPL-3; se reutiliza
el **método**, nunca el fichero):

- **Contrato real:** lee un carácter por iteración; **cualquier no-dígito
  termina el número en curso** (por eso valen tanto `"12 34"` como
  `"12\n34\n"`). Cuatro dígitos seguidos se truncan a tres por operando. EOF
  cae en el mismo clasificado como no-dígito. Salida: siempre newline final,
  ceros a la izquierda suprimidos, desborde con `'1'` inicial.
- **Truco de representación:** un dígito decimal se codifica como **pareja de
  ciclos xlat2 acoplados de tamaño 5 y 2** (HIGH + LOW). El de 2 lleva la
  paridad (0/1) y el de 5 las "decenas de dos" (0..4) → 10 estados con
  `lcm(2,5)=10`. No existe un ciclo de tamaño 10 porque LMAO valida cada ciclo
  contra xlat2. Es la sustitución exacta del clasificador de 2 ranuras
  (`SLOT0_FLAG`/`SLOT1_FLAG`) que hoy limita CMP_LT/CMP_GT a `{0,1,2}`.
- **El carry ya existe:** la bandera `OVERFLOW` (ciclo de 2) se genera al
  pasar un HIGH por `MovD` o cuando ambos LOW están en `MovD`, y se consume al
  inicio del dígito siguiente, de LSD a MSD.
- **Pieza clave para el borrow:** la subrutina `decrement_value` es el **único
  detector de subdesborde ternario (C0→C2)** del fichero, y lo reporta al
  llamador por `NO_MORE_CARRY_FLAG` con **tres ranuras de retorno**, una de
  ellas libre. Un borrow es exactamente ese evento.

### Ruta recomendada (la más barata de las tres)

1. Leer cada operando como dígito decimal 0..9 en la pareja de ciclos 5+2
   (lector reutilizable verbatim).
2. **Complementar a 9 los dígitos de `b`**, sumar con acarreo de entrada 1 y
   acarreo de extremo circular, y leer el carry final:
   `carry-out = 0 ⟺ a < b`. Así se reutilizan **enteros** los sumadores por
   dígito del adder (LSD → MSD, que es la dirección correcta para un borrow).
3. Emitir `01`/`00` con la técnica de decrementar desde `'9'` (`9 − d`).
4. Clonar los operandos antes de destruir los ciclos de N1 (clonadoras ya
   escritas en el ejemplo).

**Lo que no existe y habría que escribir:** una rutina que *decremente* la
pareja 5+2 en 1 e informe el wrap. Todo el fichero solo **avanza** ciclos; los
`clear` resetean a 0, no restan.

## 4. Por qué E3 + E4 juntos cambian el plan de (b)

E3 midió que LMAO se ahoga en **flags de código**. E4-bis midió que el emisor
nativo **no necesita flags nuevos**: emite recetas rectilíneas sobre literales,
y E3 demostró que las **celdas de datos son baratas** (64 caben). Es decir: el
emisor nativo no paga exactamente el coste que rompe a LMAO.

La imagen unificada (loader + aritmética + comparación) pasa de "bloqueada en
dos rutas" a un **camino híbrido acotado**: rutas aritméticas y de comparación
emitidas en nativo (gate `mb_ref` + loader estricto), cargador/PC mantenido con
LMAO. Restricción heredada, ya medida: el emisor nativo no tiene noción de PC
de programa almacenado, así que la parte (a) — cargar byte-code en RAM — sigue
siendo de LMAO.

## 5. Siguiente experimento (E5)

**Imagen nativa mínima de 2 rutas (ADD + CMP_EQ)** con la clave `c=34, rot=7`,
gateada con `oracle/mb_ref` (loader estricto) y con `loader_cells`. Si dos
rutas pasan el loader estricto, el híbrido queda demostrado antes de intentar
tres. Requiere portar `constants.py` + `best_ops` (metodología; el repo fuente
es MIT) y el gate.

Riesgo conocido a verificar en E5: la colocación disjunta de arenas — este
barrido mide la aritmética de direcciones por ruta, no la colocación
simultánea.

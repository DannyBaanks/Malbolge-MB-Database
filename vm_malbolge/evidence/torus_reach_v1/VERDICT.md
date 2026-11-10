# torus_reach_v1 — álgebra de alcanzabilidad de palabras (CRAZY/ROT)

Pack de evidencia. Committed and pushed on `master`; every number below comes from
`stdout.raw.txt` / `results.json` in this directory.

## Objetivo

Cerrar con medición la pregunta del brief COMPOSE/TORUS-REACH-01: **¿es posible
construir los estados necesarios (en particular `59048` = diez trits iguales a 2,
y `29524` = diez trits iguales a 1) a partir de las constantes y operaciones
realmente disponibles, sin introducir clandestinamente el mismo estado?**

## Modelos separados

| Nivel | Estado | Operador | Restricción |
|---|---|---|---|
| A | una palabra de 10 trits | `crazy(a, v)`, `rot(v)` | ninguna |
| B | palabra + cadena de procedencia | idem | `IMG`/`IN`/`ROT`/`CRAZY`, nada precargado |
| C | ejecución nativa Classic Malbolge | idem + loader, cifrado, `d`/`c`/`a` | precondiciones declaradas |

## Resultado central: la dependencia circular es real, y es satisfiable

Lema verificado por enumeración exhaustiva de los 9 pares de trits (prueba
completa porque las identidades son por-trit) más 200 000 palabras aleatorias:

```
D(crazy(a, v)) = (D(v) - D(a)) U (N(v) & D(a))        ⊆ D(a) U D(v)
N(crazy(a, v)) = ((Z(v) | N(v)) & Z(a)) | (D(v) & D(a))
Z(crazy(a, v)) = (Z(v) & (D(a) | N(a))) | (N(v) & N(a))
D(rot(v))      = {i-1 mod 10 : i ∈ D(v)}   (rot^10 = identidad, exhaustivo)
```

`D/N/Z` = posiciones con trit 2/1/0. Lectura: **un trit 2 nunca aparece en una
posición donde ninguno de los dos operandos tenía un 2**. Esa es la dependencia
circular exacta que aparecía en el análisis textual, y **no es una imposibilidad**:
el acumulador `a` es una fuente independiente de trits 2, y `ROT` los recoloca.
Una sola constante imprimible con un trit 2 (`54 = 2000_3`) cubre las 10
posiciones por rotación.

## Testigos (verificados por replay contra el oráculo del repo, no contra el solver)

| Objetivo | Camino | Pasos |
|---|---|---|
| `29524` (diez 1s) | `crazy(54, 54)` | 3 |
| `0` | `crazy(29524, 29524)` | 6 |
| `P_p` (2 en p, 0 fuera) | `rot^((3-p) mod 10)(54)` | 1..10 |
| `Q_S` (2s en S, 1s fuera) | inducción `crazy(P_q, Q_S)` | 1023 subconjuntos, 0 fallos |
| `U_S` (2s en S, 0 fuera) | `crazy(29524, Q_S)` | idem |
| `F_T` (1s en T, 0 fuera) | inducción `crazy(U_{Z\{p}}, F_T)` | 1023 subconjuntos, 0 fallos |
| palabra cualquiera `w` | `crazy(U_{D(w)+Z(w)}, F_{N(w)+D(w)})` | 209 palabras, 0 fallos |
| **`59048`** (diez 2s) | `crazy(29524, Q_all)` (la ruta `U_all` sería circular) | 1038 |
| **`59048`** compacto | `crazy(58806, crazy(242, crazy(54,54)))` | 7 |
| **`59048`** fiel a la VM | escritura exacta de byte (v3) + 5 `ROT` + `crazy(54,54)` + `crazy(58806, 29645)` | 11 |

`58806 = rot^5(242)` (2s en 5..9), `29645 = crazy(242, 121)` (2s en 0..4, 1s en
5..9), `242` = byte de entrada. El testigo fiel a la VM sólo presupone la
escritura exacta de bytes demostrada en `epoch_algebra_v3` (máscara 121 en la
celda, payload por el acumulador).

## Componente cerrada (H1/H2)

`{0, 29524}` es cerrado bajo el operador **restringido** (operandos dentro del
par). Con máscaras externas autorizadas (byte 0 por `IN`, o la constante 54) el
0 deja de ser sumidero: el cierre hacia atrás de `29524` con la biblioteca
declarada (iniciales + rotaciones, 1696 máscaras) cubre **las 59049 palabras**,
y una muestra de 5000 palabras aleatorias alcanza `29524` en ≤ 2 pasos
(histograma `{0:1, 1:2315, 2:2684}`). No hay prisión toroidal: la intución
toroidal es correcta para `ROT` (ciclo Z_10 sobre posiciones) pero la salida
viene del acumulador.

## Relleno de memoria (medido, no supuesto)

`mem[i] = crazy(mem[i-1], mem[i-2])` más allá del programa, **confirmado por el
runner C original** en 5 direcciones (1200, 1294, 1300, 58000, 58900), 3 motores
coincidentes. La predicción de relleno con cero queda refutada en 3 de 5 casos:
**no hay celdas cero gratuitas**, la palabra 0 debe construirse
(`crazy(29524, 29524)`).

## Upgrade de máscara (cuánto compra `29524`)

| Máscara en la celda | Palabras con doble-CRAZY involutivo |
|---|---|
| `121` (v3, imprimible) | 7776 / 59049  (= 3^5 · 2^5) |
| `29524` (diez 1s, construir en runtime) | 59049 / 59049 |

Primer contraejemplo de 121: `486 = 0000200000_3`. Este es el camino de upgrade
del resolvedor de épocas: `29524` se construye con una sola CRAZY desde dos
celdas que contengan `54` (byte imprimible), así que no hace falta depender del
relleno.

## Controles (los 6 mutantes del brief, todos rechazados/detectados)

| # | Mutante | Cómo se rechaza |
|---|---|---|
| M1 | `crz[4]` alterado (0→1) | diferencial nativo: predice 84, el runner C emite 57 (0x39) |
| M2 | rotación en dirección equivocada | diferencial nativo: predice 99, el runner C emite 11; `rot^10` sigue siendo identidad, por eso no se detecta por ciclo |
| M3 | `35` leído como `1012_3` | round-trip: 1012_3 = 32 ≠ 35 |
| M4 | `59048` precargado | cadena de procedencia: el testigo con `PRELOAD` es inválido; el legítimo usa sólo IMG/IN/ROT/CRAZY |
| M5 | decodificador de opcodes ciego a posición | traza del resolvedor v3: el mutante emite `f9233f`, el oráculo `3f` |
| M6 | verificador que sólo mira la escritura | sobre `mutant_residue` @223: escritura exacta = True pero OUT fuera de la época → el verificador débil acepta y el completo rechaza |

## Respuesta al criterio final del brief

**A + E, con B medido.** El bloqueo era una estrategia de construcción (A): la
dependencia circular existe pero es satisfiable usando el acumulador como fuente
de trits 2 y `ROT` para reposicionarlos. Existe una ruta completa, verificable y
ejecutable al nivel del álgebra de palabras (E): toda palabra es alcanzable, con
testigo constructivo. La ejecución nativa autónoma de esos testigos (C17/C18) es
el experimento acotado siguiente — las precondiciones ya están identificadas
(colocar un byte en una celda: demostrado en v3; recargar `a = 29524`: se resuelve
re-derivando desde dos celdas con `54`, pues `CRAZY` fija `a` al resultado).

## Reproducción

```bash
cd <repo>
python3 vm_malbolge/evidence/torus_reach_v1/probe.py      # exit 0
python3 vm_malbolge/evidence/torus_reach_v1/manifest.py    # manifest.json
```

Dependencias medidas: `tools/oracle_classic.py`,
`runners/malbolge-original/malbolge`,
`vm_malbolge/tools/native_classic/constants.py`,
`third_party/lmao/src/malbolge.c`, y los `.mb` de `epoch_algebra_v3`.

## Estado de claims

Ver `results.json` (sección `claims`): C01–C14 `DEMONSTRATED`, C15–C16
`DESTROYED`, C17–C18 `NOT_DEMONSTRATED`.

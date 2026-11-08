# v3 — Resolvedor de épocas en runtime: selección por puntero, escritura exacta y salto

## Hipótesis y resultado

H1: en una única VM Classic, una solicitud recibida por `stdin` durante la ejecución
puede (a) seleccionar una celda de época entre varias alineadas a 94 de separación,
(b) escribir en ella el valor **exacto** recibido, sin ramas ni comparaciones por
valor, y (c) saltar a esa celda para ejecutarla. H0: alguna de estas propiedades falla.

**PASS** en las tres épocas (36, 130, 224) y con tres motores independientes
(trazador Python sobre las primitivas del oráculo del repo, oráculo Python del repo y
runner C original). 18 pasos, salida `3f`, y el runner C añade su `0x0a` final
(`3f0a`). La escritura es exacta para **los 256 valores de byte** en las tres épocas
(768 casos, 0 discrepancias). Los cinco controles negativos fallan como se espera.

## Mecanismo

La petición son **dos bytes**: `b` (byte de petición) y `V` (payload). La celda de
época se elige por puntero: `T = b + 1`, de modo que `b = 35 → T = 36`,
`b = 129 → T = 130`, `b = 223 → T = 224`. Las tres celdas están a 94 de separación y
comparten residuo (`36 mod 94`), así que el mismo byte de payload decodifica al mismo
opcode en las tres.

**Álgebra de la escritura exacta.** `crazy(crazy(V,m),m) = V` exige que *la celda*
contenga `m` en los dos pasos. Con la tabla de trits canónica
`TRI[y][x] = {(1,0,0),(1,0,2),(2,2,1)}`, la fila `TRI[1] = (1,0,2)` es la transposición
`(0 1)` que fija el 2 (involutiva en todo trit), `TRI[0] = (1,0,0)` manda `2 → 0 → 1`
(solo falla si el trit del valor es 2) y `TRI[2] = (2,2,1)` manda `0 → 2` (solo falla si
el trit del valor es 0). Para un valor de **byte** (0..255) solo hay trits no nulos en
0..5 y el trit 5 vale 0 o 1, luego la máscara `m = 121 = 11111_3` (trits 0..4 en 1,
trit 5 en 0) es una involución válida para **todo** byte: en los trits 0..4 manda la
fila 1 y en el trit 5 manda la fila 0, que es involutiva sobre {0,1}. `C1 = 29524`
(tots els trits en 1) también sirve, pero **no es imprimible** y el loader Classic
exige celdas fuente imprimibles; de ahí `121`.

La doble aplicación necesita **dos celdas distintas**, porque la celda destino es
también el operando: la primera aplicación deja el intermedio en un *scratch* y la
segunda lee la máscara que sigue intacta en el destino. Ese detalle es lo que fallaba
en el intento anterior (`gen_resolver.py`, `MASK=121` sobre la misma celda): con la
célula destino ya ocupada por el intermedio, `crazy(V',V')` no es la involución de la
máscara y el puntero quedaba corrupto (`35 → 31`).

Secuencia (18 pasos; `d` avanza +1 por instrucción y `DLOAD` hace `d = mem[d]`):

| pc | op | efecto | d después |
|---:|---|---|---|
| 0 | DLOAD | `d = mem[0] = 40` | 41 |
| 1 | DLOAD | `d = mem[41] = 44` | 45 (= `W`) |
| 2 | IN | `a = b` | 46 |
| 3 | DLOAD | `d = mem[46] = 46` | 47 (= scratch de petición) |
| 4 | CRAZY | `mem[47] = crazy(b,121) = b'` | 48 |
| 5 | DLOAD | `d = mem[48] = 44` | 45 (= `W`) |
| 6 | CRAZY | `mem[45] = crazy(b',121) = b` **(puntero exacto)** | 46 |
| 7 | IN | `a = V` | 47 |
| 8, 9 | NOP | relleno | 49 (= scratch de payload) |
| 10 | CRAZY | `mem[49] = crazy(V,121) = V'` | 50 |
| 11 | DLOAD | `d = mem[50] = 44` | 45 (= `W`) |
| 12 | DLOAD | `d = mem[45] = b` | `b+1` (= `T`) |
| 13 | CRAZY | `mem[T] = crazy(V',121) = V` **(payload exacto)** | `T+1` |
| 14 | DLOAD | `d = mem[T+1] = 44` | 45 (= `W`) |
| 15 | JMP | `c = mem[45] = b` → ejecución en `b+1 = T` | 46 |
| `T` | OUT | payload ejecutado: opcode `(V+T) mod 94` | |
| `T+1` | END | `44` → opcode `(44+T+1) mod 94 = 81` | |

El puntero se restaura **sin ramas**: después de escribir en `T`, `d = T+1` y la celda
`T+1` vale `44 = W-1`; el `DLOAD` sobre ella devuelve `d = 45 = W` y el `JMP` lee
`mem[45] = b`. La misma celda `T+1` sirve después como `END` (su opcode es 81 en las
tres épocas, porque 94 no cambia el residuo). No hay ninguna comparación por valor:
la única decisión es la dirección física leída del puntero.

## Paso 1 — celdas alineadas a 94

| celda | residuo | opcode de 63 | opcode de 0 |
|---:|---:|---:|---:|
| 36 | 36 | 5 (OUT) | 36 |
| 130 | 36 | 5 (OUT) | 36 |
| 224 | 36 | 5 (OUT) | 36 |
| 223 (control) | 35 | **4 (JMP)** | 35 |

El mismo payload `63` produce `OUT` en las tres celdas alineadas y **no** en la celda
desalineada: la alineación a 94 es lo que hace que la época sea un concepto y no un
adorno.

## Paso 2 — escritura exacta sin ramas por valor

Barrido exhaustivo `V = 0..255` en las tres épocas, comprobando en la traza que la
escritura en la celda de época va de `121` a `V` **exactamente**:

| época | casos | discrepancias |
|---:|---:|---:|
| 36 | 256 | 0 |
| 130 | 256 | 0 |
| 224 | 256 | 0 |

No hay ramas: el control de flujo no depende de `b` ni de `V`; solo del puntero.

## Paso 3 — traza de la dirección física usada

Traza del caso nominal (`b = 35`, `V = 63`), con las cuatro escrituras CRAZY:

| paso | dirección | valor anterior | valor nuevo | celda |
|---:|---:|---:|---:|---|
| 5 | 47 | 121 | 29501 | scratch de petición (`crazy(35,121)`) |
| 7 | 45 | 121 | **35** | puntero (`b` exacto) |
| 11 | 49 | 121 | 29542 | scratch de payload (`crazy(63,121)`) |
| 14 | 36 | 121 | **63** | celda de época (payload exacto) |

El `OUT` se emite en `pc = 36` / `130` / `224` respectivamente (`out_pcs`), es decir
que la celda escrita es **la misma** que se ejecuta; el puntero en `mem[45]` vale
exactamente el byte de petición y la celda sucesora vale `44` con opcode 81 (`END`).
La dirección usada es física, no una equivalencia modular: el control `mutant_residue`
escribe y salta a 223 (residuo 35) y ahí el mismo payload deja de ser `OUT`.

## Paso 4 — controles negativos

| control | cambio | resultado medido | detectado |
|---|---|---|---|
| `mutant_residue` | tercera época en 223 (residuo 35) | 36 y 130 emiten `3f`; 223 recibe 63 exacto pero su opcode es 4 (JMP) y no emite | sí |
| `mutant_journal` | scratch de payload con máscara 122 | la celda de época recibe **65** en vez de 63; ninguna época emite | sí |
| `mutant_pointer` | celda del puntero con máscara 122 | el puntero queda en 122/131/224 (no es `b`); **no hay ninguna escritura** en la celda de época | sí |
| `mutant_mask` | tercera época con máscara 122 | la tercera época escribe 65 sobre una máscara 122; solo falla la tercera época | sí |
| `mutant_target` | `DLOAD` final apunta a otro bloque | la celda de época conserva 121 (no se escribe); 45 pasos, sin salida | sí |

En las 144 filas (6 imágenes × 3 épocas × 8 payloads) el trazador, el oráculo del repo y
el runner C original coinciden byte a byte.

## Alcance y NOT_DEMONSTRATED

- **Una petición por ejecución.** La escritura consume la máscara de la celda de época
  (`121 → V`); una segunda petición a la misma época en la misma ejecución calcularía
  `crazy(V',V)` y no `V`. El rearm con journal y diez `ROT` está demostrado en
  `epoch_journal_state_v2` para una celda fija; **componer** ese rearm con la
  selección de época por puntero es `NOT_DEMONSTRATED`.
- **Payload imprimible para ejecutar.** La escritura es exacta para cualquier byte,
  pero el runner C solo ejecuta celdas imprimibles: con `V = 0` o `V = 255` el
  ejecutor se detiene (el oráculo del repo, que no comprueba printabilidad, continúa;
  divergencia conocida y acotada a esos casos).
- **Modelo de entrada por lotes.** Con el runner C no se observa salida antes de cerrar
  `stdin` (`NO_OUTPUT_1S` medido el 2026-11-07); la integración verificada es por
  lote o entrada completa.
- **Sin búsqueda general de transiciones.** El mapa petición → época es la aritmética
  `T = b+1`: la dirección es el dato, no el resultado de un búsqueda. No hay
  síntesis de transiciones, ni escritura a dirección arbitraria elegida por
  exploración, ni ABI general de llamada/retorno.
- **Loader.** La imagen se construye byte a byte, no con LMAO: el experimento exige
  colocación absoluta de las celdas de época (36/130/224) y de las celdas de máscara
  (121, imprimible), y LMAO coloca las celdas de datos con un stub de arranque que
  reescribe `d` y `c`. El loader estricto de PureEpoch (`tools/trace_ref.c`) rechaza
  esta imagen porque las celdas de datos no decodifican a opcodes válidos en sus
  direcciones; la evidencia usa el oráculo del repo (exige solo printabilidad) y el
  runner C original. Comprobación estática de la fuente: todos los bytes imprimibles,
  sin espacios (`integrity` en `results.json`).
- **Sin rearm, sin escritura fuera de la imagen y sin comparar valores**, la selección
  de época es un caso particular del "resolvedor" general: queda por demostrar la
  búsqueda/síntesis de la transición y la dirección dinámica elegida por búsqueda.

## Reproducir

```bash
python3 vm_malbolge/evidence/epoch_algebra_v3/build.py vm_malbolge/evidence/epoch_algebra_v3
python3 vm_malbolge/evidence/epoch_algebra_v3/probe.py
```

`probe.py` rehace las imágenes, verifica que las instancias conservadas coinciden
byte a byte con `build.py`, ejecuta los tres motores, rehace el barrido de exactitud
y sobrescribe `results.json` y `stdout.raw.txt`. Copiar el pack antes de repetir si
se quiere conservar la evidencia original.

# Celda-puntero escrita en runtime — salida del bloqueante de la pila

## Resultado

`vm_malbolge/tools/pointer_cell_rt_gen.py` emite dos imágenes de **256 bytes,
sin LMAO**:

| artefacto | sha256 | papel |
|---|---|---|
| `vm_malbolge/src/mbir_pointer_cell_rt.mb` | `1fb3eba2751c9678d797fb8622a610924327e2c1cb4ed52e53fda3a2d30350f9` | positivo |
| `vm_malbolge/src/mbir_pointer_cell_rt_ctrl.mb` | `6a5c1ecbcd4bf26f563a3b3d0fdfd16a52f6eeca1bb505a98c7fa5caff079a4b` | control `CRAZY→NOP` |

La imagen positiva escribe una celda-puntero **durante la ejecución** (`CRAZY`
sobre `P`), y un `MOVD` posterior usa el valor escrito como dirección. La salida
es `f0`; el control, con los mismos `CRAZY` sustituidos por `NOP`, lee otra celda
y emite `d4`. **9/9 variantes** (positivo y control, oráculo y runner C) con
acuerdo byte a byte.

## El bloqueante que ataca

`stack2_oneshot.md` (líneas 68-78) demostró que, dentro de la primitiva de
restauración por 2-ciclo, **una celda no puede escribirse y leerse en el mismo
ciclo**: `CRAZY` (escritura) y `ROT` (lectura) dejan ambos `d = S`, comparten las
celdas-puntero `(S+1, S+2)` y los valores que necesitan no pueden coincidir. La
salida documentada era una celda-puntero escrita en runtime.

Esta imagen construye exactamente esa salida, en un programa **one-shot** (sin
bucle, sin LMAO). El truco: la escritura y la lectura no compiten por el mismo
ciclo; la escritura se repite en `s` bloques y la lectura se difiere al final.

## Programa

Con `V(k) = ((7-k) mod 94) + 33`, `P = V(k)` y `s` bloques:

```
k x NOP
k:          MOVD      d = V(k) = P
bloque x s: MOVD      d = mem[P+1] = K-1
            ROT       mem[K] = rot(mem[K]); a = mem[K]
            MOVD      d = mem[K+1] = P-1
            CRAZY     mem[P] = crazy(a, mem[P])
final:      MOVD      d = mem[P+1] = K-1
            ROT       mem[K] = rot(mem[K])
            MOVD      d = mem[K+1] = P-1
            MOVD      d = mem[P] = T          <- celda escrita en runtime
            ROT       a = rot(mem[T+1])
            OUT
            HALT
```

Semántica (verificada contra el oráculo, no supuesta):

- `ROT` escribe `mem[d] = rot(mem[d])` y deja `a = mem[d]`; por eso `mem[K]`
  itera `rot^i(vK)` en la i-ésima vuelta.
- `CRAZY` escribe `mem[d] = crazy(a, mem[d])`; la i-ésima vuelta aplica
  `f_i(x) = crazy(rot^i(vK), x)` sobre `mem[P]`.
- Tras `s` bloques, `mem[P] = T = f_s(...f_1(v0))`.
- El `MOVD` ejecutado con `d = P` lee `T` y el incremento automático deja
  `d = T+1 = M`; el `ROT` siguiente lee el marcador `w` en `M` y `OUT` emite
  `rot(w) & 255`.
- **Control negativo:** con `CRAZY→NOP`, `mem[P]` sigue siendo `v0`, el mismo
  `MOVD` deja `d = v0+1 = N` y el `ROT` lee el marcador `u`. Si la salida
  cambia, el cambio de `d` lo causó la escritura en runtime, no otra cosa.

## Layout primario

| parámetro | valor |
|---|---|
| `s` bloques | 5 |
| `k` NOPs | 12 |
| `P = V(k)` | 122 |
| `K` (celda semilla) | 71 |
| `vK` | 121 |
| `v0` | 53 |
| `T` | 134 |
| `M = T+1` | 135 |
| `N = v0+1` | 54 |
| `ncode` | 40 |
| `w` / `u` | 40 / 44 |
| salida positivo / control | `f0` / `d4` |
| pasos | 40 (positivo), 40 (control) |

Celdas de dato: `{P: v0, P+1: K-1, K: vK, K+1: P-1, M: w, N: u}`. El loader
estricto exige que **todas** las celdas de la imagen (código y dato, 256)
decodifiquen a un opcode válido en su propia dirección; el emisor lo comprueba
celda a celda antes de escribir.

## Búsqueda

- 74 soluciones con loader estricto completo, **todas con `s = 5`**.
- 10 salidas positivas distintas (`0b,0c,0d,0e,d3,d4,ee,ef,f0,f1`) y controles
  distintos de su positivo.
- `M` en `[122,159]`.
- Barrido `s = 1..8` sobre las 94² semillas imprimibles: `T+1` cae en rango de
  imagen solo con `s = 5` (188 pares); con `s ≠ 5`, 0. No es un sesgo de
  búsqueda: es la aritmética de `rot`/`crazy` sobre semillas imprimibles.
- La imagen es explícita de 256 celdas, de modo que el loader no genera nada por
  la regla de expansión.

## TRAMPA MEDIDA: el runner C y el byte `0x0d`

El runner C añade **un `0x0a`** al final de stdout. Normalizar con
`endswith(b"\r\n")` es incorrecto: si el programa emite `0x0d`, la salida real es
`0d 0a` y el recorte CRLF **se come el byte emitido**. En la primera pasada, las
dos únicas variantes con salida `0x0d` (v1 control y v3 positivo) aparecieron
como fallo con stdout vacío; el oráculo y el `stderr` del runner ya decían
`HALTED`. La comparación correcta es `crudo == esperado` o
`crudo == esperado + b"\n"`; el emisor registra ahora `runner_*_crudo` en el JSON.

Ninguna evidencia anterior de este repo queda invalidada: sus salidas
(`6368`, `6769`, `78`, `52`, `0b`, `48`,…) no contienen `0x0d`. Pero cualquier
verificación futura que emita `0x0d` con el recorte CRLF sería un falso negativo.

## Alcance y NOT_DEMONSTRATED

- **Demostrado:** la primitiva one-shot. Una celda que empieza en `v0` y que un
  `CRAZY` transforma es leída después por un `MOVD` como dirección; el control
  con `CRAZY→NOP` sigue otra ruta y emite otro byte. Doble motor, 9/9.
- **NOT_DEMONSTRATED:** la integración de esta primitiva en el **bucle de pila**
  iterado. El one-shot no paga el muro de restauración por 2-ciclo; un bucle
  necesita además que la celda escrita se reponga entre iteraciones, y eso no se
  ha construido aquí.
- **NOT_DEMONSTRATED:** otros `s` con imágenes mayores. El barrido se hizo con
  imagen explícita de 256 celdas y `s = 1..8`; no se exploró `LEN > 256`.
- **NOT_DEMONSTRATED:** que las 74 soluciones agoten el espacio. La búsqueda
  fija la forma del programa (bloques `MOVD/ROT/MOVD/CRAZY` + lectura final) y
  elige el primer `(k, K)` válido por cadena; no barre formas alternativas.

## Reproducir

```
python3 vm_malbolge/tools/pointer_cell_rt_gen.py
```

El emisor reescribe las dos imágenes, ejecuta cada variante en
`tools/oracle_classic.py` (`stop_on_eof=True`) y en
`runners/malbolge-original/malbolge`, y escribe
`vm_malbolge/evidence/pointer_cell_rt.json`.

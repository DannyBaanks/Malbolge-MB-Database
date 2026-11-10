# epoch_mask_native_v1 — imagen Classic AUTÓNOMA que fabrica 29524 y 59048 en runtime

Primera imagen Classic Malbolge que **construye palabras de 10 trits en memoria sin
stdin**, usando sólo lo demostrado antes: la semántica medida del repo
(`tools/oracle_classic.py`, runner C original) y el resultado algebraico de
`torus_reach_v1` (`29524 = crazy(54,54)`, y que un trit 2 se añade con
`crazy(P_q, Q_S)` donde `P_q` es una rotación de una constante imprimible con un 2).

## La observación que hace autónomo el arranque

En Classic Malbolge **`a` arranca en 0** y `DLOAD` no toca `a`. La primera
instrucción útil puede ser por tanto un `CRAZY` con `a = 0` sobre una celda
imprimible **sin ningún trit 2**:

```
crazy(0, v) = 29524   si v no tiene ningún trit 2
```

(por trit: `crz[0][0] = 1` y `crz[1][0] = 1`; `crz[2][0] = 2`, excluido).
La celda 36 (`1100_3`) sirve; también 37, 39, 81, 82, 84, 90, 108, 109, 111, 117…
No hace falta stdin ni ninguna celda cero: **el 0 ya está en `a` al empezar**.

## Imagen (43 bytes, todas imprimibles, sin bucles ni saltos)

```
celdas de dato:  40 = 54 (2000_3, un trit 2)   41 = 36 (1100_3)   42 = 39 (reenvío)

pc  0  DLOAD  d = mem[0] = 40                       -> d = 41
pc  1  CRAZY  a = 0  -> mem[41] = crazy(0,36) = 29524 ; a = 29524   -> d = 42
pc  2  DLOAD  d = mem[42] = 39                      -> d = 40   (= P)
pc  3  ROT    mem[40] = rot(54) = 18 ; a = 18        -> d = 41   (= Q)
pc  4  CRAZY  mem[41] = crazy(18, 29524) = 29542     -> d = 42
pc  5  DLOAD  (misma celda de reenvío)  ... repetido 10 veces
pc 32  OUT    emite a % 256
pc 33  END
```

Diez bloques desenrollados de 3 instrucciones. Los `ROT` desplazan el trit 2 hacia
abajo (3 → 2 → 1 → 0 → 9 → … → 4), así que los diez bloques cubren las diez
posiciones y

```
29524 + (3^0 + 3^1 + ... + 3^9) = 29524 + 29524 = 59048
```

## Resultados medidos (3 motores, `stdout.raw.txt`)

| Instancia | `mem[41]` final | OUT | pasos | estado |
|---|---|---|---|---|
| `mask_native` (10 bloques) | **59048** | `a8` (168 = 59048 % 256) | 34 | HALTED |
| `bootstrap_only` (0 bloques) | **29524** | `54` ('T' = 84) | 2 | HALTED |

Traza física de la instancia buena: primera escritura en 41 = `36 → 29524`
(paso 2), 11 escrituras sobre la celda 41 (1 bootstrap + 10 bloques), `OUT` en el
PC previsto. Los tres motores coinciden byte a byte en las 6 instancias.

## Controles negativos (los 4 divergen donde deben)

| Mutante | `mem[41]` | OUT | Qué prueba |
|---|---|---|---|
| `mutant_boot_has_trit2` (celda 41 = 62, con trits 2) | 59017 | `89` | el bootstrap exige una celda sin trit 2 |
| `mutant_rot_src` (celda 40 = 36, sin trit 2) | 29488 | `30` | sin un 2 inicial no se crea ningún 2 |
| `mutant_forward` (celda 42 = 100) | 29524 | `74` | el reenvío de `d` es load-bearing |
| `mutant_nine_blocks` (9 bloques) | 59021 | `8d` | faltan exactamente las diez posiciones |

## Qué habilita esto

La celda 41 queda con **29524 = la única máscara involutiva para toda palabra de
10 trits** (`torus_reach_v1`: 59049/59049 palabras, frente a 7776/59049 de la
máscara imprimible 121). Ese es el prerequisite que faltaba para que el resolvedor
de épocas escriba payloads de palabra completa: `crazy(crazy(V,29524),29524) = V`
para cualquier `V`, con la máscara fabricada en memoria por esta imagen.

## Reproducción

```bash
python3 vm_malbolge/evidence/epoch_mask_native_v1/build.py .
python3 vm_malbolge/evidence/epoch_mask_native_v1/probe.py   # exit 0
python3 vm_malbolge/evidence/epoch_mask_native_v1/manifest.py
```

## Pendiente (`NOT_DEMONSTRATED`)

Reusar la celda 29524 dentro de la **misma** ejecución (rearm) y un resolvedor de
épocas con payload de 10 trits seleccionado por `stdin`. La imagen actual es de
una sola tirada y sin bifurcaciones: los diez bloques están desenrollados, no hay
bucle ni salida condicional.

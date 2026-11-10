# c_printable_guard_v1 — el runner C se detiene ante celdas no imprimibles

Cierra la causa raíz que `epoch_resolver_word_v1` dejó como `NOT_DEMONSTRATED`:
la «divergencia» del runner C en la fase final del resolvedor de épocas **no es
una diferencia semántica de Malbolge**. Es una guarda del propio runner.

## El hallazgo

El bucle de `runners/malbolge-original/malbolge` (función `vm_run`) comprueba la
celda señalada por `pc` **antes de decodificar** la instrucción:

```
1cc8  mov  edi,r14d          ; c (pc)
1ccb  add  rbp,0x1           ; steps += 1
1ccf  call mem_get           ; eax = mem[c]
1cd4  lea  edx,[rax-0x21]    ; celda - 33
1cd7  cmp  edx,0x5d          ; 93
1cda  ja   1e5e              ; -> status = terminated ; return
```

Si `mem[pc] ∉ 33..126`, el runner termina la ejecución (mismo destino que el
opcode `END`). El intérprete canónico no hace eso: ejecuta cualquier valor
decodificando `(mem[c] + c) % 94`, y sólo condiciona a la imprimibilidad el
*cifrado posterior* de la celda (`1d30`–`1dae` en el mismo binario).

En `epoch_resolver_word_v1` el pc aterriza en `T = 100`, cuya celda contiene el
payload de 10 trits (`29797`, `29311` o `29554` según la instancia): no es
imprimible, así que el C para ahí sin emitir. Encaja con todos los síntomas
medidos antes: el contador coincide con el del `OUT`, no emite nada, y un `OUT`
inserto justo después de la escritura —en zona de código, imprimible— sí emite
`0x65`.

## Programas mínimos

44 celdas, todas imprimibles, sin ramificaciones. La misma forma aterriza en una
celda de dato (`pc = 41`) cuyo valor se elige a cada lado del rango imprimible:

| instancia | cómo se fija la celda 41 | valor | ¿imprimible? |
|---|---|---|---|
| `guard_high` | `crazy(0, 36)` | `29524` | no (> 126) |
| `guard_low` | `crazy(29524, 29524)` tras el anterior | `0` | no (< 33) |
| `control_seed_33` | semilla directa | `33` | sí (frontera baja) |
| `control_seed_126` | semilla directa | `126` | sí (frontera alta) |

No existe un control `crazy` imprimible: `crazy(0, x)` mapea los trits de `x` a
`{1,2}`, así que su resultado siempre es `≥ 29524`. Por eso las fronteras se
prueban en modo `seed_only`, que aterriza en la misma celda sin pasar por
`CRAZY`.

## Resultado medido

El trazador calcula el paso en que entra por primera vez en una celda no
imprimible; esa es la predicción del paso de parada del C.

| instancia | pivote | primer paso no imprimible | parada predicha | parada del C | coincide |
|---|---|---|---|---|---|
| `guard_high` | `29524` | 4 (`pc = 41`) | 4 | **4** | sí |
| `guard_low` | `0` | 6 (`pc = 41`) | 6 | **6** | sí |
| `control_seed_33` | `33` | — | 6 (hasta `END`) | **6** | sí |
| `control_seed_126` | `126` | — | 6 (hasta `END`) | **6** | sí |

## Reproducción sobre `epoch_resolver_word_v1`

La misma predicción, aplicada a las cuatro instancias ya publicadas, coincide
con el contador del C **exacto**, sin ningún parámetro ajustado:

| instancia | primer paso no imprimible | `pc` | valor | parada del C |
|---|---|---|---|---|
| `resolver_word` | 276 | 100 | 29797 | **276** |
| `resolver_word_dynamic` | 273 | 100 | 29797 | **273** |
| `mutant_mask_121` | 272 | 100 | 29311 | **272** |
| `mutant_wrong_payload` | 176 | 100 | 29554 | **176** |

## Qué cambia y qué no

* **Cambia**: el runner C no es un motor divergente. Es un **runner restringido**
  que se niega a ejecutar celdas no imprimibles. No puede correr un programa que
  ejecute un payload de 10 trits en la celda de época, y eso es una propiedad del
  runner, no del programa.
* **No cambia**: la semántica canónica que sostienen el oráculo del repo y
  `native_classic` (dos motores independientes), y todos los resultados de
  `epoch_resolver_word_v1`.
* **Consecuencia práctica**: el C sigue siendo válido como tercer motor para
  todo programa cuyas celdas ejecutadas sean imprimibles — que es el caso de las
  fases 0–4 del resolvedor, verificadas byte a byte en el pack anterior. Para la
  fase 5 (ejecutar el payload en la celda de época) hay que usar los motores
  canónicos, o un runner sin la guarda.

## Reproducción

```bash
python3 vm_malbolge/evidence/c_printable_guard_v1/build.py .
python3 vm_malbolge/evidence/c_printable_guard_v1/probe.py   # exit 0
```

## Pendiente

* confirmar la guarda en el resto de variantes de runner del ecosistema
  (Malbolge-Engine, lmao) — este pack sólo mide
  `runners/malbolge-original/malbolge`;
* si se quiere el C como tercer motor del resolvedor completo, construir una
  variante sin la guarda (fuera de este pack, que no modifica binarios de
  terceros).

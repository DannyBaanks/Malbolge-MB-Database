# epoch_rearm_primitive_v1 — dos escrituras exactas en UNA ejecución, con rearm de la máscara

Cierra el `NOT_DEMONSTRATED` que quedaba tras `epoch_algebra_v3`: **la máscara se
restaura dentro de la misma ejecución**, así que el resolvedor puede atender una
segunda petición sin reiniciar la imagen.

## Mecanismo

La imagen fabrica la máscara de palabra completa `29524` (diez trits iguales a 1)
y la usa dos veces, restaurándola entre medias:

```
bootstrap   crazy(0, 36) = 29524        (36 imprimible, sin ningún trit 2; a arranca en 0)
fábrica     X → 0, A → 29524, B → 0, hop, B → 29524        (A y B listas, a = 29524)
escritura 1 IN a = V ; CRAZY A (→ swap(V)) ; CRAZY B (→ V EXACTO) ; OUT = V
recarga     ROT sobre S:  29524 es todo 1s, así que es INVARIANTE bajo ROT:
           a = 29524 y la celda S queda intacta (no se consume)
rearm B     CRAZY B (a=29524 → extract2(V)) ; CRAZY B (a=E → 29524)
rearm A     igual sobre A
escritura 2 IN a = V2 ; CRAZY A (→ swap(V2)) ; CRAZY B (→ V2 EXACTO) ; OUT = V2
END
```

Identidades (verificadas en `torus_reach_v1`):

| expresión | resultado |
|---|---|
| `crazy(0, v)` con `v` sin trit 2 | `29524` |
| `crazy(V, 29524)` | `swap(V)` (0↔1, 2 fijo) |
| `crazy(swap(V), 29524)` | **`V`** ← la escritura exacta |
| `crazy(29524, X)` | `extract2(X)` (2 donde X tiene 2, 0 fuera) |
| `crazy(E, E)` con `E` sin trits 1 | `29524` ← el rearm |
| `rot(29524)` | `29524` ← la recarga no consume |

## Resultado medido (tres motores, `stdout.raw.txt`)

| instancia | OUT | `B` antes de escritura 2 | veredicto |
|---|---|---|---|
| `rearm_primitive` | `f2 ff` = [242, 255] | `29524` | **dos escrituras exactas + rearm** |
| `mutant_no_rearm` | `f2 6c` | `242` | sin rearm la segunda escritura falla |
| `mutant_reload_wrong` | `f2 ff` | `29484` | la recarga desde la celda equivocada rompe el rearm |
| `mutant_boot_trit2` | `bc ff` | `29514` | el bootstrap exige una celda sin trit 2 |
| `mutant_write_wrong_cell` | `79 ff` | — | el payload aterriza en la celda equivocada |

Escrituras sobre la celda destino `B` en la instancia buena:
`36→0`, `0→29524`, `29524→242` (escritura 1 exacta), `242→242`, `242→29524`
(**rearm**), `29524→255` (escritura 2 exacta).  43 pasos, 160 bytes, todos
imprimibles, sin saltos condicionales.

## Nota sobre el mutante descartado

Un mutante que falseaba una celda de salto para sacar `d` de la zona de dato
(43 → 77) **divergía entre el runner C y el oráculo**: el C paraba en el paso 11 y
el oráculo seguía. Es comportamiento fuera de contrato (`d` sin envolver), no un
defecto de la imagen: se reemplazó por `mutant_write_wrong_cell`, que mantiene el
recorrido en contrato y sigue discriminando.

## El planificador (`plan.py`)

Como el rutado de `d` era el cuello de botella, `plan.py` simula el recorrido
mientras emite el código y **lanza excepción en cuanto una celda de salto
necesitaría dos valores distintos**. Zonas: código en `0..39`, dato en `41..126`
(todo valor de salto debe ser byte imprimible, por eso los destinos van hasta
127), código en `127+` tras un `JMP` de zona. El `JMP` también avanza `d` en 1
(esa omisión fue un bug real del planificador, cazado por el diferencial).

## Reproducción

```bash
python3 vm_malbolge/evidence/epoch_rearm_primitive_v1/build.py .
python3 vm_malbolge/evidence/epoch_rearm_primitive_v1/probe.py    # exit 0
python3 vm_malbolge/evidence/epoch_rearm_primitive_v1/manifest.py
```

## Pendiente

- **Payloads de 10 trits** (no sólo bytes): la escritura exacta ya funciona para
  cualquier palabra con la máscara `29524`; falta construir el payload en memoria
  desde la petición y seleccionar la celda destino por época (la arquitectura de
  `epoch_algebra_v3` con la máscara nueva).
- **Bucle**: las fases están desenrolladas; no hay salida condicional.

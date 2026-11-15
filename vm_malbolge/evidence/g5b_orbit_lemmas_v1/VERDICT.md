# G5b-0: lemas de rearme por órbita — veredicto

2026-11-15. Base `a8dcd4d`, preregistro `2f9c5f5` (`GATES.md`). Cierra el G5
de restauradores (`code_rearm_multi_v1/G5_DESIGN.md`): sus islas R/R2
resolvían un problema que, para los JMP, no existe, y para el resto de
instrucciones tiene una solución sin restaurador (órbita de fase).

| Puerta | Resultado | Evidencia |
| --- | --- | --- |
| G0 (L1, fuente) | **PASS** | Vendor `olmstead_original.c` (sha `05abd38e…`): línea 122 `case 'i': c = mem[d]; break;` precede a la línea 140 `mem[c] = xlat2[mem[c] - 33];`. El cifrado actúa sobre el destino ya asignado, nunca sobre la celda JMP. |
| G1 (L1, nativo) | **PASS** | Vendor instrumentado (`run02/instr.diff`, solo `fprintf` a stderr). `increment.mb` con 00..ff+EOF: 895 600 JMP en 46 celdas; 895 554 revisitas con la misma palabra, 0 cambios (con o sin escritura de datos). stdout idéntico al nativo (`9bc038d0…`, 256 B, rc 0). `phase_loop` positivo: 932 020 JMP en 3 celdas, 0 cambios; prefijo `41424344a8` idéntico. |
| G2 (L2) | **PASS** | `orbit_table.py`: tablas del probe y `xlat1`/`xlat2` parseados del C coinciden. Órbitas de longitud `[2,4,5,6,9,68]`; una sola de periodo 2, `{70,74}`. Residuos `pc mod 94` (palabra activa): JMP 24(74)/28(70) · OUT 25(74)/29(70) · IN 43(74)/47(70) · ROT 59(74)/63(70) · MOVD 60(74)/64(70) · CRAZY 82(74)/86(70) · HALT 7(74)/11(70). |
| G3a (control L1) | **PASS** | Intérprete mutante que además cifra la celda JMP: `increment.mb` no emite nada y no termina (timeout 120 s); `phase_loop` emite 1 byte y hace HALT. Ambos divergen del nativo. |
| G3b (control L2) | **PASS** | `xlat2` con las dos primeras entradas intercambiadas: el comparador detecta el desacuerdo. |
| G4 | NOT_DEMONSTRATED | Imagen G5b-1, orden arbitrario de instrucciones en línea recta, comparación con HeLL. |

## Consecuencia de diseño

- Un JMP es reutilizable sin coste. Lo que se consume al ejecutar es la celda
  *destino* (debe ser imprimible: con un destino no imprimible el vendor lee
  `xlat2` fuera de rango) y la celda de cada instrucción no-JMP.
- Toda instrucción activa puede rearmarse sola colocándola en uno de sus dos
  residuos con palabra inicial 74 o 70 y recorriéndola dos veces por
  iteración (fase activa + fase NOP). Con órbitas más largas también hay
  residuos de un solo activo (17–20 por opcode), a costa de más pasadas.
- No hace falta isla restauradora por instrucción; la desigualdad de tamaño
  que mató a R/R2 no aplica.

## Hallazgo lateral para el cuerpo G5b-1 (`crazy` no es XOR)

Trit bajo de `crazy(a, d)` (filas `a`, columnas `d`):
`[[1,1,2],[0,0,2],[0,2,1]]`. Solo `a=2` es biyectiva sobre `d` (y es la
negación ternaria `d → −d mod 3`, una involución); ningún byte `k∈[0,255]`
hace de `crazy(k,·)` una involución en 0..255. Un "XOR ternario con clave"
mediante `crazy` no es reversible salvo con clave todo-2 (`59048`), que ya no
es clave sino una permutación fija.

## Negativo registrado

`run01/`: primer intento con el arnés anterior (stdout con búfer y
comparación de stdout completo). `phase_loop` no hace HALT tras EOF
(documentado en `g5_phase_loop_20261112`), el timeout cortó el búfer y la
comparación falló (`run01.lemma_jmp.stderr.raw.txt`). No es contraevidencia
del lema; se corrigió el arnés (stdbuf -o0, prefijo verificado de 5 bytes,
líneas truncadas descartadas) y se repitió en `run02/`. Binarios y logs
grandes de `run01` no se conservan en el repo; sus hashes están en
`run01/bulk_sha256.txt`.

## Reproducción

```sh
python3 vm_malbolge/evidence/g5b_orbit_lemmas_v1/orbit_table.py
python3 vm_malbolge/evidence/g5b_orbit_lemmas_v1/lemma_jmp.py <dir-nuevo-vacio>   # ~2 min, gcc
```

Los logs instrumentados de `run02` están comprimidos (`gzip -n`); el hash del
log sin comprimir está en `run02/bulk_sha256.txt` y en el stdout del run.

## Nota sobre los `.diff`

Los `instr.diff`/`mutant.diff` originales llevaban rutas absolutas de la
estación en las cabeceras (bloqueado por repo-engine `LOCAL_PATH_001`). Se
regeneraron con `diff -u --label` desde los `.c` conservados en cada run; el
cuerpo del diff es idéntico, solo cambian las dos líneas de cabecera.
`lemma_jmp.py` ya emite etiquetas relativas. El stderr de `run01` (traceback)
conserva su ruta tal cual: es salida cruda.

# Empaquetado exacto de destinos: N=4 con el protocolo original y N=5 con bandas adyacentes

## Resultado

Dos imágenes nuevas, **ambas con coste de rotación cero** (ninguna cadena de
`ROT`), ejecutan N instrucciones encadenadas leídas del flujo y dan **9/9** de
acuerdo byte a byte entre `tools/oracle_classic.py` (`stop_on_eof=True`) y
`runners/malbolge-original/malbolge`:

| N | protocolo | V | colas | imagen | bytes | sha256 |
|---|---|---|---|---|---|---|
| 4 | `PUSH 0x35` / `POP 0x41` | 108, 107, 75, 68 | 7, 1, 4, 10 | `vm_malbolge/src/mbir_dispatch4_pack.mb` | 29.580 | `c871ba52…` |
| 5 | `PUSH 0xff` / `POP 0x35` | 81, 44, 45, 54, 73 | 1, 5, 2, 6, 9 | `vm_malbolge/src/mbir_dispatch5.mb` | 29.564 | `f4534600…` |

Evidencia máquina completa (9 casos por imagen, parámetros, destinos, celdas de
código/dato): `vm_malbolge/evidence/dispatch4_pack.json` y
`vm_malbolge/evidence/dispatch5.json`. Emisor reproducible:
`vm_malbolge/tools/dispatch_pack_gen.py`.

## Corrección al bloqueante de `dispatchN.md`

`dispatchN.md` concluía: «con `V` imprimible los destinos viven en ~284 celdas
y con manejadores de ~10 celdas caben como máximo 6 destinos separados 14
(3 parejas)», y por tanto N > 3 quedaba bloqueado por la ventana. La conclusión
no se sostiene; la restricción real era doble:

1. **Separación uniforme 14 entre todos los destinos.** El requisito real no es
   una separación mínima global, sino que los bloques de manejador no se
   solapen. El bloque de un destino `L` (celda de destino incluida, que el
   `JMP` salta) ocupa exactamente

   ```
   push: [L, L+5+t]     código en L+1: IN, NOP, MOVD, CRAZY, t NOP, JMP
   pop:  [L, L+4+t]     código en L+1: NOP, MOVD, ROT, OUT, t-1 NOP, JMP
   ```

   El código mide `5+t` / `4+t` celdas y el bloque completo `6+t` / `5+t`.
   Con colas pequeñas el bloque mide 6–13 celdas, no ~26, y dos destinos pueden
   estar a 12 celdas si el bloque del primero es corto. La pareja
   `(29497, 29509)` de N=4, con separación 12, es legal por eso: su bloque push
   termina en 29503 y el pop empieza en 29509.

2. **Protocolo fijo 53/65 y colas 3k+1.** El protocolo también es una variable
   de diseño. `PUSH=0xff` cae en la banda adyacente: `crazy(op, V)` con
   `op ≥ 243` tiene el trit 5 a 1 y los trits 6–9 a 0, así que la ventana es
   `[29160, 29402]`, contigua a la de `op < 243`, `[29403, 29645]`. La unión
   son **486 celdas**, no 284, y los destinos push/pop pueden repartirse entre
   las dos mitades.

**Regla de choque de celdas-puntero (medida).** Las colas no pueden diferir en
2: la celda del `JMP` del manejador está en `slotA+1+t_i` y la celda de entrada
del despacho siguiente en `slotA+3+t_j`; coinciden si `t_j = t_i + 2`. Las
colas `1,2,5,6,9` (diferencias 1 y 3) y `7,1,4,10` (diferencias 1, 3, 6) son
válidas. `dispatch_pack_gen.py` rechaza explícitamente un conjunto con
diferencia 2.

## Parámetros medidos

**N=4** (`dispatch4_pack.json`): `slotA=82`, `Ps=[96,101,106,111]`,
`stride=15`, destinos

```
D0 push@29484 pop@29541   D1 push@29497 pop@29509
D2 push@29553 pop@29532   D3 push@29563 pop@29515
```

**N=5** (`dispatch5.json`): `slotA=95`, `Ps=[106,111,116,121,126]`,
`stride=15`, destinos

```
D0 push@29269 pop@29484   D1 push@29276 pop@29506   D2 push@29287 pop@29493
D3 push@29296 pop@29538   D4 push@29314 pop@29549
```

Los manejadores de N=4 caben en la misma banda que usaba N=3; los de N=5 se
reparten entre las dos bandas adyacentes. El bootstrap, el HALT y los
`exit_landing` siguen siendo imprimibles (≤ 126): con `stride=15` el HALT de
N=5 queda en 125.

## Búsqueda (reproducible)

`dispatch_pack_gen.py` hace, en este orden:

1. Enumera las parejas `(crazy(push,V), crazy(pop,V))` para
   `V = 33..126` (94 valores imprimibles).
2. Busca el primer subconjunto de N parejas con poda necesaria
   `|L_i - L_j| ≥ 6` y comprueba los bloques exactos `[L, L+5+t]` /
   `[L, L+4+t]` para cada permutación de las colas.
3. Busca `(slotA, Ps)` que cierre la coreografía de `d` con
   `dispatchN_gen.plan`.
4. Ensambla con `dispatchN_gen.build` (celdas de código válidas en su propia
   dirección; las de dato que nunca se ejecutan como instrucción quedan
   contadas en `dato_no_valido`).

Comandos:

```bash
python3 vm_malbolge/tools/dispatch_pack_gen.py --push 53 --pop 65 -n 4 \
  --tails 1,4,7,10 --mb vm_malbolge/src/mbir_dispatch4_pack.mb \
  --json vm_malbolge/evidence/dispatch4_pack.json
python3 vm_malbolge/tools/dispatch_pack_gen.py \
  --mb vm_malbolge/src/mbir_dispatch5.mb \
  --json vm_malbolge/evidence/dispatch5.json
```

## Qué queda medido y qué no

- **N=5 con coste de rotación cero** está demostrado (9/9, imagen y JSON
  commiteados).
- **N=6 con coste cero: excluido en los protocolos de mayor capacidad.**
  `dispatch_pack_bound.py` barre los 3.159 protocolos mixtos
  (`a ∈ [243,255]`, `b ∈ [0,242]`) con la condición necesaria de N=6 (6 parejas
  con los 12 destinos a ≥ 6 celdas): pasan 975. En los 8 de mayor capacidad
  —más los protocolos de control (53,65) y (255,53)— se ejecuta una búsqueda
  exhaustiva de 6 parejas con asignación de colas; todas terminan sin solución,
  incluida (255,242) con 1.103.000 hojas. El verificador de empaquetado acepta
  antes las soluciones commiteadas de N=4 y N=5 (controles positivos), y el
  conjunto de colas probado, (1,2,5,6,9,10), es el mínimo componente a
  componente de todos los conjuntos válidos: cualquier otro solo alarga bloques,
  así que si el mínimo no empaqueta, ninguno lo hace. Evidencia:
  [`dispatch_pack_bound.json`](dispatch_pack_bound.json) (veredicto
  `N6_EXCLUIDO_EN_PROTOCOLOS_MEDIDOS`).
  Queda abierto el barrido exhaustivo de los 975 protocolos que pasan el filtro
  (aquí se comprobaron los 8 mejores) y la vía con rotaciones.
- Por tanto el frente 2 (cadenas de rotación para dispersar destinos) **ya no
  es necesario para N=4 ni para N=5**; sigue siendo la vía general si se quiere
  N ≥ 6, y su coste medido (2 celdas de código por rotación) sigue en pie.

## Reproducción de la verificación

Cada ejecución del emisor imprime los 9 casos con `esperado`, `oraculo`,
`runner_c`, pasos y estado; el JSON guarda la misma tabla. En ambos casos:

```
9/9 casos de acuerdo
```

(`status` HALTED cuando el flujo tiene instrucciones de sobra; EOF cuando se
agota a mitad de una instrucción, igual que el runner C.)

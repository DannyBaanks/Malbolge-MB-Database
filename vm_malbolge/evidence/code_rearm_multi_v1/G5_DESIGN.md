# Diseño G5: bucle de dos restauradores (listo para sintetizar)

2026-11-12. Pack `code_rearm_multi_v1`. Documento de implementación; la imagen
**no está sintetizada todavía**. Convenciones verificadas contra el vendor
Olmstead y contra `constants.py` de BolgeForge.

## Semántica (verificada, corrige una nota previa)

- Instrucción: `op = (valor_celda + pc) % 94` con la tabla rotada de BolgeForge
  (equivalente a `xlat1[(v-33+pc)%94]` del vendor Olmstead). Los números 64, 78
  y cualquier otro fuera de {4,5,23,39,40,62,81} son NOP efectivos en ambos
  motores. Mi nota previa en `loop_feasibility.results.json` usaba caracteres
  de tabla en vez de números y su conclusión "reloj puro N<=2" es inválida; la
  parte de `crazy` de ese resultado no cambia. Queda registrado aquí como
  corrección appended.

## El reloj (hallazgo nuevo, decidido)

Celda sin restaurar en un `pc ≡ 2 (mod 94)` con valor inicial `66`: su orbita
bajo `xlat2` es `[66, 62, 76, 79]`, que decodifica `[68 NOP, 64→NOP, 78→NOP,
81 HALT]`. Ejecutada una vez por iteración: **tres iteraciones completas y
parada limpia en la cuarta**, sin coreografiar nada y sin entrada. La celda
queda excluida de toda restauración.

## Cadena de restauración por celda (de `algebraic_restart` + v4)

Para una celda objetivo `T` con palabra original `w`:

```
ctrl = crazy(w, ONE)                      # ONE = 29524
plantar C = rot^9(ctrl)                   # ROT tiene orden 10
plantar K = 29524                         # punto fijo de ROT
ejecución:  ROT@K -> a=ONE
            DLD -> d=T-1 ; CRAZY(T) -> crazy(ONE, e)=x
            CRAZY(T) -> crazy(x,x)=29524
            ROT@C -> C=ctrl, a=ctrl
            DLD -> d=T-1 ; CRAZY(T) -> crazy(ctrl,29524)=w
```

Válida para cualquier valor (involución sobre los 59049) y para los 94 valores
imprimibles post-ejecución; es idempotente sobre celdas ya prístinas, así que
restaurar dos veces no daña.

## Estructura de la imagen

Tres regiones, todas con celdas de código aisladas y trampolines de punteros
(patrón v4: `T+2=T-1`, `T+3=C-1`, `T+5=T-1`, `T+6=0`, `K+1=T-1`, `C+1=C-1`,
`C+2=T-1`):

1. **B** (cuerpo): 2-4 celdas aisladas con salto encadenado. Una de ellas
   puede ser `OUT` con `a` cargado por ROT sobre una celda `rot^9(byte)` para
   que la corrida nativa deje bytes observables en stdout.
2. **R**: cadena de islas restauradoras, una por celda de R2 y de B. Cada isla
   = el cuerpo de 19 celdas de v4 (`j*jpojpooj*ojpooooi`) con sus datos
   `K`, `C` y vector de arranque de 4 celdas. R no ejecuta objetivos: sólo
   restaura.
3. **R2**: cadena de islas restauradoras para las celdas de R (código) y sus
   celdas de control `C` (que derivan a `ctrl` al usarse).
4. **Reloj** en el camino de retorno tras R2, antes del JMP a la entrada de R.

Flujo por iteración: `R` (restaura R2 + B; R se cifra) → `B` (trabajo; B se
cifra) → `R2` (restaura R + los `C` de R; R2 se cifra) → `reloj` (NOP) →
`JMP` a R. Al reentrar, R y B están prístinas y R2 se restaura en el paso 1:
consistente. El reloj decodifica HALT en la cuarta pasada.

Entrada: reutilizar el patrón de vector de arranque de v4
(`put(S-1,T-1); put(S,ONE); put(S+1,H-1); put(S+2,K-1)` con
`synthesize_preamble_ops(clean, values, S-1, 9003, 0, template_clean=template,
boot='original')`). Todos los destinos de salto deben ser imprimibles (la
trampa que rompió el primer intento de dos celdas en Olmstead).

## Verificación prevista

1. Trazador scratch propio (convención `(v+pc)%94`, crazy/rot/encrypt del
   probe) sobre la imagen: pasos, visitas y escrituras por celda.
2. REA con `event_start_step` tardío + `event_capture_limit` amplio: la
   ventana debe coincidir célda a célda con el scratch.
3. Olmstead nativo: `rc=0` (parada limpia) y stdout esperado del cuerpo.
4. Control G6: suprimir un CRAZY de una isla de R (o de R2) y comprobar que la
   segunda iteración difiere; registrar si la nativa sola lo distingue.
5. Repetición de síntesis en árbol aislado con hashes.

## Comprobaciones estáticas antes de sintetizar

- El reloj elegido decodifica `[68,64,78,81]` en su `pc`.
- Cada `ctrl = crazy(w, ONE)` con `crazy(ctrl, ONE) == w`.
- Cada `e = enc(w)` (imprimible) reinicia a 29524 con `crazy(ONE,e)` y
  `crazy(x,x)`.
- Todo destino de JMP y toda celda ejecutada imprimibles; arranque dentro de
  los 59049 celdas; `fits` del plan <= `source_len-2`.

# Resultados: rearme múltiple, ventana REA y cadena de reinicio uniforme

2026-11-12 (continuación de la sesión de codex). Base `c65b75b`; preregistro en
`GATES.md`. Nada aquí sustituye al veredicto de `increment_stream_v2`.

## 1. REA: ventana de eventos tardía (repo `rea`, commit `32aade1ac`)

`trace_malbolge` acepta `event_start_step` (1-based): los pasos anteriores se
ejecutan igual, sólo cambia qué eventos se retienen. Pruebas nuevas en
`src/domain/malbolge/malbolgeClassic.test.ts` y
`tests/boundary/mcp/malbolgeMcp.test.ts`: la ventana equivale al slice de la
corrida completa, el estado final y la salida no cambian, y una ventana que
empieza tras el HALT queda vacía. Las pruebas de fixture EOF
(`REA_MALBOLGE_EOF_FIXTURE`) pasan con `compiled_relocated.mb` (24/24). Esto
desbloquea verificar los eventos finales de cálculo, que antes quedaban fuera
del límite de captura.

## 2. Operandos reales del ayudante (`trace_helper.py`)

Traza del modelo scratch sobre `multi_v4_positive.mb`, ventana 7080-7160. Los
auxiliares hacen, por celda objetivo:

| Paso | Operación | Efecto |
| --- | --- | --- |
| ROT sobre celda `K` (=29524) | `a=29524` | 29524 es punto fijo de ROT (todos los trits son 1) |
| CRAZY `a=29524`, celda objetivo | `e -> crazy(ONE,e)` | primer reinicio |
| CRAZY `a=x`, celda objetivo | `x -> crazy(x,x)=29524` | segundo reinicio |
| ROT sobre celda `C` (=rot^9(ctrl)) | `a=ctrl` | ROT tiene orden 10: `rot^10(ctrl)=ctrl` |
| CRAZY `a=ctrl`, celda objetivo | `29524 -> want` | restaura la palabra original |

## 3. Cadena de reinicio uniforme para las 48 celdas (`algebraic_restart.py`)

Para las 48 filas de `increment_stream_v2/code_rearm_v2.results.json`:

- `crazy(x,x)==29524` **no** es universal: `crazy(29524,29524)=0`, así que
  sobregirar la cadena rompe el rearme.
- Sin excepción, las 48 filas necesitan **exactamente** un paso intermedio:
  `e --crazy(a=ONE)--> x --crazy(a=x)--> 29524`, y luego
  `--crazy(a=ctrl)--> want` con `ctrl=crazy(want,ONE)`.
- Es decir: el rearme de cualquier celda del bloque es una cadena **fija** de
  3 CRAZY + 1 ROT por parámetro, con dos datos por celda: el PC objetivo y el
  control plantado. El control sigue calculándose en el host
  (`NOT_DEMONSTRATED` selección automática), pero la rutina ya no depende de
  la celda: misma secuencia de operandos para las 48.

## 4. Lo que sigue abierto

- Imagen con rutina genérica: tabla `(pc, control)` en memoria, cadena uniforme
  iterada sobre la tabla, y reejecución del bloque.
- Que la propia rutina se restaure a sí misma (sus celdas también se cifran al
  ejecutarse) para poder repetirse.
- Integrar el detector de EOF de UNIECO (`unieco_bf_compile_v1`,
  `REA_MALBOLGE_EOF_FIXTURE`) y el bucle de longitud arbitraria.
- `code_rearm_multi_v1` cubre 3 celdas aisladas con vecinos de reemplazo; el
  bloque contiguo de 48, el bucle y EOF siguen `NOT_DEMONSTRATED`.

# Bucle de fetch nativo con estado entre bytes — frente 3, hito por vía nativa

## Qué se construyó

`vm_malbolge/tools/native_fold_loop_gen.py` emite, **sin LMAO**, una imagen
Classic de 130 bytes que ejecuta un bucle de fetch real:

```
bucle (vuelta de ~15 pasos por byte):
    IN 43      a = byte de stdin
    MOVD 60    d = 90                (apunta a la celda de estado)
    CRAZY 82   mem[93] = crazy(a, mem[93]);  a = mem[93]
    OUT 119    emite a & 255          (el estado acumulado)
    MOVD 64    d = 67                 (rebobina d y cierra la vuelta)
```

La vuelta **vuelve al mismo punto de despacho (celda 43)** y mantiene una celda
de estado (celda 93) a través de todos los bytes leídos. Termina en EOF: lo para
el runner C (`terminated=1`) y el oráculo con `stop_on_eof=True`.

## La primitiva de bucle (causa raíz, medida)

Traza paso a paso de `simple_cat` + este emisor. En este dialecto:

1. Cada celda ejecutada se cifra tras la instrucción.
2. El cifrado (XLAT2) **no es una involución global**: es una permutación con
   ciclos mezclados. Solo hay **dos valores imprimibles en 2-ciclo**: 70 (`F`)
   y 74 (`J`). Medido: `pares_2ciclo = {70, 74}`, `puntos_fijos = 0`.
3. Cuando la instrucción es un salto, `c` se reasigna al destino **antes** del
   cifrado ⇒ la celda del `JMP` nunca se cifra ⇒ un JMP es estable para siempre.

De ahí la receta (idéntica a la de LMAO, ahora entendida):

| celda | contenido | efecto |
|---|---|---|
| A | instrucción, valor en 2-ciclo | se cifra 1 vez al ejecutarse |
| A+1 | `JMP` → A | la cifra otra vez: **70↔74, queda restaurada** |

La misma celda JMP se ejecuta dos veces por vuelta (restaura, luego salta al
siguiente landing). Consecuencia medible: las direcciones donde cada opcode cae
en 2-ciclo son, mod 94, **MOVD 60/64 · IN 43/47 · CRAZY 82/86 · OUT 119/123**.
Esas son las únicas direcciones utilizables para celdas de trabajo en un bucle.
(`simple_cat` usaba 74 en 2017/1999/2034: mismo fenómeno.)

## Verificación (doble motor)

`run_oracle` = `tools/oracle_classic.py` con `stop_on_eof=True`;
`runner_c` = `runners/malbolge-original/malbolge`.
Salida esperada precalculada: `estado = crazy(byte, estado)` por byte.

| stdin | esperado | oráculo | runner C | pasos | estado |
|---|---|---|---|---|---|
| `A` | `68` | `68` | `68` | 19 | EOF |
| `AB` | `684e` | `684e` | `684e` | 34 | EOF |
| `ABC` | `684e68` | `684e68` | `684e68` | 49 | EOF |
| `HELLO` | `694b624762` | idem | idem | 79 | EOF |
| `12345` | `323230322f` | idem | idem | 79 | EOF |
| (vacío) | — | — | — | 4 | EOF |
| `00 01 02` | `575656` | idem | idem | 49 | EOF |
| 32 bytes `01..20` | `56565756565456534b4a` | idem | idem | 484 | EOF |
| 4.096 aleatorios | fold | — | **exacto** | 61.444 | HALTED |

**9/9 acuerdo byte a byte en ambos motores**, más el volumen de 4 KiB.
Evidencia máquina: `vm_malbolge/evidence/native_fold_loop.json`
(sha256 de la imagen y de la salida esperada incluidos).

## Estandar del loader

- Las 5 celdas de trabajo y sus 5 JMP decodifican a opcode válido en su propia
  dirección (comprobado una auna en el emisor, con `two_cycle` como invariante).
- Las 14 celdas de **puntero** son imprimibles pero **no** decodifican a opcode
  válido en su dirección. Nunca se ejecutan como instrucción ( `c` no las
  visita: recorre solo 0,1,2 y 42..121 ); solo las leen `MOVD`/`JMP` como dato.
  Está listado en el JSON (`punteros_no_validos`). Es la relajación honesta de
  `loader estricto` sobre las celdas de dato de coreografía.

## Lo que abre

1. El bucle de fetch nativo existe y verifica ⇒ el frente 3 deja de estar
   bloqueado por "no hay iteración que heredar".
2. La receta de restauración (2-ciclo + JMP estable) es reutilizable para
   cualquier bucle emitido por esta vía.
3. Lo que falta para la pila de profundidad 2 con despacho por opcode: un
   clasificador sobre el byte leído. Con esta primitiva ya es cuestión de
   encadenar decrementos/pruebas, no de ausencia de bucle.

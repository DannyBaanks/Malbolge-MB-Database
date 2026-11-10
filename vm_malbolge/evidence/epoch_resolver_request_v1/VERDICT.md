# epoch_resolver_request_v1 — el payload de 10 trits lo elige la petición

En `epoch_resolver_word_v1` la máscara `29524` yanked en runtime permitió
escribir **cualquier** palabra de 10 trits, pero el *qué* se escribía lo fijaba
el programa: el payload era constante y sólo la celda de época dependía de
`stdin`. Aquí el payload también lo decide la petición, y una **única imagen**
de 293 bytes sirve para payloads distintos.

## Una restricción de la álgebra, medida

Para construir una palabra desde cero el acumulador debe mantener el invariante
`{1,2}` (entonces `ctrl=0` es no-op: `1→1`, `2→2`), y cada posición se pone a
`2` con un `ctrl=2` en esa posición. Es decir, hace falta un **dígito de control
por posición**, y ese dígito sólo puede valer 0 o 2.

¿Se puede derivar ese dígito del trit pedido? El mapa necesario sería
`0→0, 1→2, 2→0` (para `P`) o `0→0, 1→2, 2→2` (para `M`). El semigrupo de
composiciones de `crazy` sobre un trit tiene **exactamente 15 mapas**
(enumeración exhaustiva a partir de `g0=(1,0,0)`, `g1=(1,0,2)`, `g2=(2,2,1)`):

```
(0,0,0) (0,0,1) (0,0,2) (0,1,0) (0,1,1) (0,1,2) (1,0,0) (1,0,1)
(1,0,2) (1,1,0) (1,1,1) (1,1,2) (2,2,0) (2,2,1) (2,2,2)
```

Ni `(0,2,0)` ni `(0,2,2)` están: **el trit de la petición no puede producir el
dígito de control**. El mapa `(0,0,2)` sí está, y es precisamente el que
gobierna la fase final (poner `ctrl=2` donde el trit es 2).

Conclusión de interfaz: la petición lleva **dígitos de control**, no los 10
trits. Es un resultado negativo con prueba exhaustiva, no una suposición.

## La descomposición que sí funciona

Con `P` y `M` ambas en `{1,2}^10` (el invariante que `ctrl=0` conserva):

```
V = crazy(M, P)                      (ctrl = M, celda = P)
```

y por trit:

| trit de `V` | `P` | `M` | `TBL[P][M]` |
|---|---|---|---|
| 0 | 1 | 1 | 0 |
| 1 | 2 | 2 | 1 |
| 2 | 1 | 2 | 2 |

de donde

```
P = 29524 + Σ_{p: trit_p(V)=1} 3^p        (2 donde el trit es 1)
M = 29524 + Σ_{p: trit_p(V)≠0} 3^p        (2 donde el trit no es 0)
```

**Verificado exhaustivamente sobre las 59049 palabras: 0 discrepancias.**

## Protocolo de la petición (20 bytes)

```
bytes 0..9    : 2 si el trit p del payload es 1, si no 0     -> control de P
bytes 10..19  : 2 si el trit p del payload no es 0, si no 0 -> control de M
```

## Programa (293 bytes, todos imprimibles, sin bucles)

```
fase 0  bootstrap   a arranca en 0; crazy(0, 36) = 29524 en S
fase 1  fábrica     P, M, A, T pasan a 29524 (make-0 / make-29524)
fase 2  payload     20 bytes de control: se construyen P y M
                    cada byte se escribe con CRAZY en la ventana de posición 0;
                    el acumulador gira (ROT) una vez entre escrituras, así que la
                    ventana avanza de posición en posición; el ROT final restaura
                    el marco (10 rotaciones = identidad) y deja a = la palabra
fase 3  combinación  V = crazy(M, P)  -> P queda con V, a = V
fase 4  escritura    crazy(V, A) = swap(V) ; crazy(swap(V), T) = V EXACTO
fase 5  salto        JMP a T ; el payload decodifica OUT y emite V % 256 ;
                    T+1 contiene 74, que decodifica END
```

Celdas: `S=41`, `P=44` (salto en 45), `M=46` (salto en 47), `A=48`, `SH=61`,
`T=100`, `T+1=101`.

## Resultado medido

| instancia | payload | P construido | M construido | `T` escrito | `OUT` | pasos | estado |
|---|---|---|---|---|---|---|---|
| `payload_v93` | 93 | 29617 | 29617 | **93** | `0x5d` | 171 | HALTED |
| `payload_v187` | 187 | 29525 | 29618 | **187** | `0xbb` | 171 | HALTED |
| `payload_v281` | 281 | 29803 | 29804 | **281** | `0x19` | 171 | HALTED |
| `payload_v29797` | 29797 | 58775 | 59048 | **29797** | `0x65` | 171 | HALTED |

Los 20 bytes se leen **en orden** en las cuatro instancias; el `OUT` se emite en
`pc = T = 100`; el `END` está en `T+1`. `payload_v29797` reproduce exactamente
el `OUT = 0x65` del pack `epoch_resolver_word_v1`, con otra imagen.

Dos motores Python independientes (trazador con las primitivas del oráculo del
repo y trazador con las de `native_classic`) coinciden byte a byte con el
oráculo del repo.

## Controles negativos

| control | resultado | qué prueba |
|---|---|---|
| petición alterada (byte 0 invertido) | la época queda con `29798` en vez de `29797` | el payload **no** está fijo en el programa: lo decide la petición |
| los cuatro payloads | 4 `T` distintos y 4 `OUT` distintos | la misma imagen atiende payloads distintos |

## El runner C en esta imagen

Con `V = 93` (imprimible) el runner C recorre el programa entero y emite lo
mismo que el oráculo (`0x5d`, 171 pasos). Con los otros tres (payload no
imprimible) se detiene en la guarda de imprimibilidad, en el paso **170**, que
es exactamente el que predice el trazador del oráculo — coherente con
`c_printable_guard_v1`.

## Reproducción

```bash
python3 vm_malbolge/evidence/epoch_resolver_request_v1/build.py .
python3 vm_malbolge/evidence/epoch_resolver_request_v1/probe.py   # exit 0
```

## Pendiente

* la celda de época sigue siendo fija (`T = 100`): falta componer la selección
  de época de `epoch_algebra_v3` (la elige el byte de `stdin`) con este payload
  elegido por la petición;
* rearm de la época para una **segunda** petición en la misma ejecución
  (`epoch_rearm_primitive_v1`).

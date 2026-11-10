# epoch_resolver_word_v1 — payload de 10 trits, escrito exacto y ejecutado

Cierra el siguiente escalón de la línea de épocas: con la máscara `29524`
fabricada en runtime (en lugar de la imprimible `121` de `epoch_algebra_v3`), la
escritura exacta deja de valer sólo para 7776/59049 palabras y **vale para
cualquier palabra de 10 trits**, incluido un payload con trits 2 en posiciones
altas — justo lo que `121` no puede escribir.

## Programa (399 bytes, todos imprimibles, sin bucles)

```
fase 0  bootstrap   a arranca en 0; crazy(0, 36) = 29524 en S (36 = 1100_3)
fase 1  fábrica     W, PW, A, P, T pasan a 29524 (por parejas make-0/make-29524)
fase 2  petición    IN b ; crazy(b, PW) = swap(b) ; crazy(swap(b), W) = b EXACTO
fase 3  payload     P parte de 29524 y gana un trit 2 por posición con la máscara
                    rot^r(54) (una celda de rotación por máscara; r=0 -> r=10
                    porque la identidad no ejecuta instrucción ni carga `a`)
fase 4  escritura   crazy(V, A) = swap(V) ; crazy(swap(V), T) = V EXACTO
fase 5  salto       JMP a T ; el payload decodifica OUT y emite V % 256 ;
                    T+1 contiene 74, que decodifica END
```

Payload construido: `V = 29797`, trits 2 en las posiciones **1, 3 y 5**.
La posición 5 queda fuera del alcance de la máscara `121` (que tiene trits 0 en
5..9), así que este payload es un test discriminatorio del upgrade.

## Resultado medido

| comprobación | valor |
|---|---|
| puntero `W` | `99` exacto (el byte de petición) |
| celda de época `T` | **`29797` exacto** (escrituras `36→0`, `0→29524`, `29524→29797`) |
| `OUT` | `0x65` emitido **en `pc = 100 = T`** (el payload se ejecuta) |
| estado | `HALTED` en 277 pasos (END en `T+1`) |
| motores | trazador con las primitivas del oráculo del repo, trazador con las de `native_classic` y el oráculo del repo: **coinciden los tres** |

## Controles negativos

| mutante | `T` final | qué prueba |
|---|---|---|
| `mutant_mask_121` | `29311` ≠ `29797` | con la máscara imprimible la escritura del payload **falla**: el upgrade a `29524` era necesario |
| `mutant_wrong_payload` | `29554` | sin el trit 2 de la posición 5 el payload es otro y el opcode en `T` deja de ser `OUT` |

## Divergencia medida del runner C (documentada, no cerrada)

Las dos instancias legítimas corren correctamente en el oráculo del repo y en los
dos trazadores, pero el **runner C original** diverge en la fase final: aterriza
en `T` (su contador de pasos es 276, justo el del `OUT`) y sin embargo no emite
nada y para un paso antes. Síntomas acotados por experimentación:

* todas las fases anteriores coinciden (el puntero exacto, el payload, la
  escritura en la época: un `OUT` inserto justo después de la escritura emite
  `0x65` en el C);
* el `DLOAD` que deja `d` sobre el puntero también coincide (un `CRAZY` sobre
  `mem[d]` produce el mismo valor en los dos motores);
* un `JMP` con destino escrito en runtime **sí** funciona en el C (programa de
  control: ambos motores coinciden en 29429 pasos por una ruta salvaje).

Es decir: la divergencia está en la combinación «aterrizar en una celda de la
zona de dato con un valor de 10 trits» que sólo ocurre en la fase final. Queda
`NOT_DEMONSTRATED` para el runner C; los dos motores Python independientes
(trazador + oráculo) sostienen el resultado.

## Instancias del pack

`resolver_word` (salto con destino conocido en compilación), `resolver_word_dynamic`
(el mecanismo de `epoch_algebra_v3`: salto por el puntero escrito en runtime) y los
dos controles. Ambas legítimas verifican igual en los motores Python.

## Reproducción

```bash
python3 vm_malbolge/evidence/epoch_resolver_word_v1/build.py .
python3 vm_malbolge/evidence/epoch_resolver_word_v1/probe.py    # exit 0
```

## Pendiente

* payload **elegido por la petición** (hoy el payload es fijo y sólo la época la
  elige el byte de stdin);
* rearrm de la época para una segunda petición en la misma ejecución;
* la divergencia del runner C en la fase final.

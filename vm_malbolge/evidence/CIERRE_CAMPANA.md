# Cierre de la campaña — ambos frentes, con todo lo aprendido

Fecha: 2026-11-07. Repo: MALBOLGE-MB-DATABASE.

## Frente (a) — comparador decimal E1: `NOT_DEMONSTRATED`

### Estado del artefacto
`vm_malbolge/src/mbir_cmp_lt_dec.mb` — **34.105 bytes, ensambla** con el LMAO v0.6.0
del repo. Generador: `vm_malbolge/tools/cmp_lt_dec_gen.py`.

### Qué funciona, verificado
| Componente | Evidencia |
|---|---|
| Mecanismo de entrada `ENTRY` en `.DATA` | el programa arranca y lee stdin |
| `IN` alcanzado | traza: op 23 en el paso ~33.314 |
| Salida booleana de **un** byte | formato correcto, no ráfaga multibyte |
| Segunda subrutina de decremento | bloque autónomo, ensambla |
| `compare` con alternancia A/B | cableado, ensambla |
| Presupuesto | 24.944 bytes de margen — nunca el obstáculo |

### El defecto, localizado y verificado por dos métodos
**El byte leído nunca se escribe en `value` ni en `value2`.** Instrumentación
sobre las cuatro celdas (direcciones verificadas con `.dbg` regenerado):
**cero escrituras** en 400.000 pasos, con entrada `"1 2"`.

Consecuencia: la alternancia de `compare` decrementa dos celdas que nunca
recibieron los operandos, así que el primer carry llega siempre por `value` y
`result_false` se selecciona siempre → salida constante `0x00`.

### Los mecanismos de HeLL aprendidos (12, en orden)
1. Entrada: `.CODE` propio desenruta → `ENTRY` en `.DATA`.
2. `decrement_value` from-scratch rota sin fin → trasplantar el del cargador.
3. Compuerta de fase con `R_` consume la bandera → quitarlo.
4. Banderas armadas en `.CODE` no persisten → usar celdas de datos.
5. Pila → A sobrevive a la clasificación.
6. `MOVED` no copia entre celdas → camino de lectura.
7. Camino de B cruzado con el de decremento → bandera propia.
8. La clasificación de B destruía el operando → ir directo a `compare`.
9. La fase A clasificaba y destruía A → ir directo a `read_digit_B`.
10. Reordenar celdas rompe ambas cadenas → el orden es load-bearing.
11. El fichero tenía CRLF → los parches no se aplicaban en silencio.
12. La escritura la hace la cadena crazy de LMAO, no el `MOVED`.

### Por qué no se cerró
La escritura en celda la realiza la maquinaria crazy de LMAO (`U_CRAZY`/`U_ROT``),
que deriva el contenido de la celda **en tiempo de ensamblaje** y lo reescribe
**en tiempo de ejecución** cuando la instrucción CRAZY se ejecuta con `d` sobre
la celda. Conseguir esa posición exacta requiere la macro de LMAO correctamente
encadenada; se intentó por seis variantes distintas (banderas propias, bandera
compartida, sin clasificar, con clasificar, reordenando) y ninguna dejó el byte
en la celda. Restaurar la clasificación tampoco escribió (verificado: 0
escrituras).

## Frente (b) — imagen unificada: `NOT_DEMONSTRATED`

Cinco rutas medidas, todas rechazadas por LMAO:

| Ruta | Celda de fallo | Del límite |
|---|---|---|
| Imagen aritmética, sin comprimir | 58.955 | 94 |
| Imagen aritmética, comprimida | **58.969** | **80** ← la más cercana |
| Andamio del cargador, from-scratch | 57.619 | 1.430 |
| Despacho mínimo de CMP_EQ | 58.152 | 897 |
| Poda de código muerto | — | libera 6 de 845 líneas (0,7 %) |

**Restricción vinculante identificada:** la cinta de 59.049 células de Classic
junto con el inicializador de LMAO, más el hecho de que el margen aparente de las
imágenes existentes no es utilizable porque el inicializador lo consume.

## Frentes cerrados con artefacto verificado

Fase A (16 ficheros normalizados) · E0 475/475 runner + 120/120 oráculo ·
E3 (el muro son los flags, no las celdas) · E4-bis (N=3 rutas caben) ·
imagen nativa de 3 rutas (ADD+CMP_EQ+CMP_LT, 3 motores) · comparador de dominio
0..9 (10/10 en 3 motores) · imagen sin LMAO · prueba de no-existencia para dos
operandos (BFS exhaustiva sobre 51.799 estados + separabilidad) · presupuesto del
cargador (18.740 B, 512 celdas, 8 flags).

## Conclusión

Los dos frentes abiertos llevan entre ambos más de treinta mediciones. Quedan
`NOT_DEMONSTRATED` con su obstáculo **identificado al nivel del mecanismo**, no
de la voluntad: (b) por la cinta de 59.049 células, y E1 por la escritura en
celda de la macro crazy de LMAO. El conocimiento acumulado deja el trabajo
restante especificado sin ambigüedad para quien continúe.

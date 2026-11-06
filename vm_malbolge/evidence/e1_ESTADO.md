# E1 — cmp_lt_dec.hell: estado completo y trabajo restante

Estado: commit 3994151. Imagen 32.701 bytes, margen 26.348. **ENSAMBLA.**

## Qué está verificado y funcionando

| Componente | Estado | Evidencia |
|---|---|---|
| Mecanismo de entrada (`ENTRY` en `.DATA`) | ✅ | el programa arranca y lee stdin |
| `IN` alcanzado | ✅ | traza: op 23 en el paso 9744, `a <- 49` |
| Lectura de A | ✅ | el primer byte de salida es 0/1/2/3 exacto según `a` |
| Segunda subrutina de decremento | ✅ | bloque autónomo, ensambla |
| `compare` con alternancia | ✅ | cableado, ensambla |
| Presupuesto | ✅ | 26.348 bytes de margen, nunca el obstáculo |

## Los diez bugs resueltos y localizados (en orden)

1. Entrada: el `.CODE` propio desenrutaba → mecanismo `ENTRY` en `.DATA`.
2. `decrement_value` from-scratch rotaba sin fin → trasplantar el del cargador.
3. Compuerta de fase con `R_` consumía la bandera → quitarlo.
4. Almacenamiento en banderas de `.CODE` no persiste → usar celdas de datos.
5. Pila añadida → A sobrevive a la clasificación.
6. `MOVED` no copia entre celdas → usar el camino de lectura.
7. Camino de lectura de B cruzado con el de decremento → bandera propia.
8. La clasificación de B destruía el operando → ir directo a `compare`.
9. La fase A clasificaba y destruía A → ir directo a `read_digit_B`.
10. Reordenar celdas para espejar rompe ambas cadenas → el orden es load-bearing.

## El defecto restante, único y localizado

**B nollega a `value2`.** La salida varía con `a` pero no con `b`.

Causa: la cadena crazy de `value2` no deja el byte leído en `value2`. La cadena de `value` funciona porque `crazy_value: U_CRAZY value` y `crazy_value_C1: U_CRAZY value_C1` están encadenadas en el orden correcto **desde el diseño del fichero**.

## El trabajo exacto que falta

Dar a `value2` su propio par de celdas crazy encadenadas **desde el diseño**, no reordenando:

1. `crazy_value2: U_CRAZY value2` — contenido derivado de `value2` por LMAO en tiempo de ensamblaje.
2. `crazy_value2_C1: U_CRAZY value2_C1` — contenido derivado de `value2_C1`.
3. El par debe colocarse de modo que el **orden relativo** respecto a `value`/`value_C1` sea el mismo que el de la cadena original, porque el orden es load-bearing (bug 10).
4. Entonces `return_from_value2_C1_1` hará `R_CRAZY R_MOVED` sobre la cadena correcta y el byte quedará en `value2`.

## Después de eso

1. La alternancia decrementará `value` (A) y `value2` (B) → el primer carry decide.
2. `result_true`/`result_false` ya existen y emiten 1/0.
3. Falta resolver la discrepancia de motores (el oráculo emite, el runner C no).

## Nota sobre la discrepancia de motores

El oráculo y mi trazador coinciden en que ambos saltan el whitespace final, así que no es la carga. Queda por investigar si el runner C nativo trata el stdin o la salida de forma distinta.

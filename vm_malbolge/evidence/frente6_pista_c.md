# Frente 6a — pista C: primer milestone

## Resultado: NO DEMOSTRADO, con el obstáculo localizado

Script: `vm_malbolge/tools/c_frontend_gen.py`. Escribe un emisor C
(`c_emitter.c`), lo compila con gcc, ejecuta para producir un `.mal` Classic y
verifica en los dos motores.

## Lo que se depuró

1. **Fórmula posicional invertida.** Mi primer emisor calculaba
   `char = (indice_xlat1 - dir) % 94 + 33` sobre el índice crudo del carácter,
   cuando la forma canónica del repo (`constants.py:char_for_op`) es
   `chr((XLAT1.index(op_char) - addr) % 94 + 33)`. Corregido.
2. **Secuencia de instrucciones.** El programa pasó de `/j<v` (4 celdas) a
   `/j*j<v` (6: IN, JMP, ROT-carga-dato, OUT, HALT).
3. **Comentario C roto** por un `*/` interno (`'*'/*/p`) que cerraba el bloque
   antes de tiempo. Reparado.

## El obstáculo, localizado

El emisor produce imágenes de 4-6 bytes y **ambos motores paran en <10 pasos**
(oráculo emite `eb`, runner no emite nada). La causa no es un parámetro: es que
un emisor Classic mínimo necesita tres cosas que mi versión no hace:

1. **Memoria de relleno.** Classic rellena hasta 59.049 celdas con
   `mem[i] = crz(mem[i-1], mem[i-2])`. Una imagen de 6 bytes deja el resto al
   relleno, y las primeras celdas que el flujo toca después del programa
   explícito son basura.
2. **Puntero de datos apuntado.** El `j` (op 40) hace `d = mem[d]`, así que `d`
   solo llega a la celda de dato si alguna celda intermedia contiene su
   dirección. Mi emisor no construye esa cadena.
3. **Carga del acumulador.** `*` hace `a = mem[d]`, pero solo si `d` ya apunta
   al dato. Sin (2), `a` recoge basura.

## Veredicto del frente 6

Sin bloqueante de presupuesto ni de toolchain (gcc funciona, runner y oráculo
funcionan). El obstáculo es de **diseño del emisor**, y está localizado en los
tres puntos de arriba.

## Camino concreto

No escribir el emisor desde cero: `BolgeForge/experiments/square_0_9_native_
dispatcher/build_native_square.py` ya resuelve los tres puntos (layout posicional
con `char_for_op`, cadenas de puntero, y relleno validado celda a celda con
`valid_cell`). El siguiente paso es portar ESE emisor a C, no inventar uno
mínimo. El coste estimado es la traducción de ~250 líneas de Python a C.

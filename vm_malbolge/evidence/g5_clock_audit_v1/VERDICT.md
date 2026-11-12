# G5: reloj y tres instrucciones compartidas por fase

2026-11-12. Base `0e6fb49`; puertas `f01495e`, `77e9776`, `22a9ad0`, `4073bae`. Las pruebas son nuevas y conservan los packs previos. REA se ejecutó desde el código fuente local `32aade1ace`; el servicio conectado anteriormente no fue reiniciado.

## Resultado

Se confirmó con una imagen estricta el reloj corregido de G5. Además, se construyeron tres imágenes parciales que reutilizan una misma celda para `CRAZY`, `ROT` o `MOVD`, alternando cada operación con un NOP efectivo. Cada imagen usa un recorrido **finito y preinstalado** de punteros D. No se construyó la imagen G5 con R y R2 ni un bucle de incremento de longitud arbitraria.

| Afirmación | Estado | Evidencia |
| --- | --- | --- |
| Reloj `66→62→76→79` | PASS para la imagen construida | `verification.results.json`: visitas con opcodes `68,64,78,81`, tres salidas `a6` y halt nativo. |
| Control del reloj | PASS en alcance medido | Segunda rama alterada produce una sola salida `a6`; Olmstead termina. |
| CRAZY compartida | PASS, tres operaciones | `shared_verification.results.json`: misma PC 58456, secuencia `62,58` repetida tres veces; tres celdas de datos distintas cambiadas. |
| ROT compartida | PASS, tres operaciones | `rot_verification.results.json`: misma PC 58433, secuencia `39,35` repetida tres veces; tres datos distintos rotados. |
| MOVD compartida | PASS, tres operaciones | `movd_verification.results.json`: misma PC 58434, secuencia `40,36` repetida tres veces y destinos D 57100, 57200, 57300. |
| Controles de fase | PASS para lo observado | La fase inicial se invierte; CRAZY y ROT actúan sobre otros datos, y MOVD comienza con NOP en vez de MOVD. Ambas imágenes terminan sin salida, por lo que la salida nativa sola no distingue esos controles. |
| G5 R→B→R2 | NOT_DEMONSTRATED | Las primitivas y el reloj son imágenes separadas; no se sintetizó un restaurador compartido completo. |
| Incremento arbitrario y EOF | NOT_DEMONSTRATED | No se integraron cálculo, rearme de código y detector EOF. |

## Reloj

El valor 66 en PC 58470 (`pc % 94 = 2`) sigue los valores `66,62,76,79`, que decodifican `68,64,78,81`; los tres primeros son NOP efectivos y el último HALT. Scratch y la ventana REA coinciden evento por evento hasta HALT, y Olmstead emite `a6 a6 a6` con rc=0. El control altera el segundo destino y emite `a6` con rc=0.

Las tres salidas son **tres posiciones OUT distintas**. El reloj no modifica A ni usa D para contar; el recorrido que vuelve al reloj sí utiliza una secuencia finita de punteros D. Esto no demuestra un cuerpo OUT reutilizable ni un reloj integrado con R/R2.

## Primitivas de dos fases

La órbita `74↔70` permite escoger posiciones de código donde la primera palabra decodifica la operación deseada y la segunda un NOP efectivo:

| PC mod 94 | Fases medidas | Primitiva |
| --- | --- | --- |
| 82 | `62,58` | CRAZY, NOP |
| 59 | `39,35` | ROT, NOP |
| 60 | `40,36` | MOVD, NOP |

Cada posición ejecutó su operación tres veces en la misma corrida sin que otra rutina restaurara esa celda de código. Cada paso NOP hace avanzar D y se retorna mediante JMP y datos preinstalados. La prueba de MOVD confirma los destinos después del incremento de D. Las ventanas tardías de REA coinciden evento por evento con el modelo scratch hasta HALT; `events_truncated=true` porque no incluyen el arranque. Olmstead terminó cada imagen y su control con rc=0, sin salida. No se infiere de esa salida vacía que el control sea igual al positivo: las trazas muestran diferencias de fase y destinos.

## Tamaño del diseño G5 literal

`architecture_check.py` comprueba una lectura concreta de `G5_DESIGN.md`: islas de 19 celdas de código **separadas y no compartidas**, una por cada celda objetivo; R restaura todas las celdas de R2 y B, y R2 todas las de R. Si `r`, `s` y `b` son sus cantidades de celdas y `b≥1`, las condiciones son `r≥19(s+b)` y `s≥19r`. Combinadas exigen `r≥361r+19b`, imposible para cantidades no negativas. Z3 devuelve `unsat` para esas hipótesis.

Esto **no demuestra que G5 sea imposible en general**: la cota deja de aplicar si se comparten primitivas, se toleran fases NOP o se restaura por bloques. Las primitivas medidas aquí muestran una dirección para compartir operaciones, pero aún falta una tabla o despachador que las coordine, restaure sus controles y mantenga los registros correctos. Tampoco se ha sintetizado R/R2 conforme a otra arquitectura.

## Reproducibilidad y límites

Las imágenes y planes del reloj y de las tres primitivas se reprodujeron en árboles aislados (`reproduction.results.json`, `shared_reproduction.results.json`, `rot_movd_reproduction.results.json`). El manifiesto conserva hashes, salidas y controles. Las capturas originales REA se guardan en estado local privado y se incluyen copias saneadas; su ventana tardía no incluye el bootstrap.

Pendiente: componer las primitivas en una rutina de rearme compartida y repetible, integrar R/R2 y B, verificar G5/G6 con el reloj, y después incorporar EOF y el incremento a longitud arbitraria. Ninguna de estas afirmaciones está demostrada aquí.

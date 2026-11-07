# Selector + almacén exacto rearmable en una imagen Classic

## Hipótesis

H1: una imagen Malbolge Classic, sin intervención del host durante la ejecución, recibe secuencias de solicitudes 01 y 02, selecciona respectivamente valores 0x50 y 0x52 en rutas diferentes, almacena el valor seleccionado exactamente en una celda, lo recupera desde esa celda y vuelve al mismo IN para atender la siguiente solicitud. H0: al menos una propiedad falla en los casos ensayados.

**CONDITIONAL_PASS**, dominio acotado {01,02}: las nueve secuencias de `stdout.raw.txt`, incluyendo `01 02 01 → 50 52 50`, `02 01 02 → 52 50 52`, repeticiones y 128 solicitudes pseudoaleatorias, producen resultados exactos en el oráculo Python y el runner C, con el mismo número de pasos. Python etiqueta EOF y C etiqueta HALTED la terminación en agotamiento de entrada.

Este experimento conecta en una imagen el selector de `epoch_selector_reusable_v1` con una rutina de dos CRAZY que copia el resultado al almacén y dos CRAZY con C2 para leerlo. El inicializador rearma scratch y slot al comienzo de cada vuelta. La poda del clasificador elimina rutas mayores a 02 y envía lo no soportado a HALT: no extiende el dominio.

## Trazado de memoria para A→B→A

Traza instrumentada Python, guardada íntegra en `results.json`. En cada vuelta se observa un salto a `compose_entry`, diez visitas a la rama seleccionada (el bucle que rota el marcador diez veces), y al reingresar el mismo PC `IN` con scratch y slot en C1=29524.

| Evento | paso | escritura/estado de `compose_slot` |
|---|---:|---|
| entrada A | 37090 | 29524 |
| salida A | 41056 | 29524 → **80** → 40 → **80** |
| entrada B | 41201 | 29524 |
| salida B | 46018 | 29524 → **82** → 164 → **82** |
| entrada A | 46163 | 29524 |
| salida A | 50128 | 29524 → **80** → 40 → **80** |
| siguiente IN / EOF | 50273 | 29524 |

La primera escritura en cada fila guarda el valor seleccionado; las dos siguientes corresponden a la recuperación. En OUT el slot contiene el mismo valor emitido. `compose_entry` se visita una vez por solicitud; la ejecución vuelve al selector, no se prueba una ABI de retorno a llamadores arbitrarios. El trazador Python replica la semántica del oráculo; el runner C verifica externamente bytes y pasos, no expone sus escrituras internas.

## Controles

- `mutant_read` cambia de C2 a C1 en la primera operación de lectura. Para 010201 produce `28 00 28`, no `50 52 50`, y ambos motores coinciden en bytes y pasos. Confirma que la recuperación no se puede sustituir por esa transición.
- `mutant_rearm` omite el ciclo completo de rotación del marcador 01. La solicitud 02 sigue produciendo `52` en ambos motores, mientras 01 y 010201 fallan en ambos. El oráculo y el runner discrepan en pasos o salida tras entrar en código no imprimible; no se afirma paridad para ese mutante.
- La primera unión sin poda (`combined.hell`) no ensambló: LMAO informó `Free space exceeded` / celda 59012. Se preserva la fuente y `rebuild.raw.txt`; la versión binaria explícitamente acotada sí ensambla. Ese fallo se refiere a esta construcción/LMAO, no demuestra imposibilidad de otra organización.
- Para entradas aisladas fuera de dominio 00, 03 y ff se observó terminación sin salida en ambos motores; son observaciones, no una especificación exhaustiva del protocolo.
- Validación estática del loader estricto: 0 celdas inválidas tras excluir whitespace. No se ha ejecutado un loader estricto independiente.

## Alcance y reproducción

Esto demuestra una **composición in-VM acotada** de selector, escritura exacta, recuperación, rearme y retorno al bucle, no el resolvedor PureEpoch general. No se ha importado o integrado código PureEpoch como middleware, no se ha demostrado búsqueda/síntesis de transiciones en runtime, escritura a direcciones arbitrarias ni un protocolo más amplio. Las dos ramas/valores están predefinidos. Tampoco se afirma restauración íntegra de memoria o independencia respecto de LMAO.

`python3 vm_malbolge/evidence/epoch_selector_store_v1/probe.py` reproduce la prueba sobre las imágenes y **sobrescribe** `results.json`; copiar el pack antes de repetir para preservar la evidencia original. `build.py <directorio-nuevo>` reconstruye el ensamblado completo, su poda y los dos mutantes. Se comprobó que las tres fuentes reconstruidas son idénticas a las conservadas, y que el binario reconstruido produce `50 52 50` para 010201 (`rebuild.raw.txt`). La reconstrucción registra el error del ensamblado sin poda; LMAO no se considera byte-determinista.

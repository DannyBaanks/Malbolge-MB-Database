# Época reutilizable: escritura exacta y retorno — v1

## Hipótesis y alcance

H1: una sola imagen Classic recibe varias solicitudes consecutivas, rearma una pareja de celdas, almacena cada byte exactamente, lo lee y vuelve a recibir otra solicitud. H0: una de estas propiedades falla en los flujos medidos. Este es un experimento sobre el código HeLL **existente** `vm_malbolge/src/cell_stack_loop_echo.hell`, no una implementación de PureEpoch ni prueba de un buscador general.

**CONDITIONAL_PASS:** siete flujos, incluidos 0..255 y 255..0 completos en ejecuciones separadas; salida y pasos coinciden entre el oráculo y el runner C. El oráculo reporta EOF mientras el runner denomina HALTED al mismo fin de entrada. El trazador instrumentado confirma por solicitud el rearme de `stack_scratch` y `stack_top` a C1=29524, la escritura del byte de 10 trits en `stack_top` y su presencia en esa celda al ejecutar OUT. Las PC de IN y OUT se repiten: la siguiente solicitud se procesa dentro de la misma ejecución.

## Control negativo y corrección del harness

El mutante inserta `ROT C1 R_ROT` antes de almacenar en `stack_scratch`: reemplaza el dato que se pretende escribir por C1. En los siete flujos, ambos motores emiten 0x54 por cada byte, su byte bajo, y la traza confirma que `stack_top` contiene el **valor completo 29524**, no 84. Este control separa el dato recibido del dato almacenado; no demuestra que el sistema detecte el fallo por sí mismo. Cuando la entrada es 0x54 el byte observado coincide casualmente con el mutante.

Se preserva `first_attempt.raw.txt` y `first_attempt.json`: el primer harness falló al comparar el valor completo 29524 de la celda mutante con su byte bajo 84. La versión corregida compara palabras completas y mantiene los resultados negativos originales.

## Loader y límites

Tras excluir espacios en blanco del archivo antes de numerar las celdas, todas las celdas fuente de ambas imágenes son imprimibles y decodifican a un opcode válido bajo XLAT1 (0 inválidas). Es una validación estática del loader estricto, no una ejecución independiente de otro loader estricto.

No demuestra el resolvedor propuesto completo: **NOT_DEMONSTRATED** búsqueda/síntesis de transiciones decidida en runtime, escritura a direcciones dinámicas o arbitrarias, servicio/middleware de PureEpoch, anidamiento/reintentos/rollback, ni retorno a un llamador general distinto del bucle construido. El programa sirve como control positivo y andamio para investigarlos. El estado de las celdas se observa con un trazador Python que replica la semántica, no con introspección independiente del runner C.

## Reproducir

Desde la raíz: `python3 vm_malbolge/evidence/epoch_reusable_store_v1/probe.py`. Sobrescribe `results.json`: copiar el pack antes de repetir si se requiere preservar esta evidencia. Positivo compilado con `third_party/lmao/lmao -d -o positive.mb vm_malbolge/src/cell_stack_loop_echo.hell`; mutante desde `mutant.hell` con el mismo comando. Compilación LMAO no se reivindica byte-determinista; hashes identifican estas instancias.

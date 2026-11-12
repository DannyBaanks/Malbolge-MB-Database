# Bucle Malbolge de dos fases: código reutilizado

2026-11-12. Base `2f022b1`; gates en `GATES.md`. Esto es un nuevo bloque de control nativo y reutilizable para avanzar hacia el incremento; por ahora su cuerpo hace eco, no calcula `+1` y no detecta EOF.

## Construcción

El bloque lineal empieza en 58058. Su primera celda, MOVD, toma un puntero fijo y pone D en 57000. Las celdas 58135 y 58211 son IN y OUT. Las tres usan la órbita XLAT2 `74 ↔ 70`: producen su instrucción en la primera pasada y una operación sin efecto en la segunda. El JMP de 58212 vuelve al inicio y no se cifra a sí mismo. El valor de D en cada JMP selecciona la misma entrada para la pasada siguiente; tras la pasada de rearme, el siguiente MOVD reinicia D.

El relleno no usa una sola celda NOP repetida: en cada dirección el sintetizador elige una órbita cuya **totalidad** decodifica como operación sin efecto en esa posición. Algunas órbitas son de más de dos pasos; por eso no se afirma que todo el bloque tenga el mismo estado después de dos pasadas, sino que las tres celdas útiles retornan a su fase y el relleno sigue inofensivo. No hacen falta islas de restauración por cada instrucción en esta construcción limitada.

## Evidencia

- Imagen estricta autoinstalable. El modelo observa las mismas direcciones MOVD, IN y OUT alternando operación/sin efecto al menos cuatro veces. `run01/verification.stdout.raw.txt` contiene los valores y posiciones.
- REA hizo replay hasta 7900 pasos: positivo `ABCD`, control `dbABC`, ambos `MAX_STEPS`; sólo se conservan los primeros 64 eventos y no incluyen el bucle. La comparación de visitas y fases proviene del modelo, no de esa ventana REA.
- Olmstead nativo, con stdout sin búfer, emitió la entrada completa de 10 000 bytes en orden. El proceso emitió después `a8` al recibir EOF y fue terminado por el arnés; no fue HALT. `run01/long.stdout.raw.txt` conserva los hashes de entrada y salida.
- El control parte con la celda IN en la fase opuesta; el primer byte de salida difiere y los IN ocurren en la pasada incorrecta. La salida y eventos de ambos casos están registrados.
- Síntesis repetida en una carpeta aislada: las dos imágenes, objetivos, planes e informe son idénticos byte a byte. Paridad de memoria CRAZY: common y scratch 0 discrepancias, operandos invertidos 18709.

## Límites y siguiente integración

El objetivo completo sigue abierto: reemplazar eco por el cálculo `(byte+1) mod 256`, mantener tabla y scratch al reingresar, integrar detección autónoma de EOF y generar el resultado desde BF sin depender de una imagen prefabricada. El control de fase y el eco largo no demuestran esas propiedades. Una ruta de integración consiste en programar el cuerpo de tabla ya estudiado con instrucciones de órbita de fase y asegurar que las dos pasadas conduzcan de vuelta a un estado D conocido; la detección EOF debe ocurrir antes de emitir.

Reproducción desde la raíz del repositorio; el directorio elegido debe estar vacío o no existir:

```sh
PHASE_OUTPUT_DIR=/tmp/phase-loop-NUEVO python3 vm_malbolge/evidence/g5_phase_loop_20261112/synthesize.py
python3 vm_malbolge/evidence/g5_phase_loop_20261112/verify.py /tmp/phase-loop-NUEVO
python3 vm_malbolge/evidence/g5_phase_loop_20261112/verify_long.py /tmp/phase-loop-NUEVO
```

Las pruebas requieren los repositorios hermanos BolgeForge y Malbolge-PureEpoch y `stdbuf`; las huellas están en el manifiesto.

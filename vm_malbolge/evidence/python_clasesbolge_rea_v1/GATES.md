# Python → Clasesbolge → REA: prueba previa

Base `2f0d829`, 2026-11-11. Probar el método pedido: definir primero el comportamiento en Python, construir Malbolge a partir de `s=33+((op-c-33)%94)` y comparar observaciones en REA y Olmstead. El primer contrato, deliberadamente acotado, copia hasta cuatro bytes, en orden, y termina. Se usa un programa Malbolge lineal de cuatro pares IN/OUT y HALT: no demuestra el bucle UNIECO.

G0: definir referencia Python y generador; cada byte Malbolge es imprimible, decodifica al opcode previsto y pasa el cargador de Olmstead. La fuente de la ecuación se identifica por hash.
G1: con al menos cuatro bytes, la salida es exactamente el prefijo de cuatro; probar 256 secuencias deterministas que cubren cada valor 0..255, más entrada de cinco bytes para mostrar el límite; comparar Python y Olmstead por bytes y retorno. Capturar entrada/salida cruda y detalles reproducibles.
G2: usar REA para observar Python y para trazar el Malbolge con el mismo vector visible; comparar los cuatro bytes y terminación, registrando diferencias de autoridad y semántica. REA Malbolge es un motor de replay, no medición eléctrica ni garantía de equivalencia universal.
G3: probar EOF antes de los cuatro bytes y publicar si Python y Malbolge coinciden. Un resultado distinto es negativo y no se enmienda el contrato; no usar entrada de tamaño insuficiente para afirmar paridad.
G4: control que sustituye un OUT por NOP y falla el contrato; registrar el resultado del cargador y salida de control.

Conservar negativos, comandos, salida cruda, código y hashes; no cambiar los packs anteriores. No se afirma que compartir entrada/salida implique iguales instrucciones nativas, misma complejidad, mismo estado interno o equivalencia para toda entrada. El bucle de tabla constante y la detección interna de EOF siguen fuera de esta primera prueba.

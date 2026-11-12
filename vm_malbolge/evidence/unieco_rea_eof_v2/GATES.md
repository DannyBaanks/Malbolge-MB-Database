# Python → BF → Malbolge: EOF binario, prueba preregistrada

Fecha: 2026-11-11. Base: `84e83e0`. No modificar packs anteriores.

Contrato: reflejar cada byte de la entrada, incluidos NUL y FF, y terminar al EOF sin bytes extra. Python es referencia; Brainfuck usa celdas de 16 bits con wrap y `,` que escribe 65535 en EOF. La imagen Malbolge debe ejecutarse con el cargador estricto de Olmstead. Sus construcciones y el origen de cada una se registran por separado: igualdad de comportamiento no prueba compilación entre lenguajes.

- G0: programa BF genuino con bucle y semántica de EOF documentada, caso vacío y NUL incluidos.
- G1: comparación Python/BF/Malbolge, proceso Malbolge termina rc=0 y bytes coinciden; entradas vacío, 00, mixto, 0..255 y 10000 bytes.
- G2: controles negativos verifican que se detectan salida alterada y EOF incorrecto.
- G3: REA observa el Malbolge; registrar límites de pasos, cobertura y comportamiento de EOF del motor REA. REA es replay, no medición de silicio.
- G4: candidata relocalizada original con detección EOF propia, sin que el host fuerce la parada. Sólo PASS si se construye y ejecuta de verdad, con controles.

Registrar salida cruda, hash, comandos y límites. No extrapolar equivalencia de todas las entradas ni declarar BF→Malbolge compilado sin un compilador y prueba de procedencia. No usar el promedio del pack anterior como techo matemático.

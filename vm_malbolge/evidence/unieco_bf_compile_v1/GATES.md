# Especialización BF → Malbolge para eco binario

Fecha 2026-11-11. Base `737f890`; preregistro anterior a la ejecución.

Alcance: compilador por plantilla para la única secuencia BF `,+[-.,+]`, con celdas de 16 bits modulares y EOF=65535. Este patrón realiza eco binario completo; cualquier otro programa o convención debe rechazarse. La salida es la imagen Malbolge estricta de referencia existente, autenticada por SHA-256: no es un compilador general ni una traducción estructural de operaciones ni la candidata relocalizada.

G0: entrada BF reconocida y plantilla auténtica; rechazar BF distinto, convención distinta y plantilla alterada. G1: ejecutar la salida compilada con Olmstead y comparar con Python y BF para vacío, NUL, mixto, todos los bytes y 10000 bytes, sin salida extra y con halt. G2: demostrar que los controles negativos rechazan sin crear salida. G3: observación REA bajo EOF histórico; identificar versión y semántica. G4: EOF autónomo en el bucle relocalizado previo, sólo si se construye y prueba realmente. Preservar evidencia y no reescribir packs anteriores.

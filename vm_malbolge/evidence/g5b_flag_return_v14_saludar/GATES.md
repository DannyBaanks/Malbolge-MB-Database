# P14 — preregistro: def saludar / print Hola / saludar()

2026-11-24 México. Base P13 e0d4934. Construir una imagen Classic autónoma con llamador separado, cuerpo saludar, dirección de retorno numérica guardada en runtime y retorno indirecto al llamador que termina.

- Salida exactamente Hola seguido de LF, equivalente al programa Python de referencia.
- Traza CALL desde llamador → entrada saludar → cinco OUT de su cuerpo → RET mem[slot] → continuación llamador → HALT.
- Imagen alternativa cambia solo la continuación del llamador (30000/32000), conservando idéntico código de saludar.
- Control de retorno roto imprime Hola pero no vuelve a la continuación correcta; control que omite CALL no imprime Hola.
- Cuatro motores, salida de Python de referencia, dos generaciones e integridad SHA-256.

Traducción manual de este ejemplo concreto; no compilador Python general. Una invocación por ejecución, sin prueba de cuerpo reutilizable múltiples veces ni pila general.

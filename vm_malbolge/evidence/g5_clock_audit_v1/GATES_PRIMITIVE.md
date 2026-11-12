# Enmienda preregistrada: primitiva CRAZY compartida por fase

2026-11-12. Tras la auditoría del diseño sin compartir, probar una alternativa parcial: una celda de código en pc≡82 con valor 74 alterna por xlat2 entre 74 y 70, que decodifican CRAZY y NOP efectivo. La misma celda se visita seis veces (CRAZY/NOP tres veces), y las tres operaciones CRAZY deben modificar tres celdas de datos diferentes. El retorno puede usar punteros D preinstalados y terminar tras seis visitas; no se afirma un despachador ilimitado.

Exigir cargador estricto, Olmstead nativo, trazas scratch y REA, comparación de visitas y escrituras, y control con fase inicial intercambiada. La primitiva no constituye el restaurador compartido completo, no rearma otras instrucciones y no cierra G5 ni el bucle de incremento.

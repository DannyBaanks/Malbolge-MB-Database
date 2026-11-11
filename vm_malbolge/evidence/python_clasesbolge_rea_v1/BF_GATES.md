# Ampliación: Python → Brainfuck → Malbolge → REA

2026-11-11. Solicitado después de `c6b6dc8`. El código Python original y la imagen Malbolge generada ya existían antes de estas puertas; esta es una investigación exploratoria con pre-registro únicamente de las comparaciones BF que siguen, no de la construcción previa ni de las capturas REA ya efectuadas.

BF de referencia: `,.,.,.,.` (cuatro lecturas y cuatro escrituras, sin bucles). El intérprete BF real del ensamblaje interpreta `,` en EOF como cero y codifica `stdin_data` en UTF-8; se coteja directamente para entradas ASCII, vacío y NUL. Para bytes 0..255, una implementación binaria acotada del fragmento `,.` debe usar la misma regla EOF=0 y rechazar otros programas; no se presenta como intérprete BF general.

Comparar Python, BF acotado e intérprete BF de ensamblaje donde su interfaz lo permita, y el Malbolge estricto derivado con la fórmula. Usar al menos 256 vectores de cuatro bytes que cubran todos los valores, y 0..3 bytes para revelar diferencias EOF. La equivalencia para >=4 bytes debe compararse observacionalmente; EOF=0 BF, Python termina y Olmstead usa 59048, así que la equivalencia en EOF queda sujeta a lo medido, no asumida.

Probar que el compilador Boss 2 existente rechaza `,` y `[`/`]`; no atribuirle la traducción especializada de `,.`. La traducción propuesta acepta exclusivamente repeticiones completas de `,.`, rechaza cualquier otro comando y emite pares IN/OUT y HALT mediante la fórmula de Clasesbolge; no hay mapeo general 1:1 ni se afirma un compilador BF completo. Controles negativos: OUT sustituido, programa BF con entrada insuficiente y sintaxis fuera del subconjunto.

Capturar con REA la referencia Python, un wrapper BF acotado y el replay Malbolge con el mismo vector, verificando bytes/terminación y preservando sus distintas autoridades. Preservar errores de herramientas, en particular cualquier error del replay REA en EOF. No afirmar que la traducción limitada soluciona UNIECO o EOF del eco completo.

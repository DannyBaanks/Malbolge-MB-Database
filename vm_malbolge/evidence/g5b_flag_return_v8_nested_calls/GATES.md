# P8 — preregistro: llamadas anidadas, profundidad fija 2

2026-11-24. Base P7 0fb866c. GAP: las llamadas secuenciales no prueban conservación de un retorno exterior durante otra llamada.

Contrato acotado: A/B llaman a una rutina exterior O compartida; O llama a I (crazy sobre una variable) y recibe el retorno en O_AFTER; después O selecciona A/B usando una bandera exterior preservada. I usa una bandera interior distinta, rearmada antes de O_AFTER. La misma imagen repite A/B durante tres vueltas y termina por reloj.

- G0: cargador Classic estricto, un único O_ENTRY, I_ENTRY y O_AFTER; una operación crazy de trabajo.
- G1: seis secuencias O_ENTRY → I_ENTRY → O_AFTER → continuación A/B, alternadas A B A B A B. Profundidad observada 0→1→2→1→0, no dos llamadas secuenciales.
- G2: el valor de la bandera exterior en O_ENTRY se conserva en I_ENTRY y O_AFTER; las dos identidades exteriores (70/74) tienen continuaciones distintas. No se reinicializa la bandera exterior entre esos puntos. Bandera interior vuelve a 74 antes de O_AFTER; sitio crazy y ambas banderas restaurados en cada vuelta.
- G3: estado V persistente, recurrencia crazy exacta, solo I escribe V; colas JMP estables.
- G4: control que cifra deliberadamente la bandera exterior dentro del retorno interior debe romper el orden nominal de retornos. Control que omite el armado de A en el llamador también debe fallar el contrato nominal.
- G5: Olmstead, clasesbolge, trazador local y eventos REA coinciden; dos generaciones independientes idénticas byte a byte. Conservar negativos y medir todos los retornos.

No es una pila general: dos niveles tienen banderas distintas asignadas estáticamente; el llamador de I es único, con continuación fija. No cubre recursión, selección por entrada ni profundidad arbitraria. Parar al demostrar o falsar este contrato.

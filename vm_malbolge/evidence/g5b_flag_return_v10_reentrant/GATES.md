# P10 — preregistro: reentrada de R en dos niveles

2026-11-24. Base P9 c08fd4d. Contrato: A/B llaman R; antes de que esa activación retorne, R vuelve a entrar por el mismo R_ENTRY y ejecuta el mismo cuerpo crazy en un segundo contexto. El retorno del segundo nivel reanuda el primero; después se recupera A/B.

- G0: un solo ENTRY, MIX y DISPATCH compartidos por los dos niveles. Imágenes Classic estrictas. Contextos de profundidad fija V=41000 y W=43000.
- G1: seis grupos ENTRY(V) MIX(V) ENTRY(W) MIX(W) RESUME RETURN_A/B, sin retorno exterior entre ambas entradas; A B repetido tres vueltas.
- G2: ENTRY y MIX ejecutan las mismas celdas y sus palabras se rearman a 74 en cada visita. DISPATCH es compartido también al volver del segundo nivel y al retornar al llamador exterior.
- G3: FO de A/B se conserva durante el segundo nivel. El contexto exterior V no se modifica por la activación interior W; ambas variables conservan su estado entre vueltas. Solo MIX escribe esas variables, con recurrencia crazy exacta. Colas JMP intactas y FO/MIX/ENTRY restaurados al reloj.
- G4: control outer_clobber cifra FO durante el retorno interior y debe perder A/B. Control bypass_inner omite la segunda entrada; mantiene A/B pero falla reentrada y no modifica W.
- G5: cuatro motores coinciden; REA confirma entradas al mismo pc, contextos distintos y retornos en orden. Dos generaciones reproducibles y hashes.

Dos contextos y destinos estáticos, profundidad acotada, sin pila dinámica ni recursión arbitraria. No confundir una rutina reentrante con dos copias de código ni con dos invocaciones ya terminadas. Cierre al demostrar o falsar el contrato.

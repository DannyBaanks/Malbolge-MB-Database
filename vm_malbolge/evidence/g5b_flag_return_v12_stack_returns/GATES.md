# P12 — preregistro: pila de tokens conectada con R

2026-11-24. Base P11 a8cd9be. Capacidad 2; catálogo de continuaciones (profundidad,token): (1,A)→A, (1,B)→B, (2,A)→RESUME, (2,B)→error E.

- G0: R_ENTRY y MIX únicos, sin FO exterior separado; el contexto V/W se selecciona por ocupación real de la pila tras push. Misma imagen llama desde A y luego B.
- G1: push retorno exterior → R(depth1) → push A interior → misma R(depth2) → pop A/RESUME → pop retorno exterior → A/B; salida AB. El pop debe ejecutar el salto seleccionado, no solo imprimir el token.
- G2: profundidad 0→1→2→1→0 dos veces, estado V/W persistente y escrituras aisladas en MIX. Al finalizar, pila vacía; colas JMP estables.
- G3: cifrar S0 después del primer push A debe cambiar el destino a B. Leer slot inferior en pop a profundidad 2 debe romper el retorno interior cuando el exterior es B (salida AE).
- G4: intento de push a profundidad 2 emite O, intento de pop a 0 emite U; conservar las cuatro flags en el rechazo. No seguir ejecutando R tras el error.
- G5: cuatro motores coinciden y dos generaciones reproducibles; REA confirma profundidad, lecturas y retorno físico seleccionado por pop.

Profundidad/catálogo/celdas acotados y clientes A/B fijados; no direcciones arbitrarias, stdin, asignación dinámica ni recursión general. Cierre al verificar o falsar este contrato.

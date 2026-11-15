# G5b-0: lemas de rearme por órbita — preregistro

2026-11-15. Base `a8dcd4d`. Cierre formal del G5 de restauradores
(`code_rearm_multi_v1/G5_DESIGN.md`) con dos lemas, antes de construir la
imagen G5b-1. Sin imágenes nuevas.

**L1 (JMP no se cifra a sí mismo).** En Olmstead Classic, ejecutar JMP en la
celda `p` no modifica `mem[p]`; se cifra el destino `mem[d]`.
**L2 (rearme de fase de periodo 2).** Bajo `xlat2` existe exactamente una
órbita de periodo 2, `{70, 74}`, y cada opcode activo distinto de HALT tiene
exactamente dos residuos `pc mod 94` donde esa órbita alterna instrucción ↔
NOP efectivo.

- G0 (L1, fuente): citar líneas del vendor `olmstead_original.c` (hash) donde
  `case 'i'` asigna `c` antes de la línea de cifrado.
- G1 (L1, nativo): build instrumentado del vendor (parche registrado, stdout
  intacto) sobre `increment_circuit_loop_v1/run02/increment.mb` con 00..ff+EOF
  y sobre `g5_phase_loop_20261112/run01/positive.mb`. Para cada celda JMP, su
  palabra en visitas consecutivas es igual salvo escritura explícita
  CRAZY/ROT intermedia (contadas aparte). stdout idéntico al build sin
  instrumentar.
- G2 (L2): tabla exhaustiva desde dos fuentes independientes (tablas del probe
  `SE` y `xlat1`/`xlat2` leídos del C del vendor); deben coincidir.
- G3 (controles): (a) intérprete mutante que cifra también la celda JMP: la
  salida de `increment.mb` debe divergir; (b) `xlat2` con dos entradas
  intercambiadas: el comparador de G2 debe detectar el desacuerdo.
- G4: imagen G5b-1, orden arbitrario de instrucciones en línea recta y
  comparación con HeLL = NOT_DEMONSTRATED aquí.

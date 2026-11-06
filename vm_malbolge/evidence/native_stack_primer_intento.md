# Intento nativo de bucle iterante — resultado y obstáculo

## Medida

`vm_malbolge/tools/native_stack_loop_gen.py` emite una imagen Classic de 120
bytes SIN LMAO: todas las celdas decodifican a un opcode válido en su propia
dirección, verificadas una a una.

Layout emitido: celda 0 `/` (IN, op 23), celda 1 `*` (ROT, op 39), celda 2
`<` (OUT, op 5), celdas 3-6 cadena `j j j i` (puntero + JMP), celdas 100-101
celdas de pila.

Ejecución dual-engine:

| stdin | salida | pasos | acuerdo |
|---|---|---|---|
| `A` | byte fijo | 70 | SÍ |
| `AB` | byte fijo | 70 | SÍ |
| `ABC` | byte fijo | 70 | SÍ |
| `HELLO` | byte fijo | 70 | SÍ |

## Qué demuestra

1. El emisor nativo produce imágenes ejecutables: 120 bytes, los dos motores
   coinciden byte a byte (4/4).
2. El loader estricto pasa: todas las celdas decodifican a `ji*p</vo`.
3. La base de verificación dual funciona.

## Qué NO logra

El bucle no itera sobre la entrada: emite un byte fijo para cualquier stdin y
se para en 70 pasos. La cadena `j j j i` no consigue que el JMP vuelva al
inicio del bucle.

## Obstrucción localizada

El opcode `i` (JMP) hace `c = mem[d]`, y el destino debe ser un valor
imprimible (33..126), así que no puede apuntar a la celda 0 directamente. La
coreografía correcta exige que `d` quede sobre una celda cuyo contenido sea la
dirección de reentrada, y esa dirección ha de ser a la vez imprimible y
decodificable como dato válido.

El `simple_cat.hell` (que sí itera, verificado) logra el retorno con
`MOVD loop`: una instrucción loop-resistant de ciclo 2. El emisor nativo no
emite ciclos, emite recetas rectilíneas.

## Síntesis

| Vía | ¿Itera? | ¿Loader estricto? | Coste |
|---|---|---|---|
| `simple_cat` (HeLL) | SÍ, verificado | SÍ | no acepta ciclos de 5 para clasificar 3 opcodes |
| Emisor nativo | no en este intento | SÍ | falta la coreografía del JMP de retorno |

Ninguna de las dos vías itera Y clasifica. El frente 3 queda
NOT_DEMONSTRATED con el obstáculo localizado en la coreografía del salto de
retorno del emisor nativo.

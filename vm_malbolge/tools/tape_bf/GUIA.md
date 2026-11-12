# Compilar movimiento de cinta BF (> y <) a Malbolge Classic

Desde la raíz de `MALBOLGE-MB-DATABASE`, compila el programa Brainfuck con movimiento de cinta a una imagen Malbolge autónoma:

```bash
python3 vm_malbolge/tools/tape_bf/compile.py vm_malbolge/evidence/tape_circuit_loop_v1/swap.bf --output /tmp/tape-swap-user.mb
```

**Regla de oro:** el compilador admite exclusivamente el patrón canónico `,>,+[-.<.,>,+]` con celdas de 16 bits, wrap y EOF=65535. Demuestra el direccionamiento y desacoplamiento de dos celdas de memoria de cinta (`cell0` y `cell1`) controladas por los comandos `>` y `<`. Rechaza rutas de salida preexistentes.

La salida observada al compilar es:

```json
{
  "bf_pattern": ",>,+[-.<.,>,+]",
  "cell_bits": 16,
  "bf_eof": 65535,
  "runtime": "Malbolge Classic, Olmstead EOF=59048",
  "hell_sha256": "2f521cd8a3a8555d50f8d6659c8417d8aa5fd765b02ce7a7b50883922fcbcd0d",
  "image_sha256": "93616e1c3581274b0c5a9bd27b2d4be37eec03a360aef993fc0ea3ecde3a681c",
  "image_bytes": 56946,
  "layout_cells": 1004,
  "entry_data": 57093,
  "installer_ops": 54781,
  "scope": "single BF tape pattern; no arbitrary BF compilation"
}
```

## Ejecución en intérprete Classic (Olmstead)

Para ejecutar la imagen sintetizada con el intérprete nativo Olmstead:

```bash
printf 'AB' | ../Malbolge-PureEpoch/build/olmstead /tmp/tape-swap-user.mb
```

Salida esperada: `BA` (código de salida `rc=0`).

Flujo de pares continuo:

```bash
printf '123456' | ../Malbolge-PureEpoch/build/olmstead /tmp/tape-swap-user.mb
```

Salida esperada: `214365`.

Flujo con longitud impar (semántica BF exacta: el último byte incompleto se descarta al detectar EOF en la celda activa):

```bash
printf 'ABC' | ../Malbolge-PureEpoch/build/olmstead /tmp/tape-swap-user.mb
```

Salida esperada: `BA` (el byte `'C'` no se emite porque `cell1` recibe EOF y el bucle termina limpiamente).

## Diagnóstico de errores

| Resultado | Causa | Acción |
|---|---|---|
| rc 0 y JSON | Compilación exitosa | Ejecutar con intérprete Olmstead (`EOF=59048`). |
| rc 2 y `only ,>,+[-.<.,>,+] is supported` | Código Brainfuck diferente o flags no admitidos | Usar el patrón exacto `,>,+[-.<.,>,+]`. |
| rc 2 y `FileExistsError` | El archivo de salida ya existe | Indicar una ruta de salida nueva. |
| rc 2 y fallo de `make` | Falta gcc, make, flex o bison | Instalar las herramientas de compilación C. |
| Timeout en ejecuciones no-Olmstead | El runtime no respeta la convención de EOF 59048 | Usar el motor canónico Olmstead. |

## Arquitectura

El compilador genera un circuito ternario HeLL donde:
1. `cell0` y `cell1` residen en celdas de datos separadas.
2. Los comandos `>` y `<` dirigen las lecturas (`IN`) y escrituras (`OUT`) hacia las celdas respectivas sin sobrescritura mutua.
3. El bucle `[` evalúa el discriminador de EOF sobre `cell1` (`*ptr`). Al recibir EOF (59048), transfiere el control a `EOF_STOP` ejecutando `HALT`.
4. La extracción de disposición usa el código fuente de LMAO (`third_party/lmao`) compilado temporalmente con el hook `DUMP_LAYOUT`.
5. La síntesis del cargador estricto (`ji*p</vo`) usa el motor BolgeForge (`synthesize_preamble_ops`) con el bootstrap `bootstrap_1533.bin`.

# MBIR Zig backend

Estado: `M1_IN_PROGRESS` — scaffold, decoder seguro y stack mínimo.

Este backend ejecutará gradualmente MBIR_VERSION 0. En M1 solo están
implementados `HALT`, `PUSH_CONST`, `POP` y `DUP`; los otros opcodes se aceptan
por el decoder para validar el formato, pero todavía devuelven
`Unsupported` durante la ejecución.

## Prueba

Desde esta carpeta:

```text
zig version
zig build test
```

No declarar `ZIG_MBIR_DEMONSTRATED` todavía: faltan aritmética, control de
flujo, frames, I/O, errores completos y comparación diferencial con Python.

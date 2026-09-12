# MBIR Zig backend

Estado: `M2_PASS` — semántica de ejecución MBIR v0 implementada en el runtime
Zig; el runner interoperable diferencial todavía es M3.

Este backend ejecuta MBIR_VERSION 0 con aritmética modular, locals, frames,
saltos, llamadas, I/O y errores fail-closed. El ejecutable actual sigue siendo
un smoke executable M1; el transporte externo de bytecode/input se implementa
en M3.

## Prueba

Desde esta carpeta:

```text
zig version
zig build test
```

No declarar `ZIG_MBIR_DEMONSTRATED` todavía: faltan runner interoperable,
comparación diferencial completa con Python y gate de evidencia final.

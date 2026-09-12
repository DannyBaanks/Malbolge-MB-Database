# MBIR Zig backend

Estado: `ZIG_MBIR_V0_DEMONSTRATED`.

Alcance demostrado: los 18 opcodes de `MBIR_VERSION 0` ejecutados por el
runtime Zig, con manejo de stack, locals, frames, saltos, llamadas, I/O,
errores y límite de pasos, comparados byte a byte contra la VM Python de
referencia.

No demostrado: intérpretes de lenguajes fuente, MBIR alojado en Malbolge,
transporte streaming/IPC, ni salida over 4096 bytes. Esos quedan para
milestones posteriores y necesitan evidencia nueva.

## Ejecutar

Desde esta carpeta:

```powershell
zig build test
zig build -Doptimize=ReleaseSafe
py tests\differential.py --manifest evidence\m3_differential_latest.json
```

Runner externo:

```powershell
zig-out\bin\mbir-zig.exe <program.mbir> [input.bin] [--max-steps N]
```

El runner escribe un envelope JSON `mbir-zig-result/1` por stdout, sin stderr
en ejecución normal. Salida MBIR: campo `output` como arreglo de bytes.

Ver `GUIA.md` para salida real, lectura de campos y trampas.

## Evidencia

- `evidence/m1_smoke.json` — decoder y runtime M1.
- `evidence/m2_smoke.json` — semántica de los 18 opcodes.
- `evidence/m3_differential.json` — primera corrida diferencial 22/22.
- `evidence/m3_differential_second.json` — segunda corrida diferencial 22/22.
- `evidence/hashes.json` — SHA-256 de binario, fuentes, pruebas y evidencia.

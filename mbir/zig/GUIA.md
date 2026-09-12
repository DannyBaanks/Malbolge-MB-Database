# Guía rápida — MBIR Zig

## El comando que buscas

Desde `mbir/zig`:

```powershell
zig build -Doptimize=ReleaseSafe
py tests\differential.py --manifest evidence\m3_differential_latest.json
```

## Regla de oro

Si la comparación Python/Zig no pasa, no declares `DEMONSTRATED`. El resultado
sin ejecutar no cuenta.

## Comandos probados

### Compilar y probar

```powershell
zig build test
```

Salida real: sin texto, exit 0.

```powershell
zig build -Doptimize=ReleaseSafe
```

Salida real: sin texto, exit 0.

### Comparación diferencial

```powershell
py tests\differential.py --manifest evidence\m3_differential.json
```

Salida real: 22 casos `PASS` y, al final:

```text
differential: 22/22 PASS
manifest: evidence\m3_differential.json
```

### Ejecutar un programa MBIR

Formato:

```powershell
zig-out\bin\mbir-zig.exe <program.mbir> [input.bin] [--max-steps N]
```

Ejemplo probado: programa bytes `01 5a 10 00` (`PUSH_CONST 0x5a`, `OUT_BYTE`, `HALT`).

Salida real:

```json
{"schema":"mbir-zig-result/1","status":"HALTED","error":null,"steps":3,"output":[90]}
```

Exit real: `0`.

## Cómo leer la salida

| Campo | Significado |
|---|---|
| `status=HALTED` | El programa ejecutó hasta `HALT`. |
| `status=MAX_STEPS` | El límite de pasos detuvo el programa. |
| `status=ERROR` | Error MBIR o de decodificación. |
| `error=null` | No hubo error MBIR. |
| `steps` | Número de instrucciones ejecutadas. |
| `output` | Bytes emitidos por `OUT_BYTE`. |

## Trampas

- Usa `py`, no `python`, en esta máquina.
- Después de editar Zig, reconstruye antes de repetir la diferencial.
- Los directorios `.zig-cache/` y `zig-out/` no se versionan.
- `MAX_STEPS` es un estado controlado, no una caída del proceso.

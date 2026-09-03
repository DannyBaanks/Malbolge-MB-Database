# Toolchain

Vendored and built toolchain used to produce Malbolge artifacts.

## Vendored Packages

| Package | Version | Source | Commit/Provenance | Path |
|---------|---------|--------|-------------------|------|
| LMAO (Low-level Malbolge Assembler, Ooh!) | 0.6.0 | https://github.com/esoteric-programmer/LMAO | `3ea747e16b45ea7627018b291409b12c1f9ca3dc` (HEAD as of 2026-09-03) | `third_party/lmao` |

## Build Artifacts

| Binary | Path | SHA256 | Build |
|--------|------|--------|-------|
| lmao.exe | `third_party/lmao/bin/lmao.exe` | `A734A030E32A2B942113774EFE5FFC6C79468CE71B663A6A02AF8A50747BD9C3` | `py powershell tools/build_lmao.ps1` |

### Toolchain dependencies for building LMAO

- gcc (Mingw-w64, 16.1.0)
- win_flex 2.6.4 (`CoEvoLang/command_surface` provider, external path)
- win_bison 3.8.2 (same)

`tools/build_lmao.ps1` rebuilds `bin/lmao.exe` from the vendored source.

## Quick smoke test

```
tools\..\third_party\lmao\bin\lmao.exe example_simple_hello_world.hell -o %TEMP%\hw.mb
runners\malbolge-original\malbolge.exe %TEMP%\hw.mb   # -> "Hello, World!"
```

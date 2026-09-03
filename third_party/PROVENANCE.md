# third_party Provenance

All vendored third-party code recorded here with immutable provenance.

## lmao/

- **Upstream**: https://github.com/esoteric-programmer/LMAO
- **Version**: 0.6.0
- **Commit**: `3ea747e16b45ea7627018b291409b12c1f9ca3dc` (HEAD, fetched 2026-09-03)
- **License**: GPL-3.0+ (see `third_party/lmao/LICENSE`)
- **Author**: Matthias Lutter <matthias@lutter.cc>
- **Files**: full source tree (src/, examples, datamodule.txt, Makefile); `.git` removed; `bin/` regenerated locally and gitignored except where committed intentionally.
- **Local build**: `py powershell tools/build_lmao.ps1` (win_flex 2.6.4 + win_bison 3.8.2 + gcc). Output binary SHA256 recorded in `docs/TOOLCHAIN.md`.

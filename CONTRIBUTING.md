# Contribuir a Malbolge MB Database

## Flujo de trabajo

Los cambios entran por **pull request** hacia `master`. No se hace push directo
a `master`: la rama está protegida y exige la CI en verde.

```sh
git switch master
git pull --ff-only origin master
git switch -c <tipo>/<descripcion>     # p. ej. fix/is-eof, ci/zig-tests
# ... cambios ...
zig fmt mbir/zig                       # formato canónico
zig build test --summary all           # en mbir/zig: 9/9 en milisegundos
git push -u origin HEAD
gh pr create --fill
```

Convención de mensajes: `<tipo>: <resumen>` en español, con `tipo` ∈
`fix`, `feat`, `docs`, `test`, `ci`, `chore`.

## Qué corre la CI (y qué no)

| Job | Qué hace | Coste |
|---|---|---|
| `zig-tests` | `zig build test --summary all` en `mbir/zig` | ~milisegundos |
| `zig-fmt` | `zig fmt --check mbir/zig` | ~milisegundos |
| `python-fast` | `py_compile` de todo el repo + suite MBIR | segundos |
| `repo-gate` | bloquea cambios en evidencia no declarados | segundos |

**La CI corre la suite en Zig, no el oráculo Python.** El oráculo Python tarda
~1 min por imagen y la quine ~22 min: eso queda para reproducción manual,
documentada en [`REPRODUCING.md`](REPRODUCING.md). Si un cambio necesita esas
corridas, ejecútalas en local y pega el resultado en el PR.

## Reglas de evidencia

Los artefactos bajo `evidence/` (`.json`, `.mb`, `hashes.sha256`) son
**registros append-only**: documentan lo que se midió. No los reescribas.

`repo-gate` falla si un PR toca evidencia. Si el cambio **debe** tocarla (nueva
medición, corrección documentada), dilo explícitamente en el cuerpo del PR con
la palabra `evidencia`.

Nunca edites un JSON de evidencia a mano para que una afirmación cuadre: mide de
nuevo o deja la afirmación como `NOT_DEMONSTRATED`.

## Tests en Zig

El oráculo de referencia MBIR vive en `mbir/zig` (Zig 0.16.0). Es el núcleo
rápido del repo: la suite completa corre en milisegundos.

```sh
cd mbir/zig
zig build test --summary all
zig fmt --check .
```

Si añades código Zig, `zig fmt` debe pasar limpio y los tests nuevos deben correr
en la suite de `mbir/zig/tests/runtime.zig`.

## Antes de abrir el PR

- [ ] `zig fmt mbir/zig` no deja cambios
- [ ] `zig build test --summary all` pasa 9/9 (o más)
- [ ] `python3 -m unittest discover -s mbir/tests` pasa
- [ ] No tocaste evidencia, o lo declaraste en el cuerpo del PR
- [ ] `git diff --check` limpio

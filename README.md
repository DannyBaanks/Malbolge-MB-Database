# Malbolge MB Database

Base de datos reproducible y laboratorio de investigacion para programas Malbolge sustanciales, runtimes en otros lenguajes, y el boundary de middleware que los conecta a substratos de ejecucion.

## Mision

Investigar, construir, ejecutar y conservar programas `.mb` — especialmente interpretes/runtimes de otros lenguajes implementados sobre Malbolge. MBIR es el
boundary de intercambio entre un adaptador frontend/backend y un substrato; no es
una VM omnilingue.

Objetivos a largo plazo:

```
source program -> frontend/adapter -> MBIR -> backend adapter -> substrate
                                      (native Malbolge, Rustbolge, Pibolge, ...)
```

## Principio Central

**NUNCA ADIVINAR.** Si una propiedad no esta demostrada por codigo, documentacion, ejecucion, prueba, trazo, hash, artefacto o reproduccion independiente, clasificala:

```
NOT_DEMONSTRATED
```

README ≠ evidencia. Nombre de archivo ≠ evidencia. Claim ≠ implementacion.

## Pistas de Lenguaje

| Lenguaje | Target | Variante | Estado | Hito mas alto | Evidencia |
|----------|--------|---------|--------|---------------|-----------|
| Python   | python.mb | Unshackled (primario) | REFERENCE_FRONTEND | P2 (frontend) | P1 ref VM, P2 frontend |
| Swift    | swift.mb  | Unshackled (primario) | NOT_STARTED | — | — |
| Rust     | rust.mb   | Unshackled (primario) | NOT_STARTED | — | — |
| Java     | java.mb   | Unshackled (primario) | NOT_STARTED | — | — |
| C        | c.mb      | Unshackled (primario) | NOT_STARTED | — | — |

> Estado honesto: P1 es una **VM de referencia Python** (evidencia REFERENCE_MODEL) y
> P2 es un **frontend Python AST → bytecode** (evidencia FRONTEND). El boundary MBIR y
> las primitivas Malbolge estan parcialmente demostrados; un backend de ejecucion MBIR
> completo sigue siendo **NOT_DEMONSTRATED**.

## Estructura del Repo

```
MALBOLGE-MB-DATABASE/
├── README.md              ← este archivo
├── DATABASE.md            ← overview y navegacion de la base de datos
├── LICENSE
├── registry/              ← metadata estructurada (lenguajes + substratos externos: registry/substrates.json)
├── docs/                  ← definiciones, variantes, modelo de evidencia
├── references/            ← documentacion de referencia externa
├── tools/                 ← utilidades para build, ejecucion, pruebas
├── runners/               ← entornos de ejecucion reproducibles de Malbolge
├── python/                ← pista python.mb (ACTIVO)
├── swift/                 ← pista swift.mb (NOT_STARTED)
├── rust/                  ← pista rust.mb (NOT_STARTED)
├── java/                  ← pista java.mb (NOT_STARTED)
└── c/                     ← pista c.mb (NOT_STARTED)
```

## Como Usar

1. Lee `DATABASE.md` para navegacion.
2. Lee `docs/DEFINITIONS.md` para terminologia.
3. Lee el `STATUS.md` del lenguaje target para el estado actual.
4. Lee `docs/EVIDENCE_MODEL.md` antes de interpretar cualquier resultado.

## Regla Anti-Fake

Para demostrar `print(2 + 3)`, NO aceptamos un `.mb` que simplemente imprima `5`. Tenemos que demostrar una representacion operacional equivalente a:

```
PUSH 2
PUSH 3
ADD
PRINT
```

y que cambiar los operandos modifica el resultado correctamente sin fabricar un programa de print independiente para cada salida.

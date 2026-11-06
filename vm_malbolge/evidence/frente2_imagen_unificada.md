# Frente 2 — imagen unificada sobre el andamio del cargador

## Etapa 1: el andamio absorbe la primitiva del emisor (SIN BLOQUEANTE)

Graft: `mbir_m2_loader.hell` + las celdas de datos de la primitiva de despacho
del emisor nativo, colocadas con `.OFFSET 57000` (región libre).

Generador: `vm_malbolge/tools/unified_graft.py`

### Medidas

| Medida | Valor |
|---|---|
| Base (`mbir_m2_loader.hell`) | 40.310 B |
| Con injerto | 40.967 B |
| Coste del injerto | **657 B** |
| Margen restante | 18.082 B |
| Celdas añadidas | 3 pares dato (const 85, rot 84, target C1) |

### El cargador sigue funcionando

Los 4 vectores del hito M2, sobre la imagen injertada:

| Vector | Entrada | Salida | Pasos | Estado |
|---|---|---|---|---|
| push + out | `01411000` | `41` | 41.692 | HALTED |
| push 42 + out | `01421000` | `42` | 41.692 | HALTED |
| halt | `00` | (vacía) | 42.411 | HALTED |
| push + out + halt | `014100` | (vacía) | 42.913 | HALTED |

**4/4 PASS.** El injerto no rompe el cargador.

### Qué demuestra

El andamio del cargador **sí** tiene sitio para la maquinaria del emisor
nativo, y esa maquinaria no gasta flags de código (la dimensión que E3 midió
como el muro). El conflicto de la celda 0 se resuelve con `.OFFSET`.

### Conflicto resuelto y conflicto pendiente

| Conflicto | Estado |
|---|---|
| Ambos mecanismos quieren la celda 0 | ✅ resuelto con `.OFFSET` |
| Presupuesto de flags de código | ✅ no aplica: el emisor solo usa celdas de dato |
| Presupuesto de células | ✅ 18.082 B de margen tras el injerto |
| **Las rutas del emisor imprimen constantes, no computan sobre lo cargado** | ❌ **pendiente** |

## Etapa 2 (pendiente): rutas que operen sobre lo cargado

Las recetas del emisor trabajan sobre literales. Para que la imagen unificada
"cargue un programa Y ejecute la aritmética", la ruta necesita leer los
operandos desde las celdas `prog_1`/`prog_3` que el cargador ya llenó.

Eso exige apuntar el puntero de datos a una celda cuya dirección depende del
opcode — que es exactamente el selector dinámico de 72 rutas medido en el
frente 1. La composición de ambos está disponible; falta escribirla.

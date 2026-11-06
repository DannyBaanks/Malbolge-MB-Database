# Corrección al frente 1 — la imagen nativa NO itera sobre el flujo

## Medida que corrige el veredicto anterior

`mbir_native_cmp_decimal.mb`, flujos de distinta longitud:

| stdin | Salida | Pasos |
|---|---|---|
| `30` | `310a` | 40 |
| `303` | `310a` | 40 |
| `3030` | `310a` | 40 |
| `303030` | `310a` | 40 |
| `303040` | `310a` | 40 |

**Todos idénticos.** La imagen consume un byte, auto-enruta, emite y se para.

## Qué fue el error de interpretación

La traza con `"35"` mostró tres `IN` y la leí como "vuelve al despacho y busca
un segundo opcode". Los pasos 238/250/278/286 leían **EOF**, no bytes: la
imagen seguía pidiendo entrada después de agotar el flujo, y el oráculo le
devolvía 59048. No hay iteración sobre bytes reales.

## Veredicto corregido

| Componente | Estado real |
|---|---|
| Auto-enrutado por el dato (`f(byte) = byte + 1`) | ✅ **verificado** — la cadena crazy + JMP indirecto existe y está reconstruida |
| Iteración sobre un flujo de varios bytes | ❌ **NO** — es one-shot |
| Selector dinámico de 72 direcciones | ✅ **verificado** (imagen de la clave sobre 0..255) |
| Pila de profundidad 2 | ❌ no construible sobre esta imagen heredando el flujo: no itera |

## Consecuencia para la campaña

El frente 1 queda con lo que sí tiene: auto-enrutado y selector de 72 rutas.
Los frentes 3 y 5 **siguen bloqueados** y el bloqueante es ahora más preciso:
no existe en el corpus una imagen Classic que itere sobre un flujo de bytes.
Construirla exige flags de código nuevos, que E3 midió como el muro.

## Lo que sí queda como resultado utilizable

La cadena de salto computado (`crazy(byte, c) → crazy(·, dato) → JMP`) está
reconstruida y verificada. Es la primitiva correcta para un PC genérico; lo
que falta es el cableado de vuelta, y su coste en flags está medido.

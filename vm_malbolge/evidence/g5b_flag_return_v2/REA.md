# Referencias de traza REA

Las corridas se hicieron con `rea.trace_malbolge`, `eof_mode=olmstead_1998`, entrada vacía, límite de 10 000 pasos y captura máxima de 4000 eventos. Ambas respuestas conservaron la lista completa (`events_truncated=false`). El ID identifica el registro completo de REA.

| Caso | Evidencia REA | Imagen SHA-256 | Estado | Pasos | Bytes de salida | Eventos |
|---|---|---|---|---:|---|---:|
| Positivo | `ev_e941b2d8bdb8db08f074d338c7e97eb527e1dbc0f8d7232c7fde1a6f1b92a77a` | `9aa1a39cc4f1cc1a2d55b119a26f52a76b5d1d2a62eece59ef915bfe0ed5f3b6` | HALTED | 3756 | `[98,230,110,230]` (`62e66ee6`) | 3756 |
| Control negativo | `ev_e5667c55af1e9a43e2f1cb39a210dc09a73dacd5a75b28470f275bf1c8a57918` | `5696889bc004600ed1fc87b4ebf13a5ed9529b4591d20e3d3f812fc8e8af5e46` | HALTED | 3672 | `[98,230]` (`62e6`) | 3672 |

La traza positiva observa cuatro visitas a la operación `38058` con `d=40006` y las continuaciones `15000, 15004, 15008, 15012`. El control observa dos visitas y las continuaciones `15000, 15012`.

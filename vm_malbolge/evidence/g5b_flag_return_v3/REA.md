# Referencias de traza REA — G5b P3

Se usó `rea.trace_malbolge` 6.9.0 con entrada vacía, `eof_mode=olmstead_1998`, máximo de 10 000 pasos y captura de hasta 4096 eventos. Las dos imágenes terminaron antes del límite y conservaron todos sus eventos (`events_truncated=false`).

| Caso | Evidencia REA | SHA-256 de la imagen | Estado | Pasos/eventos | Bytes de salida |
|---|---|---|---|---:|---|
| Positivo `rr → ll → rl → lr` | `ev_0738dd8e4fefebb83e449a1ef38bfc94b1e8938d8e1ac2bf9ac2f8b7b9463fa1` | `5c72beaf362d783f7846cd74463cf729786a1c9c0bfc9e0ea9a6f36a91913d72` | HALTED | 4014 / 4014 | `[98,230,110,230]` (`62e66ee6`) |
| Control: toggle extra de `f_root` en `rr` | `ev_85e2fe5a9e075ffc21577f0d370f08bd96570095f2a8bba36f7c4c05c51b5dbc` | `8450625bfc71fce5191bfa59468b5a9bf581d31f05c110cb7b2ff109b1cf2423` | HALTED | 3944 / 3944 | `[98]` (`62`) |

La imagen positiva visita `pc=38058` cuatro veces con `d=40006`; las salidas ocurren en `15000, 15004, 15008, 15012`. La imagen de control visita el sitio una vez y emite desde `15012`.

| Caso | Paso | PC | Operación | Acumulador | D |
|---|---:|---:|---|---:|---:|
| Positivo | 3952 | 38058 | `crazy` compartida | 39999 | 40006 |
| Positivo | 3972 | 38058 | `crazy` compartida | 12130 | 40006 |
| Positivo | 3987 | 38058 | `crazy` compartida | 21990 | 40006 |
| Positivo | 4004 | 38058 | `crazy` compartida | 7534 | 40006 |
| Control | 3934 | 38058 | `crazy` compartida | 39999 | 40006 |

| Caso | Paso | Continuación | Operación | Acumulador |
|---|---:|---:|---|---:|
| Positivo | 3963 | 15000 | `out` | 12130 |
| Positivo | 3979 | 15004 | `out` | 21990 |
| Positivo | 3996 | 15008 | `out` | 7534 |
| Positivo | 4013 | 15012 | `out` | 21990 |
| Control | 3943 | 15012 | `out` | 12130 |

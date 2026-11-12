# Enmienda previa: emitir la nueva plantilla relocalizada

2026-11-11. Tras observar el modelo y generar una imagen relocalizada nueva, ampliar el compilador especializado para aceptar la plantilla `relocated_candidate.mb` por su SHA-256 completo, además de la referencia original. Registrar esta enmienda antes de compilar esa nueva plantilla desde BF.

Pasa sólo si: (1) `,+[-.,+]` y la convención exacta BF16/EOF=65535 producen bytes idénticos a la plantilla autenticada; (2) el artefacto compilado ejecuta eco y halt en EOF bajo Olmstead; (3) el REA modificado se prueba en su frontera MCP fuente con `olmstead_1998`; (4) controles rechazan BF, EOF, ancho y plantilla inválidos. La plantilla es un backend específico de eco, no un compilador BF general ni el bucle compacto previo. Las pruebas previas del modelo e instalador son exploratorias y se conservan.

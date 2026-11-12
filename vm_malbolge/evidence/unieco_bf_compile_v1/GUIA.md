# Cómo generar el eco relocalizado

Desde la raíz de `MALBOLGE-MB-DATABASE`:

```bash
UNIECO_DIR="$(mktemp -d)" && python3 vm_malbolge/evidence/unieco_bf_compile_v1/compile_bf.py vm_malbolge/evidence/unieco_bf_compile_v1/echo.bf --template vm_malbolge/evidence/unieco_bf_compile_v1/relocated_candidate.mb --output "$UNIECO_DIR/cat.mb"
```

Regla de oro: este compilador sólo acepta el patrón `,+[-.,+]`, celdas BF de 16 bits con wrap y EOF=65535. Produce una plantilla autenticada; no traduce programas Brainfuck arbitrarios.

La salida real de ese comando fue:

```text
compiled bytes=33822 sha256=c7b0aef98363242607c1fb13aa964fd412da057bcea04105f7e9b8559e986d13
```

| Resultado | Significado | Qué hacer |
| --- | --- | --- |
| `compiled bytes=...` y código 0 | Se creó el archivo en la ruta elegida. | Ejecutarlo con un intérprete Malbolge que use EOF de Olmstead. |
| `unsupported Brainfuck program` | El código BF contiene otra secuencia de operaciones. | Limitarse al patrón soportado. |
| `requires 16-bit...` | La convención de celda o EOF no coincide. | Usar los valores por defecto del comando. |
| `template SHA-256 mismatch` | La plantilla no coincide con un backend admitido. | Revisar su procedencia; no cambiar el hash para saltarse la comprobación. |
| `File exists` | El archivo destino ya existe. | Elegir una ruta nueva: el compilador no sobrescribe. |

La imagen se verificó con Olmstead de 1998. Algunos motores detienen el host al alcanzar EOF y otros usan otro valor: no interpretes ese resultado como prueba de halt interno. El REA ya conectado antes del cambio necesita actualizarse para aceptar `eof_mode=olmstead_1998`; las pruebas de este pack ejecutan el código fuente actualizado, no ese proceso anterior.

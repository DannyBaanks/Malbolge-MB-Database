# Compilar el incremento BF a Malbolge

Desde la raíz de MALBOLGE-MB-DATABASE, usa una ruta de salida nueva:

```bash
python3 vm_malbolge/tools/increment_bf/compile.py vm_malbolge/evidence/byte_increment_v1/increment.bf --output /tmp/increment-user-20261112.mb
```

**Regla de oro:** el compilador admite solamente `,+[-+.,+]` con celdas BF de 16 bits, wrap y EOF=65535. No interpreta ni traduce otros programas BF. Rechaza rutas de salida existentes.

La salida observada al ejecutar el comando fue:

```json
{
  "bf_pattern": ",+[-+.,+]",
  "cell_bits": 16,
  "bf_eof": 65535,
  "runtime": "Malbolge Classic, Olmstead EOF=59048",
  "hell_sha256": "3bcd18c3d70baab22c21c9f567570c5ec260c06a950209caa700b1ce863fcbc5",
  "image_sha256": "aec09e9fe64ae4b456818ce1960b7ecb92ccfae456592c2d5b8413b6190757f1",
  "image_bytes": 56570,
  "layout_cells": 1090,
  "entry_data": 56717,
  "installer_ops": 56116,
  "scope": "single BF pattern; no arbitrary BF compilation"
}
```

El resultado transforma cada byte a `(byte + 1) mod 256` y termina al EOF de Olmstead. Por ejemplo, con el intérprete hermano disponible:

```bash
printf 'ABCD' | ../Malbolge-PureEpoch/build/olmstead /tmp/increment-user-20261112.mb
```

Salida observada: `BCDE` (sin salto de línea añadido por el programa).

| Resultado | Significado | Qué hacer |
|---|---|---|
| rc 0 y JSON | Imagen creada | Ejecutarla con un intérprete Classic que implemente EOF=59048. |
| rc 2 y `only ... is supported` | Patrón o convención no admitidos | Usar el patrón y las convenciones indicadas. |
| rc 2 y ruta existente | Se preservó el archivo existente | Elegir otra ruta de salida. |
| rc 2 y error de `make` | Falta una herramienta o falló la compilación temporal de LMAO | Comprobar `gcc`, `make`, `flex` y `bison`. |
| EOF en un motor con otra convención | El comportamiento puede diferir | Usar semántica Olmstead, no asumir que EOF siempre es 59048. |

El compilador genera HeLL y sintetiza una imagen nueva; no copia una imagen de incremento. Usa el código fuente de LMAO incluido en `third_party/lmao` y el backend incluido aquí; no requiere el checkout hermano de BolgeForge. Requiere Python 3, gcc, make, flex y bison. La ejecución de ejemplo requiere además el intérprete Olmstead indicado.

El backend de síntesis deriva de BolgeForge (licencia MIT incluida en `backend/LICENSE`). `bootstrap_1533.bin` conserva el prefijo de instalación y los dos bytes finales del programa `cat.mal` de referencia de Matthias Lutter; no contiene el programa de incremento ni demuestra que BF arbitrario esté compilado. LMAO está distribuido en el repositorio con su propia licencia GPL. El compilador no escribe en sus fuentes: construye la variante de extracción de la disposición en un directorio temporal.

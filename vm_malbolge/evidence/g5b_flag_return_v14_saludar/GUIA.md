```sh
MALBOLGE_MB_DATABASE_ROOT='/home/danny/Development/ISyCo Git/MALBOLGE-MB-DATABASE' sh ejecutar.sh
```

Ejecutar desde esta carpeta. Regla: usar la imagen conservada; cualquier reconstrucción debe escribir en un directorio nuevo.

Salida real del comando, exit 0:

```text
Hola
```

ejecutar.sh usa Olmstead nativo del proyecto hermano Malbolge-PureEpoch y ejecuta run02/saludar.mb. El programa no necesita Python para correr. saludar.py es únicamente la referencia de salida; probe.py es el generador y verificador del ejemplo.

| Resultado | Significado |
|---|---|
| Hola y salto de línea, exit 0 | imagen nominal correcta |
| Hola seguido de ! | se ejecutó el control de retorno roto |
| salida vacía | se ejecutó el control que omite la llamada |

La ruta del repo en el comando es la de esta máquina; ajustar MALBOLGE_MB_DATABASE_ROOT si se mueve el checkout. No interpretar un .mb como ejecutable ELF: necesita el intérprete Malbolge. La prueba hace una sola llamada por ejecución; no demuestra un compilador Python general ni un cuerpo cíclico reutilizable.

# REA: Python, BF16 e incremento Malbolge acotado

2026-11-12. Este es un contraste exploratorio de artefactos existentes, no una nueva implementación ni un compilador BF→Malbolge.

REA capturó procesos separados para la referencia Python y el ejecutor BF16: con `41424344` ambos informaron `42434445` y terminaron con rc=0. El replay REA de `increment_four.mb` produjo `42434445`, HALTED en 55471 pasos; el control produjo `42430e45`, HALTED en 55442. Los replays sólo retienen sus primeros 64 eventos, no la ejecución completa. Las respuestas REA de las cuatro llamadas están conservadas con rutas del repo sustituidas por `<repo>`; no son los originales byte por byte.

Una comprobación local separada ejecutó Python, BF16 y Olmstead para `41424344`, `00ff80fe`, `00000000` y `ffffffff`, con salidas iguales al incremento modular. El control nativo con `41424344` produjo `42430e45`. `compare.py` registra rc, salida y hashes; `check_evidence.py` comprueba las capturas guardadas.

Como punto de partida para el siguiente diseño, REA volvió a trazar la celda de código CRAZY del pack anterior: las visitas al PC 58550 son `[62,62]` en el positivo y `[62,21]` en el control; la ejecución capturada no está truncada. Los extractos guardados incluyen visitas, escrituras, identificadores y huellas, pero no la traza completa de esta nueva llamada. Las trazas completas de la ejecución anterior están en `increment_stream_v2/rea_revisit_{positive,control}.redacted.json`; no se atribuyen a esta nueva ejecución.

El nuevo contraste no conecta la celda CRAZY con el cuerpo de incremento: `increment_four.mb` sigue usando cuatro bloques desenrollados. Longitud arbitraria, EOF limpio, rearme de todo el cuerpo y compilación BF→Malbolge permanecen **NOT_DEMONSTRATED**. Python/BF son capturas de procesos mediante wrappers de salida hexadecimal; REA Malbolge es replay, y Olmstead es una ejecución nativa no instrumentada. El control no es una prueba global para todas las entradas.

Se probó además REA sobre el control R/R2 del ensayo anterior, pero el adaptador disponible devolvió un error de validación (`output_bytes` negativo); no se considera resultado del programa ni se compara con Olmstead. El positivo R/R2 terminó en el replay, con captura truncada antes de la zona de interés.

Reproducción local, desde la raíz del repositorio:

```sh
python3 vm_malbolge/evidence/rea_pipeline_recheck_20261112/compare.py
python3 vm_malbolge/evidence/rea_pipeline_recheck_20261112/check_evidence.py
```

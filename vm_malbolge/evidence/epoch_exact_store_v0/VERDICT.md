# Escritura exacta de un byte — experimento exploratorio v0

**Hipótesis:** una imagen Classic puede recibir un byte desconocido al generar la imagen, escribirlo exactamente en una celda y recuperarlo sin perderlo. H0: al menos un byte no cumple este contrato.

**Resultado: CONDITIONAL_PASS, dominio 0..255, un disparo.** `probe.py` compara cada valor con el oráculo Python y el runner C; verifica el estado de la celda 90 mediante un trazador Python separado, y recupera el byte con diez operaciones ROT, no usando el acumulador que dejó la escritura.

| Claim | Estado |
|---|---|
| 256 entradas: escritura y lectura exactas, imagen única, doble motor | PASS |
| Mutante elimina CRAZY de escritura; ambos motores emiten 0x54 y la traza observa C1 sin alterar | PASS |
| Escritura arbitraria en dirección dinámica, palabras de 10 trits, búsqueda y rearme repetible | NOT_DEMONSTRATED |
| Middleware PureEpoch integrado o servicio de dos procesos | NOT_DEMONSTRATED |
| Loader estricto completo | FAIL: celdas de datos 41,70,71,90,91,92 no son opcodes válidos al cargar. Los dos motores usados aceptan la imagen; no extrapolar a loader estricto. |

Secuencia: A=0 inicial; `crazy(0,40)=29524` en 70; `crazy(29524,40)=0` en 90; `crazy(0,0)=29524` en 90. Tras IN(V), `crazy(V,29524)` en 70 y `crazy(crazy(V,29524),29524)=V` en 90. Diez pares MOVD/ROT recuperan 90 y restauran su contenido. El mutante sustituye la escritura final CRAZY por NOP; siempre lee C1, cuyo byte bajo es 0x54. Para entrada 0x54 la salida coincide por casualidad: el estado interno y los otros 255 valores distinguen el control.

El protocolo se inspira en la involución usada en PureEpoch; no importa ni ejecuta su código. La traza replica semántica y no constituye un tercer motor independiente. Las salidas crudas C incluyen el 0x0a del runner y se conservan íntegramente. Ejecución: `python3 vm_malbolge/evidence/epoch_exact_store_v0/probe.py` desde la raíz del repositorio. El script sobrescribe las salidas del pack: para preservar el original, ejecutar una copia en otro directorio.

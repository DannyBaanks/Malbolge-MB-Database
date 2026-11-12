# Veredicto: Movimiento de Cinta Brainfuck (> y <) sobre Malbolge Classic

2026-11-12. Se demostró la implementación de movimiento de puntero de cinta Brainfuck (`>` y `<`) sobre memoria desacoplada en Malbolge Classic. La imagen generada ejecuta de forma continua el bucle de intercambio de pares `,>,+[-.<.,>,+]`, preservando celdas de almacenamiento independientes (`cell0` y `cell1`), procesando flujos continuos y deteniéndose de manera autónoma ante EOF bajo la semántica de Olmstead (59048).

## Tabla de Puertas

| Puerta | Veredicto | Evidencia y Alcance |
|---|---|---|
| G0: Álgebra y control negativo | **PASS** | `circuit.py` y `verification.raw.json`: la memoria de cinta de 2 celdas desacopladas intercambia pares ordenadamente. El control negativo que simula ausencia de movimiento de cinta (colapsando a una celda) falla en 256 de 256 pares probados (100% de detección). |
| G1: Imagen estricta | **PASS** | Imagen canónica `tape_swap.mb` (56.946 B, SHA-256 `93616e1c...`) aceptada por el cargador estricto (`ji*p</vo`). La mutación deliberada de un opcode en el preámbulo provoca rechazo inmediato por el cargador. |
| G2: EOF autónomo | **PASS** | Finalización limpia con `rc=0` y 0 bytes espurios para entrada vacía, secuencias impares (descarte exacto del byte incompleto según semántica BF) y flujos masivos. |
| G3: Tortura adversarial y BF16 | **PASS** | Batería adversarial completa: flujo masivo de 10.000 bytes (5.000 pares aleatorios), tormenta de 1.000 bytes NUL, tormenta de 1.000 bytes 0xFF, secuencia completa 0..255 (128 pares) y 256 pares individuales. Coincidencia exacta bit a bit (0 discrepancias) contra el intérprete BF16 del repositorio (`bf16.py`). |
| G4: Compilador reproducible | **PASS** | Compilador dedicado `vm_malbolge/tools/tape_bf/compile.py`. Genera el ensamblador HeLL, extrae la disposición de memoria con LMAO y sintetiza el instalador con BolgeForge de manera autónoma sin requerir imágenes preexistentes. |

## Arquitectura y Desacoplamiento de Cinta

1. **Memoria desacoplada:** A diferencia de los flujos de un solo acumulador/celda (echo o incremento), el movimiento de cinta requiere que múltiples valores sobrevivan simultáneamente. Las celdas `cell0` y `cell1` residen en ubicaciones fijas de la memoria Malbolge con sus propias banderas de despacho (`F1..Fn`) y rutinas de manipulación (`U_CRAZY`).
2. **Semántica de Puntero:**
   - `,`: Lectura de entrada almacenada en `cell0`.
   - `>`: Avance de puntero hacia `cell1`.
   - `,`: Lectura de entrada almacenada en `cell1`.
   - `[`: Condición de bucle sobre la celda activa (`cell1`). Se evalúa la máscara de EOF contra 59048. Si es EOF, bifurca a `HALT`.
   - `.`: Emisión del contenido de `cell1`.
   - `<`: Retroceso de puntero hacia `cell0`.
   - `.`: Emisión del contenido de `cell0` (logrando el intercambio de la tupla).
   - `]`: Reenganche de bucle al inicio del ciclo.
3. **Rearme:** Tras cada ciclo de intercambio, los slots temporales auxiliares se limpian a la constante neutra 29524, garantizando que un flujo arbitrariamente largo no sufra degradación de estado o interferencia cruzada.

## Batería Adversarial Anti-Fake

Para evitar falsos positivos o ilusiones de éxito ("antifake locotron"):
- **Control Negativo de Celda Única:** Se demostró matemáticamente y por oráculo que si los comandos `>` y `<` fuesen nulos y las lecturas se realizaran sobre la misma celda de memoria, la entrada `AB` produciría `BB`. En 256 pares con valores distintos, el modelo de celda única produce 256 fallos (0% de aciertos), mientras que la cinta real produce 256 aciertos (100%).
- **Control de Mutación de Instalador:** Modificar un único byte en el preámbulo del instalador (`offset=200`) invalida la gramática del cargador estricto, resultando en rechazo inmediato.
- **Tortura de Flujo Masivo (10.000 bytes):** Ejecutado sobre el binario nativo C de Olmstead con 10.000 bytes pseudoaleatorios deterministas (`seed=0xDEADBEEF`), produciendo exactamente 5.000 pares intercambiados sin fugas de memoria, divergencias ni bloqueos.

## Reproducción

Desde la raíz del repositorio:

```bash
# Ejecutar la suite adversarial completa
python3 vm_malbolge/evidence/tape_circuit_loop_v1/verify.py vm_malbolge/evidence/tape_circuit_loop_v1/tape_swap.mb

# Compilar una imagen nueva desde el programa BF
python3 vm_malbolge/tools/tape_bf/compile.py vm_malbolge/evidence/tape_circuit_loop_v1/swap.bf --output /tmp/tape_reproduced.mb
```

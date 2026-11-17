# Reproducción de resultados

## Cómo Reproducir y Ejecutar

### 1. Verificar el Stored-Program Loader & PC (Hito M2)
Para cargar un programa de bytecode MBIR completo desde STDIN a la memoria RAM de Malbolge y ejecutarlo mediante el Program Counter (`PC`):

```bash
# Vector 1 M2: Carga en RAM y ejecución por PC de PUSH 'A', OUT, HALT -> Emite 'A' (41343 pasos)
echo -ne "\x01\x41\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_m2_loader.mb

# Vector 2 M2: Carga en RAM y ejecución por PC de PUSH 'B', OUT, HALT -> Emite 'B' (41343 pasos)
echo -ne "\x01\x42\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_m2_loader.mb

# Vector 3 M2: HALT inmediato en carga -> Salida vacía (42062 pasos)
echo -ne "\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_m2_loader.mb
```

### 2. Verificar la ALU Unificada: ADD (0x02) y SUB (0x03)
Para ejecutar operaciones aritméticas individuales o secuencias complejas encadenadas en la misma imagen de VM en Malbolge puro:

```bash
# Suma: PUSH 2, PUSH 3, ADD, OUT, HALT -> Emite 0x05 (2 + 3 = 5)
echo -ne "\x01\x02\x01\x03\x02\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_alu.mb | xxd

# Resta: PUSH 4, PUSH 2, SUB, OUT, HALT -> Emite 0x02 (4 - 2 = 2)
echo -ne "\x01\x04\x01\x02\x03\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_alu.mb | xxd

# Expresión encadenada: (1 + 1) - 1 = 1
echo -ne "\x01\x01\x01\x01\x02\x01\x01\x03\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_alu.mb | xxd
```

### 3. Verificar el Kernel de Comparación: CMP_EQ (Hito P2)
Para evaluar igualdad booleana en Malbolge puro desapilando 2 operandos de la pila:

```bash
# Vector 1 P2: 2 == 2 -> Emite 0x01 (true)
echo -ne "\x01\x02\x01\x02\x02\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_p2_cmp.mb | xxd

# Vector 2 P2: 2 == 1 -> Emite 0x00 (false)
echo -ne "\x01\x02\x01\x01\x02\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_p2_cmp.mb | xxd

# Vector 4 P2: 4 == 2 -> Emite 0x00 (false)
echo -ne "\x01\x04\x01\x02\x02\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_p2_cmp.mb | xxd
```

### 4. Verificar la Pila LIFO de 2 Ranuras (Hito A05b)
Para verificar la inversión LIFO y desapilado frente al runner C real:

```bash
# Vector Clave A05b: PUSH 'A', PUSH 'B', OUT, OUT, HALT -> Emite "BA" (4241) en orden LIFO
echo -ne "\x01\x41\x01\x42\x10\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_a05_lifo.mb

# Vector A05b: PUSH 'A', PUSH 'B', OUT, HALT -> Emite "B" (42) del tope de la pila
echo -ne "\x01\x41\x01\x42\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_a05_lifo.mb
```

### 5. Verificar el Bucle Multi-Ciclo Reentrante (Hito A05)
```bash
# Vector Multi-Ciclo: PUSH 'A', OUT, PUSH 'B', OUT, HALT -> Emite "AB" (4142)
echo -ne "\x01\x41\x10\x01\x42\x10\x00" | ./runners/malbolge-original/malbolge vm_malbolge/src/mbir_a05_multicycle.mb
```

### 6. Ejecutar la Suite de Pruebas de MBIR
```bash
# Validar el encoder/decoder y conformidad de MBIR
python3 -m unittest discover -s mbir/tests

# Validar el oráculo en Zig nativo
./mbir/zig/zig-out/bin/mbir-zig --help
```

### 7. Verificar los frontends Python P3, P4 y P5 (host)
Cada compilador escribe de nuevo su JSON de evidencia. El harness cubre P1, P2, P3, P4 y P5.

```bash
python3 python/src/p3_compiler.py
python3 python/src/p4_compiler.py
python3 python/src/p5_compiler.py
python3 python/tests/test_harness.py
```

### 8. Verificar el Orden Relacional CMP_LT (Hito P2 relacional, 12/12)
El harness corre los 12 vectores (9 pares ordenados + 3 líneas base) en el oráculo Python **y** en el runner
nativo C, y compara salida y número de pasos. Tarda un minuto porque el oráculo es un intérprete en Python.

```bash
# Imagen canónica 12/12 (Finding 74). Sale 0 sólo si se alcanza 12/12.
python3 vm_malbolge/tests/lt_harness.py vm_malbolge/src/mbir_cmp_lt.mb

# Copia inmutable de evidencia (blob sha256 79160ecf906ce3a4…).
python3 vm_malbolge/tests/lt_harness.py vm_malbolge/evidence/artifacts/lt_pass12.mb

# Reconstruir desde el HeLL canónico (LMAO v0.6.0, modo normal con depuración). Los builds son
# byte-nodeterministas pero invariantes en comportamiento (Finding 62): el hash identifica una instancia.
./third_party/lmao/bin/lmao -d -o /tmp/imagen.mb vm_malbolge/src/mbir_cmp_lt.hell

# Imágenes históricas de la etapa 11/12 (cada una falla UNA sola entrada distinta): negativo conservado.
python3 vm_malbolge/tests/lt_harness.py vm_malbolge/evidence/artifacts/lt_f59_cand_C.mb
```

### 8b. Verificar el Orden Relacional CMP_GT (Hito P2 relacional inverso, 12/12)
Mismo contrato de harness: 9 pares ordenados + 3 líneas base, salida y número de pasos en los dos motores.

```bash
# Imagen canónica 12/12 (Finding 75).
python3 vm_malbolge/tests/gt_harness.py vm_malbolge/src/mbir_cmp_gt.mb

# Copia inmutable de evidencia (blob sha256 1f17062a9585beb…).
python3 vm_malbolge/tests/gt_harness.py vm_malbolge/evidence/artifacts/gt_pass12.mb

# Reconstruir desde el HeLL canónico (misma nota de no-determinismo de bytes).
./third_party/lmao/bin/lmao -d -o /tmp/gt.mb vm_malbolge/src/mbir_cmp_gt.hell
```

### 9. Verificar la Quine Clásica Récord (53,562 B)

La quine imprime su propio código fuente byte a byte; la verificación es un `cmp` entre la salida del runner y el archivo. El runner C de este repositorio añade un `0x0A` final de convención propia (igual que en los vectores M2), así que se comparan los primeros N bytes con `cmp -n`.

```bash
# Salida identica en los primeros 53,562 bytes (los pasos van en stderr: steps: 62239852 | status: HALTED)
./runners/malbolge-original/malbolge quine/quine_53562_m281.mb > /tmp/quine.out
cmp -n 53562 /tmp/quine.out quine/quine_53562_m281.mb   # 0 bytes de diferencia

# Escalera completa (m=287, 293, 308): mismo protocolo
for f in quine/ladder/*.mb; do
  ./runners/malbolge-original/malbolge "$f" > /tmp/out.mb 2>/tmp/steps.txt
  cmp -n "$(wc -c < "$f")" /tmp/out.mb "$f" && echo "$f OK"
done
```

La quine tarda ~22 minutos en el runner C de este repositorio (~63M pasos); el oráculo `mb_ref` de BolgeForge la resuelve en ~0.2 s con paridad byte a byte completa. Detalles, hashes y límites: [`quine/README.md`](quine/README.md).

Aviso de hashes (Hallazgo 62): las compilaciones de LMAO **no son deterministas en bytes** — seis builds
sucesivos del mismo `.hell` dan seis `.mb` con sha256 distinto y una única firma de comportamiento, porque la
cola `56904..57507` nunca es `pc` ni operando de lectura. La identidad canónica de una imagen es
`(sha256 del .hell, firma de los 12 vectores, sha256 de la instancia)`, no el sha del `.mb`. Además este
repositorio se maneja con `core.autocrlf=true`: para un artefacto commiteado hay que citar el hash del **blob**
(`git show HEAD:<ruta> | sha256sum`) junto al del fichero de trabajo.

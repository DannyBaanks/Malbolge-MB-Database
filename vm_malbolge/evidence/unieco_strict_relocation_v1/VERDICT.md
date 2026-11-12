# UNIECO estricto con relocalización — veredicto

**Fecha:** 2026-11-11. **Base del pack:** `35348ff` (compuesto `e42938d`).
**Alcance:** una única imagen Malbolge que el cargador histórico de Olmstead
acepta, que instala un eco binario y que se detiene en EOF sin bytes extra.

## Veredicto en una línea

La **relocalización** del bucle compacto funciona y su eco binario es exacto
(G0, G1, G2 verdes), pero **la variante relocalizada no tiene detección de EOF**:
G3 queda `NOT_DEMONSTRATED` y el ciclo medido en EOF emite `0xa8` con periodo
180. En paralelo, el **requisito funcional** de UNIECO (imagen única, cargador de
1998, eco binario, halt limpio en EOF sin bytes extra) **queda demostrado** sobre
una imagen de referencia construida en otro pack. Son dos construcciones
distintas y no se afirma ninguna composición entre ellas.

| Puerta | Estado | Evidencia |
|---|---|---|
| G0 — imagen estricta aceptada por el cargador real | PASS | `candidate.mb`, `verify_echo.results.json` |
| G1 — instalación única, sin IN/OUT previos | PASS | `verify_echo.results.json` |
| G2 — eco de 10 000 bytes, multi-motor | PASS | `verify_echo.results.json` (`all_checks: true`) |
| G3 — halt limpio en EOF bajo Olmstead | **NOT_DEMONSTRATED** | `eof_cycle.results.json`, `crazy_algebra.results.json`, `budget_bound.results.json` |
| G4 — controles negativos y semántica EOF explícita | PARTIAL | `ctrl_writer_*.mb`, `reference_functional.results.json` |

## Dos construcciones, deliberadamente separadas

La imagen candidata es el **bucle compacto de 150 celdas** (`epoch_dload_inout_v1/compose_inout.mb`)
instalado en memoria alta por el planificador de BolgeForge: 4 039 ops de plan
para 87 celdas destino, desplazamiento 58 656 (= 94·624, conserva `(v+c)%94`).

La imagen de referencia funcional es `reference_cat_functional.mb`: 7 972 celdas
de `Malbolge-PureEpoch/candidates/cat_real.mal`, copiada desde
`vm_malbolge/evidence/inout_loader_eof_v1/`. **No** es el bucle compacto, **no**
fue construida en este pack y **no** hay composición de código demostrada entre
ella y `candidate.mb`. Sirve para separar "el programa puede existir" de
"esta relocalización particular lo consigue".

## G3: por qué esta relocalización no se detiene en EOF

En EOF el `IN` devuelve 59 048 (`2222222222_3`) y el bucle sigue iterando: el
modelo de memoria muestra un **ciclo de periodo 180** a partir del paso 4 123,
y en 181 pasos emite 181 bytes `0xa8` (`59048 % 256`), uno por vuelta. El eco
correcto termina; el bucle no.

La rama EOF necesita convertir el acumulador (el byte) en un destino de salto
distinto para EOF. La única fuente de ese cálculo es `CRAZY`, y `CRAZY` escribe
en la celda de la que lee su fila. Eso fija la forma del obstáculo, medido en
`crazy_algebra.results.json` (paridad previa con el motor: 4 000 muestras, 0
discrepancias; orientación fila = trit de celda, columna = trit de A):

1. **Ninguna fila es constante.** Imágenes de `R_0`, `R_1`, `R_2`: `{0,1}`,
   `{0,1,2}`, `{1,2}`. Por tanto un único `CRAZY` no puede producir un destino
   independiente del byte: la fila lee el byte y la fila no es constante.
2. **Las composiciones constantes son sólo dos.** A longitud 2: `R_0∘R_2 → 0` y
   `R_2∘R_0 → 2` (orden de aplicación: la primera de la lista se aplica antes).
   A longitud 3 hay 11 composiciones constantes, con constantes 0, 1 o 2 por
   posición. Pero una función constante sobre `{0,1,2}` **también** lo es sobre
   el trit 2 de EOF: colapsar un trit borra la distinción EOF en ese trit.
3. **La distinción EOF sólo vive en los trits 6..9.** Un byte < 256 tiene
   trits 6..9 = 0 y trit 5 ∈ {0,1}; EOF = 59 048 tiene los diez trits = 2. Los
   trits 0..4 del byte son libres.
4. **La cadena candidata no es estable en un bucle.** La cadena de colapso de
   tres pasos `CRAZY(b;A=0) ; CRAZY(a;B=C2) ; CRAZY(a;C=M3)` da la constante
   59 048 en la **ronda 1** (correcto) y a partir de la ronda 2 la máscara de A
   es `R_0(byte)` —cuyo valor ya no tiene imagen `{0,1}`—, el colapso `R_2` deja
   de colapsar y la salida **oscila** entre 59 048 y 29 524 en el flujo medido
   `[0x41, 0x42, 0x43, 0x44]`. La razón es estructural: la máscara de la vuelta
   n+1 es la salida de la vuelta n, de modo que la composición efectiva depende
   del historial.

De aquí se sigue que una rama EOF estable dentro de un bucle exige una de estas
dos vías, y ninguna es la que cabe hoy:

- **Rearmar las máscaras cada vuelta** (el idioma de LMAO: `crazy` dos veces
  para devolver la celda a `C1 = 29524`, que es involutiva:
  `crazy(crazy(V,29524),29524) = V`, verificado). Coste medido de la
  referencia equivalente: **20 776 celdas**.
- **Despachar por tabla** sobre un índice que cubra todos los estados
  alcanzables. Con el byte exacto como índice, la tabla son 256 celdas, pero
  obtener el byte exacto en una celda exige precisamente la máscara `C1` y su
  rearmado: el coste no se escapa de la vía anterior.

## El techo medido de la relocalización

`budget_bound.results.json`, con los números medidos del plan:

- Coste del planificador: **46,4253 ops por celda destino** (4 039 ops / 87
  celdas).
- Región de plan actual: 94·200 = 18 800 ops → **404 celdas destino**.
- Región máxima admisible antes de invadir el destino (`source_len ≤ 58 697`):
  49 214 ops → **1 060 celdas destino**.
- Referencias con detección de EOF que existen y funcionan: PureEpoch
  `cat_real` = **7 972 celdas** (7,52× por encima del techo máximo) y el
  ejemplo LMAO `example_cat_halt_on_eof` = **20 776 celdas** (19,6×).
- Una tabla de despacho de 256 entradas costaría 11 884 ops: cabe en la región
  actual, pero deja sólo 148 celdas para el cuerpo y exige el rearmado.

Conclusión operativa: **una variante relocalizada con halt en EOF necesita un
cuerpo nuevo de como máximo 1 060 celdas destino** (≤ 404 con la región de plan
actual), es decir, entre 7,5× y 19,6× más pequeño que las dos referencias
medidas. No existe hoy en el repo tal cuerpo; no se afirma que no pueda existir.

## Requisito funcional de UNIECO (imagen de referencia)

`reference_functional.results.json`, 6 motores × 5 entradas + 2 controles:

- Imagen de 7 972 bytes, **0 celdas inválidas** para el cargador de 1998
  (`(v+i)%94 ∈ {4,5,23,39,40,62,68,81}`), SHA-256
  `0d298645bcabd8c832c6bbad0769124828a8805bb46cc4644e35added50334f1`.
- **Olmstead**: eco exacto byte a byte y salida vacía para entrada vacía, en
  los cinco casos (vacío, `00`, `00 0a 80 ff`, `00..ff`, 10 000 bytes
  `(73i+195)%256`).
- **Runner C**: mismo contenido con su framing de un `\n` final añadido por el
  runner; estado `HALTED`.
- **Scratch, intérprete independiente, oráculo por defecto y oráculo con
  `stop_on_eof`**: mismo eco exacto. Diferencia semántica de EOF documentada:
  el intérprete independiente y el oráculo con `stop_on_eof` terminan con
  estado `EOF` (parada del host), el oráculo por defecto y el scratch terminan
  con `HALTED` (la imagen se detiene por sí misma).
- **Control 1 — cargador**: con la primera celda alterada a una no válida, el
  cargador **rechaza** con `rc = 1` y 0 bytes de salida.
- **Control 2 — ruta de EOF rota**: la variante `reference_cat_bad_eof.mb`
  (SHA-256 `8aad30cc…`) muere con `rc = -11` (SIGSEGV): una ruta de EOF
  defectuosa **no** se confunde con un halt limpio.

## Semántica de EOF entre motores (G4, nota)

El `IN` de EOF devuelve 59 048 en todos los motores; lo que difiere es quién
decide parar. Bajo Olmstead (el runner histórico) la imagen debe detenerse por
sí misma: es exactamente lo que falla en `candidate.mb` y lo que cumple la
imagen de referencia. Bajo los otros motores, parte de la parada la impone el
host (`stop_on_eof`), lo que no puede usarse como prueba de G3.

## NOT_DEMONSTRATED

- Que la variante relocalizada `candidate.mb` se detenga en EOF. G3 abierto.
- El mínimo de celdas de un cuerpo con detección de EOF: sólo hay dos
  mediciones (7 972 y 20 776), ambas por encima del techo.
- Que exista un cuerpo con detección de EOF por debajo de 1 060 celdas destino.
- Que el planificador pueda sintetizar una tabla de despacho de 256 entradas:
  sólo se midió su coste en ops, no su síntesis.
- Composición de código entre `candidate.mb` y la imagen de referencia.

## Reproducibilidad

`reproduce_check.json`: `verify_echo.py` se re-ejecutó en una **copia del pack
fuera del repositorio** (con enlaces simbólicos al resto del árbol) para no
reescribir la evidencia almacenada. Los 37 campos deterministas comparados
(traza, pasos, rondas, destinos de salto, hashes de memoria de los tres
motores, salida del runner, control mutante, `checks`) son **idénticos**, y la
captura acotada del proceso Olmstead coincide también (12 288 bytes, mismos 16
primeros bytes post-EOF `a8…`, mismo código de retorno `-15` por terminación
del arnés). La verificación de las puertas es reproducible.

## Reproducción

```bash
cd <repo MALBOLGE-MB-DATABASE>        # raiz del repo hermano
python3 vm_malbolge/evidence/unieco_strict_relocation_v1/crazy_algebra.py
python3 vm_malbolge/evidence/unieco_strict_relocation_v1/budget_bound.py
python3 vm_malbolge/evidence/unieco_strict_relocation_v1/reference_functional.py
python3 vm_malbolge/evidence/unieco_strict_relocation_v1/make_manifest.py
```

Salidas crudas en `raw/` y en los ficheros `*.stdout.raw.txt`; hashes de todo
el pack en `manifest.json`.

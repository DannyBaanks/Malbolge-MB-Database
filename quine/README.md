# Quine Clásica de 54,134 Bytes (m=284) — BolgeForge

**Récord del ecosistema (2026-10-16):** una quine Malbolge **clásica** que imprime su propio
código fuente byte a byte, de **54,134 bytes** — **5,718 bytes menos** que la quine de referencia
de Matthias Lutter (59,852 B), usada como línea base de este trabajo.

> **Alcance del claim (anti-fake):** es la quine más pequeña *producida y verificada por este
> ecosistema*. No se ha hecho un barrido externo exhaustivo de todas las quines clásicas
> publicadas; la comparación establecida es contra la referencia Lutter (59,852 B) y la escalera
> propia documentada abajo. `KNOWN_LIMIT` explícito al final de este documento.

---

## Artefacto

| Campo | Valor |
|---|---|
| Archivo | [`quine_54134_m284.mb`](quine_54134_m284.mb) |
| Tamaño | 54,134 bytes (53,392 caracteres de programa + 742 bytes `0x0A` que la quine emite como parte de su fuente) |
| SHA-256 | `1808fd4d862a274abc6b9f7b8965d1eee65fc11aa2424c23a8077040876b483c` |
| Parámetro | m=284 (ext-v2; stream sintetizado de 22,630 opcodes, margen 2,126 bajo el límite `94m−3`) |
| Sintetizador | **BolgeForge** `synthesize_v2.py` (ver Procedencia) |
| Dialecto | Classic (3^10 = 59,049 celdas), char set 33..126, whitespace ignorado por el cargador |

### Verificación en este repositorio (doble motor C independiente)

```bash
# Motor 1: runner C de este repositorio (malbolge-original)
./runners/malbolge-original/malbolge quine/quine_54134_m284.mb > /tmp/quine.out
cmp -n 54134 /tmp/quine.out quine/quine_54134_m284.mb    # 0 bytes de diferencia
# El runner añade 1 byte 0x0A propio al final (byte 54,135); los pasos van en stderr:
#   steps: 62902924 | status: HALTED   (~22 min de pared)

# Motor 2: oráculo mb_ref de BolgeForge (implementación C independiente)
#   ./mb_ref quine_54134_m284.mb > /tmp/mbref.out   →  0-byte diff completo, exit 0 (~0.2 s)
```

| Motor | Fecha | Resultado | Detalle |
|---|---|---|---|
| `runners/malbolge-original/malbolge` (este repo) | 2026-10-16 | **idéntica en los primeros 54,134 bytes** | `steps: 62902924 | HALTED`, 1,332 s de pared; añade `0x0A` final de convención propia (byte 54,135). Evidencia completa en [`evidence/quine_54134_verification.json`](evidence/quine_54134_verification.json) |
| `mb_ref` (BolgeForge, C) | 2026-10-16 | **byte-idéntica completa**, exit 0 | ~0.18 s de pared; ≈62.9M pasos (Δ1 en el conteo vs el runner del repo, por convención del paso de HALT) |

Ambos motores son implementaciones C **independientes** del dialecto Classic (semántica de
Ben Olmstead; whitespace saltado en carga). `mb_ref` reproduce la salida íntegra —incluidos los
742 `\n`— byte a byte; el runner del repositorio coincide en los primeros 54,134 bytes y añade
su `0x0A` final de convención.

## Escalera verificada (las cuatro re-verificadas el 2026-10-16, 0 bytes de diferencia)

| m | Archivo | Bytes | Δ vs Lutter (59,852) | SHA-256 |
|---|---|---|---|---|
| **284** | [`quine_54134_m284.mb`](quine_54134_m284.mb) **(récord)** | **54,134** | **−5,718** | `1808fd4d862a274abc6b9f7b8965d1eee65fc11aa2424c23a8077040876b483c` |
| 287 | [`ladder/quine_54706_m287.mb`](ladder/quine_54706_m287.mb) | 54,706 | −5,146 | `3da997b9e559230d43acf828188269d441afc03d773e71a83f49ae7e9d663efb` |
| 293 | [`ladder/quine_55850_m293.mb`](ladder/quine_55850_m293.mb) | 55,850 | −4,002 | `1719515d85fa2d5dfc0c36cdcc935eefd363fca0a435b2588ef36a1509b1b2ea` |
| 308 | [`ladder/quine_58709_m308.mb`](ladder/quine_58709_m308.mb) | 58,709 | −1,143 | `67628cf1cd8befe907c39aac6476d31927499f0421013c34195891f2ec4ca071` |

```bash
# Verificar la escalera completa (mismo protocolo, ~22 min por corrida en el runner C):
for f in quine/ladder/*.mb; do
  ./runners/malbolge-original/malbolge "$f" > /tmp/out.mb 2>/tmp/steps.txt
  cmp -n "$(wc -c < "$f")" /tmp/out.mb "$f" && echo "$f OK"
done
```

Nota histórica: `NOTES.md` de BolgeForge registra un sha `2fbdfb82…` para un build anterior de
m=308 (pre-corrección de tabla de edges); el artefacto adoptado y verificado aquí es el de la
tabla (`67628cf1…`).

## Procedencia: BolgeForge

La quine fue sintetizada por **BolgeForge**, el subsistema de síntesis del monorepo ISyCo:

- `REPO` (monorepo ISyCo, privado, fuera de este repositorio): `workspace/assembly/malbolge/bolge_forge/`
- Corrida activa: `…/bolge_forge/artifacts/quine_experiment/m299_resynthesis/`
- `SINTETIZADOR`: `synthesize_v2.py` — sha256 `f94cf10c0f0353010e324831f7be3342aa24750c40f020dd318c23fb9de7bd4c`
- `BITÁCORA`: `NOTES.md` (síntesis, triage de m, hallazgos de capacidad y correcciones)
- Espejo publicado (este repositorio): `quine/` con artefacto, escalera y evidencia JSON

Mecánica del sintetizador (resumen técnico):

- **Grafo de 26 edges**: cada edge es una macro de auto-modificación verificada *pura* bajo todo
  estado de entrada de A (p. ej. edge 6 = `*jopjo`, `x → crazy(rot x, rot x)`), encadenadas por
  Dijkstra para escribir cada celda del preámbulo.
- **Generador analítico de constantes**: carga de A por trits vía la mecánica rot/crazy del
  módulo 0 (medido: media 19.3 ops/constante; no siempre gana al Dijkstra).
- **Búsqueda runtime de macro `inc`**: primero candidatos duros, luego BFS acotado
  (profundidad ≤ 24, 150k nodos, alfabeto `o j * p`) con el A real del punto de uso.
- **Correcciones**: reordenamiento de `EDGES[19..21]` (tablas de crazy mal alineadas);
  reconstrucción ext-v2 de m=284 (stream 24,024 → 22,630 opcodes).

## Cómo está construida (mapa técnico breve)

Arquitectura de la línea Lutter (heredada y medida por BolgeForge):

- **C = 94·m celdas por mitad** (m=284 → 26,696 celdas): la fuente es una escalera de patrones
  de 94 caracteres que el cargador convierte en una tabla de operaciones auto-replicante.
- El **loop de impresión** rota cada celda por `xlat2` (`mem[c] = xlat2[mem[c]−33]`) y emite el
  byte resultante con `<`, regenerando la fuente mientras la imprime.
- Los **writes** (`p`) se rutean por una *landing table* (celdas 45..138) que devuelve a la
  celda 140 (módulo 0); el registro `DESTINATION` (celda 148) avanza +9 por grupo de 9 celdas
  vía máscaras de acarreo (celdas 142..146).
- **Regla de validez del prefijo**: `m ≡ 2 (mod 3)` en [161, 314] (celdas ≥ 2C toman la
  inicialización nativa; el prefijo Lutter las lee).
- **Capacidad**: preámbulo `c ≤ 94m − 3`; el stream sintetizado que cabe es cuasi-aleatorio
  según el layout (~24k–27k opcodes típicos), por eso descendió m=284 y no m=278.

## Contexto de investigación: REVERSE_SELF_MODIFICATION (B0/B1)

En paralelo a la escalera, se analizó *por qué* estas quines funcionan midiendo su
auto-modificación real (todo en `…/quine_experiment/REVERSE_SELF_MODIFICATION/`):

- **B0 — ley X (traza del récord)**: 24,090 celdas ejecutadas; **24,009/24,090** terminan en
  `final == X^k(init)` con **X = xlat2** (permutación de 6 ciclos {2,4,5,6,9,68}, LCM 3,060);
  las 79 excepciones son exactamente las celdas tocadas por `*`/`p` (datos). Trabajadores:
  24,028 celdas ejecutadas una sola vez; la tabla de aterrizaje (12 celdas) acumula 8.5M
  ejecuciones. Evidencia: `traces/m284_state.txt` (sha256 `1f233923…`).
- **B1 — byte imposible**: el campeón de 44 bytes `hit_strong_000633.mal` imprime **0xFD (253)**
  — un byte que no puede aparecer en una fuente Classic válida — mediante una única
  auto-modificación `X` seguida de `crazy` sobre la constante transformada.
  sha256 `f0f420916618cb595fb6b1622ef34cd9da4dc9e6688eebeaa68b16d8c2d2b8db`,
  salida sha256 `3e151409ace91cb3394fecd59e92b5dc42c0aad29993a1858f2f70a0866a539b` (198 pasos,
  SIM == REF). Corpus: 803 candidatos verificados → 314 con bytes imposibles.
- Veredicto de esa fase: **H1 parcialmente respaldada a escala mínima**; el costo a escala de
  quine completa (FASE C) y la autorreproducción (FASE D) quedaron **`NOT_DEMONSTRATED`** por
  decisión de cierre.

## Integridad de los artefactos (hashes y autocrlf)

Este repositorio usa `core.autocrlf=true`; los `.mb` de `quine/` están marcados como `binary`
en [`.gitattributes`](../.gitattributes) para que el archivo de trabajo sea siempre idéntico al
blob (los 742 `\n` de la quine son parte de su salida canónica). Para citar el hash canónico:

```bash
git show HEAD:quine/quine_54134_m284.mb | sha256sum   # = 1808fd4d…
sha256sum quine/quine_54134_m284.mb                   # idéntico en cualquier checkout
```

Contexto del ecosistema (traza B0 y contraste de motores):

| Qué | Motor A (BolgeForge) | Motor B (este repo) |
|---|---|---|
| Ejecución Classic de 63M pasos | `mb_ref` (~0.2 s) | `runners/malbolge-original/malbolge` (~22 min) |
| Paridad de salida | byte-idéntica completa | idéntica en los primeros 54,134 bytes (+`0x0A` de convención del runner) |

## Límites (KNOWN_LIMIT / NOT_DEMONSTRATED)

- El claim de récord es **acotado**: menor que la referencia Lutter y la escalera propia; no se
  hizo un barrido externo exhaustivo de todas las quines clásicas publicadas.
- **Descenso por debajo de m=284**: `NOT_DEMONSTRATED`. El piso del stream sintetizado
  (~26.5k opcodes en draws típicos) excede los límites de capacidad de m≤281 con el grafo
  actual; los caminos de rescate están en `NOTES.md` §Next steps (DP/beam de selección X,
  edges fase-2, fallback reset-write de celda 148, ataque a los walks de ~10.7k ops).
- La quine no lee stdin; su contrato es imprimir su fuente y haltear.
- El espejo de este repositorio es de solo-lectura documental (regla L0: a repos no activos
  solo documentación semántica mínima); la fuente activa vive en el monorepo ISyCo.

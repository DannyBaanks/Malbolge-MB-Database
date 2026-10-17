# Quine Clásica de 53,562 Bytes (m=281) — BolgeForge

**Récord del ecosistema (2026-10-17):** una quine Malbolge **clásica** que imprime su propio
código fuente byte a byte, de **53,562 bytes** — **6,290 bytes menos** que la quine de referencia
de Matthias Lutter (59,852 B), usada como línea base de este trabajo. Supera al récord anterior
del mismo ecosistema (m=284, 54,134 B, 2026-10-16) por **572 bytes**.

> **Alcance del claim (anti-fake):** es la quine más pequeña *producida y verificada por este
> ecosistema*. No se ha hecho un barrido externo exhaustivo de todas las quines clásicas
> publicadas; la comparación establecida es contra la referencia Lutter (59,852 B) y la escalera
> propia documentada abajo. `KNOWN_LIMIT` explícito al final de este documento.

---

## Artefacto

| Campo | Valor |
|---|---|
| Archivo | [`quine_53562_m281.mb`](quine_53562_m281.mb) |
| Tamaño | 53,562 bytes (52,828 caracteres de programa + 734 bytes `0x0A` que la quine emite como parte de su fuente) |
| SHA-256 | `96b670b825372a0f41fa3b574d47457f92654b76411e5d5be4c438003087610e` |
| Parámetro | m=281 (ext-v2; stream sintetizado de 24,094 opcodes; margen 380 antes del loop slice sobre la capacidad 25,947 = `94m−467`; fallback composite `inc` ×1, 68 ops) |
| Sintetizador | **BolgeForge** `synthesize_v2.py` (ver Procedencia) |
| Dialecto | Classic (3^10 = 59,049 celdas), char set 33..126, whitespace ignorado por el cargador |

### Verificación en este repositorio (tres motores C independientes)

```bash
# Motor 1: runner C de este repositorio (malbolge-original)
./runners/malbolge-original/malbolge quine/quine_53562_m281.mb > /tmp/quine.out
cmp -n 53562 /tmp/quine.out quine/quine_53562_m281.mb    # 0 bytes de diferencia
# El runner añade 1 byte 0x0A propio al final (byte 53,563); los pasos van en stderr:
#   steps: 62239852 | status: HALTED   (~22 min de pared)

# Motor 2: oráculo mb_ref de BolgeForge (implementación C independiente)
#   ./mb_ref quine_53562_m281.mb > /tmp/mbref.out   →  0-byte diff completo, exit 0 (~0.15 s)

# Motor 3 (ruta rápida reproducible, sin depender de mb_ref ni del runner de 22 min):
gcc -O2 -o /tmp/mb quine/evidence/mb_classic_indep.c
/tmp/mb quine/quine_53562_m281.mb | cmp - quine/quine_53562_m281.mb   # 0 bytes de diferencia (~0.25 s)
```

| Motor | Fecha | Resultado | Detalle |
|---|---|---|---|
| `runners/malbolge-original/malbolge` (este repo) | 2026-10-17 | **idéntica en los primeros 53,562 bytes** | `steps: 62239852 | HALTED`, 1,323 s de pared; añade `0x0A` final de convención propia (byte 53,563). Evidencia completa en [`evidence/quine_53562_verification.json`](evidence/quine_53562_verification.json) |
| `mb_ref` (BolgeForge, C) | 2026-10-17 | **byte-idéntica completa**, exit 0 | ~0.15 s de pared; 62,239,847 pasos hasta la última emisión (5 pasos más hasta HALT, no observables vía salida/rc) |
| [`evidence/mb_classic_indep.c`](evidence/mb_classic_indep.c) (auditoría externa) | 2026-10-17 | **byte-idéntica completa**, exit 0 | 253 ms de pared; 62,239,852 pasos, `HALTED`; calibrado contra `tools/fixtures/hello_world_40.mb` (40 pasos). Escrito desde la especificación, sin código del runner ni de `mb_ref` |

Los tres motores son implementaciones C **independientes** del dialecto Classic (semántica de
Ben Olmstead; whitespace saltado en carga). `mb_ref` y el oráculo de auditoría reproducen la
salida íntegra —incluidos los 734 `\n`— byte a byte; el runner del repositorio coincide en los
primeros 53,562 bytes y añade su `0x0A` final de convención. El hueco de 5 pasos entre la última
emisión (62,239,847) y el `HALT` (62,239,852) explica la diferencia de conteo entre motores.

La línea base **también se mide**: la quine de Lutter descargada de `lutter.cc/malbolge/quine.mal`
es de 59,852 B (sha256 `dca8476f…`, m=314, 820 `\n`) y el oráculo la reproduce byte a byte. De los
6,290 B de ventaja, **6,204 son programa** (33 bloques de 2×94 al bajar m de 314 a 281) y 86 son
saltos de línea: el 98.6% de la ganancia es estructural, no de formato.

## Escalera verificada (0 bytes de diferencia; récord vigente con triple motor el 2026-10-17)

| m | Archivo | Bytes | Δ vs Lutter (59,852) | SHA-256 |
|---|---|---|---|---|
| **281** | [`quine_53562_m281.mb`](quine_53562_m281.mb) **(récord)** | **53,562** | **−6,290** | `96b670b825372a0f41fa3b574d47457f92654b76411e5d5be4c438003087610e` |
| 284 | [`quine_54134_m284.mb`](quine_54134_m284.mb) (récord anterior) | 54,134 | −5,718 | `1808fd4d862a274abc6b9f7b8965d1eee65fc11aa2424c23a8077040876b483c` |
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
- Herramienta pública: [BolgeForge](https://github.com/DannyBaanks/BolgeForge) — sintetizador
  portable v3.1 (sha256 `e401dec1…`, `python3 synthesize.py <m>`), oráculo `mb_ref` y récord +
  escalera commiteados; la CI reproduce el récord byte a byte. Regresión del port: m=281 →
  `96b670b8…`, m=284 → `1808fd4d…` (byte-exacta, 2026-10-17).
- Corrida activa: `…/bolge_forge/artifacts/quine_experiment/m299_resynthesis/`
- `SINTETIZADOR`: `synthesize_v2.py` — sha256 `56088d2c49f1c8311db563a918beeffe0d4323a43dd490991e3b2d155c16056b` (versión 2026-10-17 con fallback composite; la anterior, `f94cf10c…`, construyó m=284/287/293/308)
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
- **Fallback composite de `inc`** (2026-10-17): donde no existe preimagen de 1 escritura
  (valores muertos con acarreo en trit 2), dos escrituras seed-style garantizadas
  `V → W → V+9` (`W` = trits del acarreo a 1; X1/X2 con `solve_crazy_first`; dance
  `'ojoooooo'` + Dijkstra + `'ooojopj'`). Sólo se activa donde la versión anterior fallaba;
  en m=281 se usó 1 vez (68 ops) y desbloqueó el récord.
- **Correcciones**: reordenamiento de `EDGES[19..21]` (tablas de crazy mal alineadas);
  reconstrucción ext-v2 de m=284 (stream 24,024 → 22,630 opcodes).

## Cómo está construida (mapa técnico breve)

Arquitectura de la línea Lutter (heredada y medida por BolgeForge):

- **C = 94·m celdas por mitad** (m=281 → 26,414 celdas): la fuente es una escalera de patrones
  de 94 caracteres que el cargador convierte en una tabla de operaciones auto-replicante.
- El **loop de impresión** rota cada celda por `xlat2` (`mem[c] = xlat2[mem[c]−33]`) y emite el
  byte resultante con `<`, regenerando la fuente mientras la imprime.
- Los **writes** (`p`) se rutean por una *landing table* (celdas 45..138) que devuelve a la
  celda 140 (módulo 0); el registro `DESTINATION` (celda 148) avanza +9 por grupo de 9 celdas
  vía máscaras de acarreo (celdas 142..146).
- **Regla de validez del prefijo**: `m ≡ 2 (mod 3)` en [161, 314] (celdas ≥ 2C toman la
  inicialización nativa; el prefijo Lutter las lee).
- **Capacidad**: preámbulo `c ≤ 94m − 3`; el stream sintetizado que cabe es cuasi-aleatorio
  según el layout (~24k–27k opcodes típicos), por eso el récord descendió hasta m=281
  (stream 24,094, margen 380) pero no m=278 (bloqueado por el piso del stream).

## Contexto de investigación: REVERSE_SELF_MODIFICATION (B0/B1)

En paralelo a la escalera, se analizó *por qué* estas quines funcionan midiendo su
auto-modificación real (todo en `…/quine_experiment/REVERSE_SELF_MODIFICATION/`):

- **B0 — ley X (traza del build m=284, récord en esa fecha)**: 24,090 celdas ejecutadas;
  **24,009/24,090** terminan en `final == X^k(init)` con **X = xlat2** (permutación de 6 ciclos
  {2,4,5,6,9,68}, LCM 3,060); las 79 excepciones son exactamente las celdas tocadas por `*`/`p`
  (datos). Trabajadores: 24,028 celdas ejecutadas una sola vez; la tabla de aterrizaje (12
  celdas) acumula 8.5M ejecuciones. Evidencia: `traces/m284_state.txt` (sha256 `1f233923…`).
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
blob (los 734 `\n` de la quine vigente son parte de su salida canónica). Para citar el hash canónico:

```bash
git show HEAD:quine/quine_53562_m281.mb | sha256sum   # = 96b670b8…
sha256sum quine/quine_53562_m281.mb                   # idéntico en cualquier checkout
```

Contexto del ecosistema (traza B0 y contraste de motores):

| Qué | Motor A (BolgeForge) | Motor B (este repo) |
|---|---|---|
| Ejecución Classic de 62M pasos | `mb_ref` (~0.15 s) | `runners/malbolge-original/malbolge` (~22 min) |
| Paridad de salida | byte-idéntica completa | idéntica en los primeros 53,562 bytes (+`0x0A` de convención del runner) |

## Barrido de quines publicadas (universo declarado)

Ver [`SWEEP_QUINES.md`](SWEEP_QUINES.md): barrido sistemático sobre **25 fuentes** (esolangs,
malbolge.org, lutter.cc, Rosetta Code, Code Golf SE, Hacker News, archive.org, Wayback, GitHub
code/repo search, archivos de la comunidad, y los **289 meses completos de logs IRC** de
`#esoteric`/`#esolangs` de 2002 a 2026). Resultado: solo existen **dos** quines Classic
publicadas, ambas de Matthias Lutter, y ambas son **mayores** que la de este repositorio en las
convenciones de conteo posibles:

| Artefacto | Bytes totales | Bytes programa | ¿Menor que este repo? |
|---|---|---|---|
| `quine-2012.mal` (Lutter) | 59,032 | 59,032 | no (−5,470 / −6,204) |
| `quine.mal` (Lutter) | 59,852 | 59,032 | no (−6,290 / −6,204) |

Ninguna de las 25 fuentes contiene una quine Classic menor, y en 24 años de logs del canal de la
comunidad nadie publicó ni anunció una alternativa (solo 23 líneas mencionan `quine` junto a
Malbolge, ninguna con un artefacto nuevo). Lo que **sigue sin cubrir** es la lista de correo
histórica `lang@esoteric.sange.fi`, cuyo archivo no es navegable hoy: la afirmación respaldada es
"no existe una menor en estas 25 fuentes", no "no existe en internet".

## Límites (KNOWN_LIMIT / NOT_DEMONSTRATED)

- El claim de récord es **acotado**: menor que la referencia Lutter y la escalera propia; no se
  hizo un barrido externo exhaustivo de todas las quines clásicas publicadas.
- **Descenso por debajo de m=284**: `DEMONSTRATED` hasta **m=281** el 2026-10-17 mediante el
  fallback composite de la macro `inc` (valores muertos sin preimagen de una escritura).
- **Descenso por debajo de m=281**: `NOT_DEMONSTRATED`. m=278 sigue bloqueado por el piso del
  stream sintetizado (~26.5k opcodes en draws típicos) y el DP de cadena por sí solo no basta
  (ahorro medido 108 ops vs ~2,321 necesarios). Palancas restantes en `NOTES.md` §Next steps
  (edges fase-2, ataque a los walks de ~10.7k ops, write predictivo).
- La quine no lee stdin; su contrato es imprimir su fuente y haltear.
- El espejo de este repositorio es de solo-lectura documental (regla L0: a repos no activos
  solo documentación semántica mínima); la fuente activa vive en el monorepo ISyCo.

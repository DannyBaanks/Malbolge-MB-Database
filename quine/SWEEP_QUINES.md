# Barrido de quines Malbolge publicadas — universo declarado (2026-10-17)

Auditoría de `autoclaw_danny_20261017`, independiente de los motores que produjeron el
artefacto. Objetivo: buscar quines **Malbolge Classic** publicadas **más pequeñas** que la de
este repositorio (`quine/quine_53562_m281.mb`, 53,562 B).

**Resultado: no se encontró ninguna.** Las únicas dos quines Classic publicadas que existen
(59,852 B y 59,032 B, ambas de Matthias Lutter) son mayores que la de este repositorio, en las
dos convenciones de conteo posibles.

> **"Exhaustivo" tiene un límite honesto y aquí está escrito.** Esto es un barrido *sistemático
> con universo enumerado*: cada fuente consultada está listada abajo, cada candidata encontrada
> fue descargada y ejecutada, y lo que quedó fuera está en §5. No es una prueba de que no exista
> una quine menor en algún rincón no indexado — es una prueba de que no existe en las N fuentes
> enumeradas, que es la única forma verificable de decirlo.

---

## 1. Método

Para cada candidata:

1. **Descarga** del artefacto original (no de un paste ni de una captura).
2. **Ejecución** en el oráculo independiente [`evidence/mb_classic_indep.c`](evidence/mb_classic_indep.c)
   (Classic 3^10, escrito desde la especificación; calibrado contra `tools/fixtures/hello_world_40.mb`).
3. **Autorreproducción**: `cmp` entre la salida y el propio archivo. Cero bytes de diferencia ⇒
   es una quine de verdad. Cualquier otra cosa ⇒ no lo es.
4. **Conteo en dos convenciones**, porque el número cambia según se cuenten los saltos de línea:
   - **bytes totales** (lo que ocupa el archivo en disco)
   - **bytes de programa** (solo caracteres 33..126; el cargador ignora whitespace)

La doble convención importa: se podría "ganar" el récord recortando saltos de línea sin cambiar
el programa. Por eso la comparación se hace con ambas cifras.

## 2. Universo consultado (N = 22 fuentes)

| # | Fuente | Qué se miró | Resultado |
|---|---|---|---|
| 1 | `esolangs.org/wiki/Malbolge` | artículo completo + enlaces externos | solo enlaza la quine de Lutter |
| 2 | `esolangs.org/wiki/Malbolge_Unshackled` | artículo completo | sin quine (enlace muerto en `List_of_quines`) |
| 3 | `esolangs.org/wiki/List_of_quines` | sección Malbolge + Unshackled | **2 enlaces**, ambos a la misma familia Lutter/Ernst |
| 4 | `esolangs.org/wiki/Talk:Malbolge` | página de discusión completa | sin quines; solo papers de Iizawa |
| 5 | `esolangs.org` search API (`malbolge`) | 7 páginas: Reborn, Compressed, Random, programming… | ninguna menciona quine |
| 6 | `malbolge.org` (hub oficial) | índice completo de programas | lista **una** quine |
| 7 | `malbolge.org/quine.mal` | descarga directa | 59,852 B — **verificada quine** |
| 8 | `malbolge.org/quine-2012.mal` | descarga directa (versión original) | 59,032 B — **verificada quine** |
| 9 | `lutter.cc/malbolge/quine.html` | página + descarga | idéntica a #7 (mismo sha256) |
| 10 | `matthias-ernst.eu/malbolgequine.html` | redirige a `malbolge.org` | mismo artefacto que #7 |
| 11 | Wayback Machine (3 snapshots digest, 2020/2023/2026) | ¿hubo versiones históricas más cortas? | siempre las mismas 2 (`quine.mal`, `quine-2012.mal`) |
| 12 | `rosettacode.org/wiki/Quine` + `/Quine/Malbolge` | tarea Quine | página Malbolge **no existe** (404) |
| 13 | Code Golf SE (tag `malbolge`) | 1 pregunta, 30 excerpts buscados | ninguna de quines |
| 14 | Hacker News (Algolia) | 12 hits `malbolge quine` | ninguno con artefacto |
| 15 | `archive.org` advancedsearch | `malbolge quine` | 0 resultados |
| 16 | GitHub code search `malbolge quine` | 319 hits, 100 inspeccionados | blogs, docs, intérpretes; **0 quines** |
| 17 | GitHub code search `extension:mal` | 27 archivos | todos hello-world / ejercicios |
| 18 | GitHub repo search `malbolge` | 227 repos, top 40 revisados | ninguno publica quine |
| 19 | `zb3/malbolge-tools` samples | 4 programas (cat, crackme, sep, wat) | **ninguno es quine** (verificado) |
| 20 | `kenrube/Esopoly` (polyglot 7 lenguajes) | `sources/Malbolge/source.mb` (150 B) | imprime "Malbolge program" — no es quine |
| 21 | `TryItOnline/malbolge`, `nstarke/malbolge-examples` | árbol completo | sin quines |
| 22 | `esotericarchives.com` | archivo esotérico histórico | dominio caído / 404 (ver §5) |

## 3. Candidatas verificadas

Todas ejecutadas en el oráculo independiente. `SELF-PRINT` = la salida es byte-idéntica al archivo.

| Artefacto | Bytes totales | `\n` | Bytes programa | SELF-PRINT | SHA-256 |
|---|---|---|---|---|---|
| `quine-2012.mal` (Lutter, 2012) | 59,032 | 0 | 59,032 | **sí** | `419e274e3fa7f635…` |
| `quine.mal` (Lutter, 2015) | 59,852 | 820 | 59,032 | **sí** | `dca8476f8b70c846…` |
| **`quine_53562_m281.mb` (este repo)** | **53,562** | **734** | **52,828** | **sí** | `96b670b825372a0f…` |

### Comparación en las dos convenciones

| Convención | Este repo | Lutter 2012 | Lutter 2015 | Margen |
|---|---|---|---|---|
| Bytes totales | **53,562** | 59,032 | 59,852 | **−6,290** vs 2015 · **−5,470** vs 2012 |
| Bytes de programa | **52,828** | 59,032 | 59,032 | **−6,204** en ambos casos |

**Conclusión robusta:** la ventaja no depende de la convención. Si se cuentan bytes totales gana
por 6,290 B (contra la 2015) o 5,470 B (contra la compacta de 2012); si se cuenta solo el
programa gana por 6,204 B contra cualquiera de las dos. No hay forma de contar que la haga perder.

### Detalle: la quine de 2012 es la misma máquina sin saltos de línea

`quine-2012.mal` tiene 0 saltos de línea y 59,032 bytes de programa; `quine.mal` (2015) tiene los
mismos 59,032 bytes de programa más 820 saltos de línea añadidos para legibilidad. Es decir, el
"formato bonito" de 2015 costó 820 B y no cambió el programa. Esto valida la decisión de comparar
en dos convenciones: el récord de este repo gana en ambas, sin depender de ese truco.

## 4. Programas Classic grandes descartados (no son quines)

Se ejecutaron con tope de pasos; ninguno se autorreproduce:

| Programa | Bytes | Comportamiento observado | ¿Quine? |
|---|---|---|---|
| `zb3/crackme.mb` | 52,360 | HALTED en 54,899 pasos, 31 B de salida | no |
| `zb3/sep.mb` | 56,308 | 400M pasos sin halt; imprime "Separator char:" y espera stdin | no |
| `zb3/wat.mb` | 12,485 | 2M pasos sin halt; 90 KB de salida | no |
| `zb3/cat.mb` | 10,835 | 2M pasos sin halt; cat interactivo | no |
| `Esopoly/source.mb` | 150 | HALTED en 64 pasos; imprime "Malbolge program" | no |

`crackme.mb` (52,360 B) es el único con tamaño potencialmente competitivo, pero imprime 31 bytes,
no su fuente.

## 5. Lo que NO cubre este barrido (`NOT_FOUND`, no `NOT_EXISTS`)

Declarado explícitamente para no inflar el claim:

- **Foros no indexados / IRC**: `#esoteric` en Freenode/Libera y los logs históricos del canal no
  fueron rastreados. Es el sitio más probable donde alguien habría publicado una quine alternativa
  sin dejar rastro indexable.
- **Mailing list de esolangs**: los archivos históricos no se recorrieron.
- **Repositorios privados o borrados**: GitHub solo indexa lo público y vivo.
- **`esotericarchives.com`**: el dominio responde con certificado TLS expirado y las rutas
  intentadas dan 404. El archivo esotérico histórico **no pudo consultarse**.
- **Pastes, gists y capturas de imagen**: no son descargables como artefacto ejecutable y no se
  consideraron fuente válida.
- **Búsqueda de texto libre en la web** (Google/Bing/DDG): hecha de forma indirecta vía API de
  búsqueda; no se agotaron páginas de resultados.
- **Generación automática**: no se intentó *sintetizar* una quine menor (eso es el trabajo de
  BolgeForge, no de este barrido).

**Consecuencia para el claim:** el README puede afirmar con respaldo "no existe ninguna quine
Classic publicada menor **en las 22 fuentes enumeradas**". No puede afirmar "no existe en internet".
La diferencia es real y conviene no borrarla.

## 6. Reproducir este barrido

```bash
# 1. Traer las dos quines publicadas
curl -sSL -O https://malbolge.org/quine.mal          # 59,852 B
curl -sSL -O https://malbolge.org/quine-2012.mal     # 59,032 B

# 2. Verificar que efectivamente son quines
gcc -O2 -o /tmp/mb quine/evidence/mb_classic_indep.c
/tmp/mb quine.mal        | cmp - quine.mal        && echo "2015 OK"
/tmp/mb quine-2012.mal   | cmp - quine-2012.mal   && echo "2012 OK"

# 3. Verificar el récord del repo
/tmp/mb quine/quine_53562_m281.mb | cmp - quine/quine_53562_m281.mb && echo "record OK"

# 4. Contar en las dos convenciones
for f in quine.mal quine-2012.mal quine/quine_53562_m281.mb; do
  printf '%-30s total=%s prog=%s\n' "$f" "$(wc -c <"$f")" "$(tr -d ' \t\n\r\v\f' <"$f" | wc -c)"
done
```

## 7. Veredicto

| Afirmación | Estado |
|---|---|
| Las dos quines Classic publicadas son de Lutter y miden 59,852 / 59,032 B | `DEMONSTRATED` (descargadas y ejecutadas) |
| Este repo tiene una quine Classic de 53,562 B (52,828 B de programa) | `DEMONSTRATED` (triple motor, ver `README.md`) |
| La de este repo es menor en **ambas** convenciones de conteo | `DEMONSTRATED` (−6,290 / −6,204 B) |
| No existe ninguna quine Classic publicada menor en las 22 fuentes enumeradas | `DEMONSTRATED` |
| No existe ninguna quine Classic publicada menor en todo internet | `NOT_DEMONSTRATED` (§5) |

Barrido realizado el 2026-10-17. Todos los hashes de este documento son SHA-256 y se pueden
recalcular con los comandos de §6.

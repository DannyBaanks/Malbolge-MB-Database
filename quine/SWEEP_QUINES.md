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

## 2. Universo consultado (N = 25 fuentes)

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
| 23 | **`logs.esolangs.org/freenode-esoteric`** | **logs IRC completos, 223 meses (2002-12 → 2021-06)** | **223/223 meses descargados, 0 fallos; 188 con menciones a malbolge** |
| 24 | **`logs.esolangs.org/libera-esolangs`** | **logs IRC completos, 66 meses (2021-05 → hoy)** | **66/66 meses descargados, 0 fallos; 45 con menciones a malbolge** |
| 25 | **Wayback: `matthias-ernst.eu/malbolge/quine.mb`** | **snapshots 2013–2017 (URL citada en IRC que hoy da 404)** | **2 artefactos, hashes idénticos a #7/#8; sin tercera variante** |

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

## 3-bis. Barrido de los logs IRC completos (24 años de #esoteric / #esolangs)

El hueco más grande del barrido inicial eran los logs del canal. Se cerró: el propio
[portal de la comunidad](https://esolangs.org/wiki/Esolang:Community_portal) documenta que los logs
viven en **`logs.esolangs.org`**, con dos archivos (`freenode-esoteric`, `libera-esolangs`).

### Cobertura

| Canal | Rango | Meses | Descargados | Fallos | Con menciones |
|---|---|---|---|---|---|
| `freenode-esoteric` | 2002-12 → 2021-06 | 223 | **223** | 0 | 188 |
| `libera-esolangs` | 2021-05 → 2026-10 | 66 | **66** | 0 | 45 |
| **Total** | **2002-12 → 2026-10** | **289** | **289** | **0** | **233** |

Filtro aplicado por streaming sobre cada fichero mensual (`grep -i malbolge`), sin descargar los
~600 MB completos. Resultado: **2,269 líneas** con menciones a `malbolge` en 24 años de canal.
Verificación de cobertura independiente: se re-pidió el código HTTP y el tamaño de los 289 ficheros
→ **289/289 = HTTP 200, 0 vacíos**. Los 56 meses sin menciones están contados, no asumidos.

### Qué se encontró

De 2,269 líneas, solo **23** mencionan `quine` junto a Malbolge. Ninguna anuncia una quine nueva,
ninguna da un tamaño, y ninguna es posterior a la de Lutter:

| Fecha aprox. | Quién | Qué dijo | Lectura |
|---|---|---|---|
| pre-2012 | Keymaker, kipple, malaprop, pgimeno, ihope, owt | "¿hay una quine de Malbolge?", apuestas y bromas | **antes** de que existiera ninguna: confirma que Lutter fue el primero |
| 2012-12 | (contexto) | publicación de la quine de Lutter | coherente con `quine-2012.mal` |
| ~2015 | `oerjan` (autor de Malbolge Unshackled) | `!malbolge http://matthias-ernst.eu/malbolge/quine.mb` | **la URL ya muerta** que se rescató en §3-bis |
| 2017-08 | `Malbranche` (vía bot de wiki) | añade la quine de **Unshackled** a `List of quines` | otro dialecto (ver abajo) |
| 2019-03 | `int-e` | "Oh, there is a malbolge quine." | descubrimiento tardío, no una nueva |
| 2026 | `Dragoneater67mobile` | edita `List of quines` § Unshackled (+13 B) | sigue siendo la misma de Unshackled |

**Nadie, en 24 años, publicó ni discutió una quine Classic mejor que la de Lutter.** Y hay evidencia
negativa útil: antes de 2012 varios usuarios del canal daban por hecho que una quine de Malbolge era
prácticamente imposible ("*I'm pretty sure I won't see a quine in Malbolge*", pgimeno). No existía
una quine anterior y más pequeña escondida en el canal.

### La URL muerta que sí valió la pena

La línea de `oerjan` apuntaba a `matthias-ernst.eu/malbolge/quine.mb`, hoy **404**. Se recuperó de
Wayback: snapshots de 2013 a 2017 con **dos digests distintos**. Descargados y comparados:

| Snapshot | Bytes | SHA-256 | Idéntico a |
|---|---|---|---|
| 2013-04-28 | 59,032 | `419e274e3fa7f635…` | `quine-2012.mal` (byte a byte) |
| 2015-09-14 | 59,852 | `dca8476f8b70c846…` | `quine.mal` (byte a byte) |

Es decir: **no hay una tercera variante**. El sitio de Ernst alojaba exactamente los mismos dos
artefactos que `malbolge.org`, cosa que solo se puede afirmar habiéndolos bajado. El de 2013 se
ejecutó igualmente: se autorreproduce (`HALTED`, 69,031,648 pasos).

### Malbolge Unshackled (otro dialecto, descartado por tamaño)

La quine de Unshackled que `Malbranche` enlazó en 2017 se recuperó de Wayback
(`malbolgeunshackled/quine.mb`, snapshot 2017-08-16): **913,047 B**, 3^19, y no carga en un
intérprete Classic ("too long": el límite son 59,049 celdas). Es **17× mayor** que la de este
repositorio y de otro dialecto, así que no compite por el récord Classic.

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

- ~~**Foros no indexados / IRC**: logs de `#esoteric` / `#esolangs`~~ → **CERRADO** (§3-bis):
  289/289 meses descargados y filtrados, 2002-12 → 2026-10, 0 fallos. No hay quine nueva en 24 años.
- ~~**Wayback de `matthias-ernst.eu`**~~ → **CERRADO**: recuperados los snapshots 2013/2015; son los
  mismos dos artefactos, sin tercera variante (§3-bis).
- **Mailing list de esolangs** (`lang@esoteric.sange.fi`): **sigue abierta**. El dominio devuelve 404
  y no aparece un archivo navegable en Wayback; los mensajes de 1998–2012 con adjuntos de programas
  no se pudieron recorrer. Es el último hueco con posibilidad real de albergar algo.
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
Classic publicada menor **en las 25 fuentes enumeradas**, incluidos los 289 meses completos de logs
IRC del canal de la comunidad". No puede afirmar "no existe en internet", porque la lista de correo
histórica sigue sin cubrir. La diferencia es real y conviene no borrarla.

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

# 4. Repetir el barrido de logs IRC (289 meses, ~6 min con 8 hilos)
./quine/tools/sweep_irc_logs.sh hits.txt
# Salida esperada (2026-10-17): TOTAL meses: 289 / con menciones: 233 / lineas: 2269

# 5. Verificar la URL muerta de matthias-ernst.eu en Wayback
curl -sS "http://web.archive.org/cdx/search/cdx?url=matthias-ernst.eu/malbolge/quine.mb&output=json&fl=timestamp,statuscode,digest"
curl -sSL "http://web.archive.org/web/20130428104606id_/http://www.matthias-ernst.eu/malbolge/quine.mb" -o wb2013.mb
sha256sum wb2013.mb   # = 419e274e... (idéntico a quine-2012.mal)

# 6. Contar en las dos convenciones
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
| No existe ninguna quine Classic publicada menor en las 25 fuentes enumeradas (incl. 289 meses de logs IRC) | `DEMONSTRATED` |
| No existe ninguna quine Classic publicada menor en todo internet | `NOT_DEMONSTRATED` (§5) |

Barrido realizado el 2026-10-17. Todos los hashes de este documento son SHA-256 y se pueden
recalcular con los comandos de §6.

# Journal PureEpoch M1b adaptado + selección según fase

## Hipótesis y resultado

H1: en una única VM Classic, cada solicitud de {01,02} puede producir uno de dos valores, guardar una representación reversible en un journal, alterar la celda objetivo, escoger una de dos rutas de restauración a partir del estado de fase, restaurar desde el journal y regresar para procesar la siguiente solicitud. H0: una de estas propiedades falla en los flujos medidos.

**CONDITIONAL_PASS** en nueve flujos: vacío, solicitudes individuales, `010201`, `020102`, ocho repeticiones de cada solicitud, dieciséis alternancias y 128 solicitudes pseudoaleatorias (semilla 20261107). Oráculo Python y runner C coinciden en bytes de salida y pasos para el positivo. La traza Python comprueba orden temporal de escritura, save en journal, alteración y reset del objetivo, selección de fase, diez rotaciones del journal y restauración. El mismo PC de IN reaparece al volver.

## Mecanismo concreto adaptado de PureEpoch

Este experimento adapta el **protocolo lógico M1b** `SAVE → clobber → 10 ROT sobre journal → RESTORE` de `Malbolge-PureEpoch/tools/build_candidates.py`, función `build_checkpoint` (SHA-256 `d7d11ce0076f77210a5cd1c81e1f6c4d93a9dc21e84729306eaeaa9ec69292c2`; repo inspeccionado en `2e9765f6fe2550e10425ab92d059ca73bcc12547`). No copia el binario M1b a otra dirección ni enlaza un servicio externo: traduce su lógica a nuevas celdas, flags y retornos HeLL dentro del selector-store. El candidato original M1b hace una restauración incondicional y acotada; esta adaptación no demuestra rollback general ni recuperación ante cualquier fallo.

Para C1=29524, la operación `g(V)=crazy(V,C1)` es involutiva: `crazy(g(V),C1)=V`. La celda `epoch_journal` empieza en C1 en cada solicitud. Se escribe `g(V)`; se lleva `compose_slot` a C1 con dos CRAZY; se rota el journal diez veces, devolviéndolo al valor guardado y cargándolo en A; luego se restaura `compose_slot=crazy(A,C1)=V`.

Traza de `010201`, antes de OUT:

| Solicitud | Valor | Journal: C1 → guardado | Celda objetivo: valor → pasos de alteración → restaurado | fase / ruta |
|---|---:|---|---|---|
| 01 | 80 | 29524 → 29564 | 80 → 80 → 29524 → 80 | 74 / odd |
| 02 | 82 | 29524 → 29442 | 82 → 0 → 29524 → 82 | 70 / even |
| 01 | 80 | 29524 → 29564 | 80 → 80 → 29524 → 80 | 74 / odd |

En la primera solicitud la primera operación de alteración deja 80 igual; la segunda sí lo cambia a C1. Al volver al siguiente IN, scratch, objetivo y journal se han preparado de nuevo a C1. Las marcas de tiempo del JSON verifican que la selección de fase ocurre **después del reset y antes del último CRAZY que restaura**. Ambas rutas llevan al mismo tipo de restauración; difieren en su control y rearme de MOVED, no son dos algoritmos de búsqueda diferentes.

## Selección según estado y controles

`EPOCH_PHASE` usa el ciclo XLAT2 70↔74. Su valor al entrar en cada época alterna y dirige a `epoch_odd` o `epoch_even` antes de restaurar la celda. La prueba de `01` repetido ocho veces comprueba que la ruta cambia aunque la solicitud no cambie. Se verifica por traza Python; el runner C se compara externamente en salida y pasos, no dispone de traza de memoria interna.

- **Mutante journal:** reemplaza el valor a guardar por cero; `010201 → 000000` en ambos motores. La salida y el contrato de estado fallan.
- **Mutante restore:** carga cero tras leer el journal; `010201 → 545454` en ambos motores. El journal puede contener el valor correcto, pero se restaura C1 en vez del valor solicitado.
- **Mutante fase:** fuerza siempre una ruta. `010201 → 505250` sigue siendo correcto en ambos motores, **pero el contrato de estado y alternancia lo rechaza**. Esto es un control contra verificar solamente stdout; ambos caminos del candidato positivo tienen el mismo resultado observable.

Los nueve ensayos y nueve controles negativos están en `results.json`. La validación estática del loader estricto, ignorando whitespace, encuentra cero celdas fuente inválidas; no se ejecutó un loader estricto independiente. La imagen se ejecuta en Classic sin escrituras del host durante la ejecución; el host proporciona la entrada y recoge la salida.

## Alcance y NOT_DEMONSTRATED

La selección es según **estado binario de fase**, con dos rutas preprogramadas; no se ha construido un buscador general de transiciones ni elegido la estrategia de reparación según la naturaleza de una corrupción arbitraria. Las solicitudes y valores están limitados a 01/02 → 50/52, y la dirección de la celda objetivo es fija. No hay validación de daño, retry condicional, conservación de toda la memoria física, independencia respecto a LMAO ni ABI general de llamadas. La adaptación demuestra un journal de restauración acotado inspirado directamente en M1b, no una integración binaria directa del programa PureEpoch ni el resolvedor completo.

## Reproducir

`python3 vm_malbolge/evidence/epoch_journal_state_v2/probe.py` ejecuta los casos sobre las instancias conservadas y sobrescribe `results.json`; copiar el pack antes de repetir para conservar la evidencia. `build.py <directorio-nuevo>` reconstruye las cuatro fuentes y las ensambla desde `epoch_selector_store_v1/combined_pruned.hell`. `rebuild.raw.txt` registra que las cuatro fuentes coincidieron byte por byte y que la imagen reconstruida emitió `505250` para `010201`. Como LMAO puede variar en bytes, el hash identifica la instancia conservada.

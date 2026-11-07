# Selector: primer punto de divergencia y estado de rearme

## Pregunta e hipótesis

Para `rearmed2.mb` con entrada binaria `01 02 01`, ¿por qué el oráculo Python continúa después de que el runner C se detenga? ¿Es suficiente restaurar cuatro celdas de datos para reingresar al selector?

**Resultado:** primera divergencia semántica localizada; selector `A→B→A` **NOT_DEMONSTRATED**. Los dos intentos adicionales de corregir la flag fallaron. No se modifica el oráculo ni se infiere imposibilidad general.

## Primera divergencia

Un runner construido a partir de `Malbolge-Engine/src/vm.c` con una sola impresión por paso produce la misma salida y número de pasos que el runner C original para este caso. Se compararon los preestados `(a,c,d,mem[c],posición entrada)` con un trazador de la semántica Python: **59.691 pasos coinciden**. En el paso **59.692**, ambos llegan a:

```
a=9814, c=71, d=52333, mem[c]=0, bytes_consumidos=2
```

El C instrumentado comprueba que `mem[c]` sea imprimible y se detiene; el oráculo Python calcula `(mem[c]+c)%94 = 71` y continúa. Un segundo trazador C independiente (`Malbolge-PureEpoch/build/trace_ref`) confirma `STALL` en el mismo estado, usando numeración desde cero: paso 59.691. La comparación con ese trazador encontró coincidencia de registros, salida y todos los deltas de memoria en los 59.691 pasos anteriores. El runner de producto muestra `HALTED`; su CLI usa esa etiqueta tanto para HALT/EOF como para celda de instrucción no imprimible. La instrumentación C es una recompilación de la fuente disponible; no se afirma que su binario sea idéntico al runner distribuido, aunque su salida y paso final coinciden en este caso.

## Estado al reingreso

Antes de los dos primeros IN de `rearmed2`, `a/c/d` coinciden y las cuatro celdas de datos medidas en v0 son C1. Entre las **etiquetas CODE** del `.dbg`, sin embargo, cambian:

| Etiqueta | Dirección | Primer IN | Segundo IN |
|---|---:|---:|---:|
| `NO_MORE_CARRY_FLAG` | 58908 | 74 | 70 |
| `CARRY` | 59047 | 70 | 74 |

Es una diferencia real de estado, no prueba de que esas dos celdas sean la única causa del fallo. Se compararon las direcciones etiquetadas CODE, no se afirmó que toda la memoria se haya restaurado. En los dos intentos de rearme se insertó un restablecimiento de la primera flag, una vez directamente y otra mediante un salto condicional; ambos ensamblaron pero fallaron incluso los controles de un byte y A→B→A. No hay corrección demostrada.

## Controles y límites

- `reset_carry` y `conditional_flag`, entradas `01`, `02`, `010201`, `020102`: los 8 contratos se rechazaron; salidas y pasos Python/C coinciden en estos intentos fallidos.
- El control de un byte de la imagen original y la captura de los resultados anteriores están en `epoch_selector_rearm_v0`.
- EOF Python y C tienen etiquetas distintas; aquí la divergencia identificada ocurre **antes del EOF**, con un tercer byte disponible.
- El código Python no aplica la guarda de código imprimible que sí tiene este C. En consecuencia, no se debe usar su traza posterior a esa posición como si fuera la ejecución del runner C.
- No se ha demostrado selector reutilizable, rearme completo, buscador de transición o integración PureEpoch. Próximo paso: estudiar el retorno/estado de flags sin suponer que cambiar una celda aislada es suficiente, y exigir que ambas implementaciones procesen la tercera solicitud.

## Reproducir

`python3 vm_malbolge/evidence/epoch_selector_divergence_v1/probe.py` verifica las trazas C comprimidas conservadas, repite ambos intentos y reescribe `results.json`; copiar el pack antes de repetir para conservarlo. `build.py <directorio-nuevo>` recompila las dos variantes, instrumenta una copia de la fuente C disponible y ejecuta el trazador C de PureEpoch en un directorio nuevo; necesita los repos hermanos en el layout documentado y `gcc`. LMAO puede producir bytes diferentes en reconstrucciones; se comparan las instancias por SHA-256, no por nombre.

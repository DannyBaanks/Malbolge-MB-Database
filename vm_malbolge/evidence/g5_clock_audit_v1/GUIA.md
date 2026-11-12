# Probar el reloj G5

Desde la raíz de `MALBOLGE-MB-DATABASE`:

```bash
../Malbolge-PureEpoch/build/olmstead vm_malbolge/evidence/g5_clock_audit_v1/clock_positive.mb | od -An -tx1
```

Regla de oro: el reloj es un experimento acotado; no demuestra que los dos restauradores G5 formen un bucle autónomo.

Salida real:

```text
 a6 a6 a6
```

| Resultado | Significado |
| --- | --- |
| `a6 a6 a6` y Olmstead termina | El reloj pasó por tres salidas y llegó a HALT. |
| `a6` con el control | La ruta alterada terminó después de una salida. |
| Falta el ejecutable | Se necesita `Malbolge-PureEpoch` hermano con Olmstead construido. |

Las tres salidas ocurren en tres posiciones de código distintas; la celda compartida es el reloj. Las imágenes `shared_*`, `rot_*` y `movd_*` son primitivas separadas, con retornos preinstalados, no un restaurador general. Los scripts de evidencia escriben en su carpeta: repítelos sólo en una copia aislada.

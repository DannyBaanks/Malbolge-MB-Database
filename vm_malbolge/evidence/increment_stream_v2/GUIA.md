# Probar el incremento de cuatro bytes

Desde la raíz de `MALBOLGE-MB-DATABASE`:

```bash
printf 'ABCD' | ../Malbolge-PureEpoch/build/olmstead vm_malbolge/evidence/increment_stream_v2/increment_four.mb | od -An -tx1
```

Regla de oro: esta imagen hace exactamente cuatro lecturas; aún no es un filtro de longitud arbitraria ni gestiona EOF limpiamente.

Salida real del comando:

```text
 42 43 44 45
```

| Resultado | Significado |
| --- | --- |
| `42 43 44 45` para `ABCD` | Los cuatro bytes se incrementaron. |
| Menos de cuatro bytes | La imagen puede emitir bytes extra o no detenerse; no usarla como filtro de EOF. |
| Más de cuatro bytes | Sólo procesa los primeros cuatro. |
| Falta Olmstead | Se necesita el binario construido del repo hermano `Malbolge-PureEpoch`. |

Las imágenes `revisit_*.mb` son experimentos aparte: verifican una instrucción rearmada y no hacen incremento. Para ejecutar scripts que generan resultados, crea un árbol aislado nuevo; no reescribas la evidencia.

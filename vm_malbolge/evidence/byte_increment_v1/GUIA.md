# Probar el incremento de dos bytes

Desde la raíz de `MALBOLGE-MB-DATABASE`:

```bash
printf '\000\377' | ../Malbolge-PureEpoch/build/olmstead vm_malbolge/evidence/byte_increment_v1/increment_two.mb | od -An -tx1
```

Regla de oro: esta imagen experimental procesa **exactamente dos lecturas**; no es un filtro general ni maneja EOF de forma segura.

La salida real de ese comando fue:

```text
 01 00
```

| Salida | Significado |
| --- | --- |
| `01 00` para `00 ff` | Incrementó ambos bytes módulo 256. |
| Falta el ejecutable Olmstead | Hace falta el repo hermano `Malbolge-PureEpoch` con su binario construido. |
| Datos cortos o largos | La imagen hace dos lecturas: no garantiza EOF limpio y descarta los bytes posteriores. |

El pipe con `od` muestra bytes en hexadecimal: evita confundir `00` con texto vacío. Para repetir las pruebas que escriben JSON, usa una copia aislada de la carpeta; no reescribas la evidencia almacenada.

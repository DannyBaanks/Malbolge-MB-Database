# Trazas REA — G5b P5

Se usó `rea.trace_malbolge` 6.9.0, motor Classic v1, con entrada vacía, `eof_mode=olmstead_1998`, máximo de 10 000 pasos y el máximo declarado de captura de 4096 eventos.

| Caso | Evidencia | Imagen SHA-256 | Estado | Pasos/eventos | Salida |
|---|---|---|---|---:|---|
| Positivo `lll → rr → lr → rl → llr` | `ev_9ec032d61bf9e84511412b35648ce5ad800decf0020c6b02e640c774f9f14283` | `c5b56940aa23efeb6f16f8876f818ca28d349bf3d6392add8126385c028c6bab` | HALTED | 4723/4096, truncada | `[98,230,110,230,110]` |
| Control, `f_extra` adicional en `lll` | `ev_63857e5d868c74602bb9b4a604172df1fdcb7f2999e1b7128afe4e30b0cb8f53` | `2a857c758242f00a8ddba9faaf059e6bfad04acdee3384aa2c416c4cc399fe5f` | HALTED | 4806/4096, truncada | `[98]` |

REA confirma la terminación y las salidas completas de ambas imágenes. La captura retiene los eventos 1–4096; no contiene eventos en `pc=38058` ni en las continuaciones `15000`–`15016`. Aunque el resumen informa un `peak_position` mayor que 38 000, los eventos necesarios para comprobar las cinco rutas quedaron fuera del prefijo retenido. Por ello, **la cobertura de llamadas y retornos por eventos REA es NOT_DEMONSTRATED**. El resultado no se usa como prueba de las cinco rutas.

Los parámetros, salidas de ejecución, conteos y digests de estado están resumidos en [rea_summary.json](rea_summary.json). Los IDs conservan la referencia a las evidencias completas administradas por REA.

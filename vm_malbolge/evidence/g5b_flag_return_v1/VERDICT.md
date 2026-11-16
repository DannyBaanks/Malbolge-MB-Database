# G5b-2 P1: una variable, dos llamadores, retorno por bandera — veredicto

2026-11-15. Base `d4d32a7` (preregistro en `GATES.md`). Resultado: **PASS (G0–G4)**.

Primera primitiva del "mini-LMAO nativo": una variable `V` con un único sitio de escritura (`ROT_V`), dos llamadores `A` y `B`, y retorno calculado mediante bandera `F` (`MOVD`↔`NOP` sin tick, `pc ≡ 60`, palabra inicial `74`).

| Puerta | Resultado | Evidencia |
| --- | --- | --- |
| G0 (estática) | **PASS** | `assemble.py` valida las 6 islas (`K`, `F`, `MOVD_V`, `ROT_V`, `OUT`, `MOVD_LOOP`) contra `XLAT1`/`XLAT2` de BolgeForge y verifica que las 39 932 celdas de cada imagen cargan en `ji*p</vo`. |
| G1 (nativo) | **PASS** | Olmstead (`Malbolge-PureEpoch/build/olmstead`), entrada vacía: `positive.mb` emite `1313210b0b914b4b89` (`19 19 33 11 11 145 75 75 137` = `r1 r1 r2 r3 r3 r4 r5 r5 r6`), `rc = 0` por HALT del reloj `K` en su 4.ª visita. |
| G2 (traza) | **PASS** | Trazador scratch del repo (`epoch_dload_compose_v1/probe.py` `SE`) y `clasesbolge/tools/malbolge.py` (tercer intérprete) producen la misma salida byte a byte (`3367` / `3366` pasos). `F` vale `74` al inicio de las 4 visitas a `K`; `ROT_V` (`15193`) es el único sitio que escribe en `V` (`41000`); ningún `JMP` de isla cambia. |
| G3a (control A) | **PASS** | `control_a.mb` (A no conmuta `F`): las dos llamadas vuelven por B; los tres intérpretes emiten `13210b` (`19 33 11` = `r1 r2 r3`), `rc = 0`. |
| G3b (control B) | **PASS** | `control_b.mb` (`p1+1` salta la segunda ejecución de `F`): `F` queda en `70` (NOP) a partir de la 2.ª iteración y la salida diverge del positivo (`1313210b91` = `19 19 33 11 145`), `rc = 0`. |
| G4 (reproducibilidad) | **PASS** | Dos planificaciones+ensamblados en directorios aislados producen `.mb`, `.ops`, `.plan.json` y `.targets.json` idénticos byte a byte. |

## Alcance

- Demuestra que una rutina compartida con islas de tick (`[op][JMP]`) y flujos de `d` por encima de la imagen puede ser llamada desde dos sitios distintos y retornar por una bandera `MOVD`↔`NOP` de periodo 2 a lo largo de múltiples iteraciones con estado mutable `V`.
- Fuera de alcance (según `GATES.md`): más de dos llamadores, varias variables, lectura de EOF y mezcla `crazy`.

## Reproducción

```sh
zig build-exe vm_malbolge/evidence/g5b_flag_return_v1/plan.zig -O ReleaseSafe -femit-bin=/tmp/p1_plan
python3 vm_malbolge/evidence/g5b_flag_return_v1/assemble.py /tmp/p1_plan /tmp/p1_run01
python3 vm_malbolge/evidence/g5b_flag_return_v1/assemble.py /tmp/p1_plan /tmp/p1_run02
python3 vm_malbolge/evidence/g5b_flag_return_v1/verify.py /tmp/p1_run01 /tmp/p1_run02
```

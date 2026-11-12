# Ejecutar el restaurador de dos celdas

Desde la raíz de `MALBOLGE-MB-DATABASE`:

```bash
python3 -c 'import subprocess; r=subprocess.run(["../Malbolge-PureEpoch/build/olmstead","vm_malbolge/evidence/shared_restore_two_v1/restore2_positive.mb"],capture_output=True); print(f"rc={r.returncode} stdout={r.stdout.hex()}")'
```

Salida real:

```text
rc=0 stdout=
```

Olmstead termina en el HALT de CLOCK2 (sin I/O). Para ver T1=T2=40:

```bash
python3 vm_malbolge/evidence/shared_restore_two_v1/verify.py
```

| Resultado | Significado |
| --- | --- |
| `final.T1=40` y `final.T2=40`, `halt_pc=58397` | Positivo: dos restauraciones nativas. |
| Control `T1=39` y `T2=39` | Constante/C2 alterados. |
| `rc≠0` en Olmstead | Imagen o runner incorrectos. |

No reescribas el pack sellado: sintetiza en una copia aislada.

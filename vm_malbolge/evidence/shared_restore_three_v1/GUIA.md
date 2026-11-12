# Ejecutar el restaurador de tres celdas

Desde la raíz de `MALBOLGE-MB-DATABASE`:

```bash
python3 -c 'import subprocess; r=subprocess.run(["../Malbolge-PureEpoch/build/olmstead","vm_malbolge/evidence/shared_restore_three_v1/restore3_positive.mb"],capture_output=True); print(f"rc={r.returncode} stdout={r.stdout.hex()}")'
```

Salida real:

```text
rc=0 stdout=
```

Para ver T1=T2=T3=40:

```bash
python3 vm_malbolge/evidence/shared_restore_three_v1/verify.py
```

| Resultado | Significado |
| --- | --- |
| `final.T1=T2=T3=40`, `halt_pc=58679` | Positivo: tres restauraciones nativas. |
| Control `T1=T2=T3=39` | Constantes alteradas. |
| `rc≠0` en Olmstead | Imagen o runner incorrectos. |

No reescribas el pack sellado: sintetiza en una copia aislada.

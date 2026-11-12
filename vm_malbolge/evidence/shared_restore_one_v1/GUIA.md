# Ejecutar el restaurador de una celda

Desde la raíz de `MALBOLGE-MB-DATABASE`:

```bash
python3 -c 'import subprocess; r=subprocess.run(["../Malbolge-PureEpoch/build/olmstead","vm_malbolge/evidence/shared_restore_one_v1/restore_positive.mb"],capture_output=True); print(f"rc={r.returncode} stdout={r.stdout.hex()}")'
```

Regla de oro: esta imagen restaura una celda con un objetivo fijo y no implementa un bucle general ni EOF.

Salida real:

```text
rc=0 stdout=
```

| Resultado | Significado |
| --- | --- |
| `rc=0 stdout=` | Olmstead terminó sin producir bytes. Para observar la memoria, consulta la traza REA o scratch del veredicto. |
| Error al abrir el ejecutable | Hace falta el repo hermano `Malbolge-PureEpoch` con Olmstead construido. |
| Misma salida del control | Es normal: ambos terminan sin stdout; las trazas muestran `40` en el positivo y `39` en el control. |

No ejecutes los scripts de evidencia sobre el pack sellado: escriben resultados en su propia carpeta. Utiliza una copia aislada nueva.

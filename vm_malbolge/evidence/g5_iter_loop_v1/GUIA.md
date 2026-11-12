# Ejecutar el loop de iteración G5 (v0)

```bash
python3 vm_malbolge/evidence/g5_iter_loop_v1/synthesize.py
python3 vm_malbolge/evidence/g5_iter_loop_v1/verify.py
```

Positivo: `halt_pc=58376`, `hclock_visits=4`, `native_rc=0`.
Control: misma parada, traza TA distinta.

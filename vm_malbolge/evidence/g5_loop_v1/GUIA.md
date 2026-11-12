# Comprobar el bloqueo de rearme in-place

Desde `MALBOLGE-MB-DATABASE`:

```bash
python3 vm_malbolge/evidence/g5_loop_v1/scratch_clock_rearm.py
python3 vm_malbolge/evidence/g5_loop_v1/scratch_aux_sled.py
```

El primero debe afirmar T2=40 con CLOCK rearjado en host. El segundo deja
`scratch_aux_probe1.json` mostrando que el JMP del sled AUX no escribe CLOCK
cuando d queda en el fallthrough del despachador.

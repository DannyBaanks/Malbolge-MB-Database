# Prototipo P5 v1 — resultado fallido conservado

Comando ejecutado el 2026-11-17 desde la carpeta del pack:

```sh
env PYTHONDONTWRITEBYTECODE=1 MALBOLGE_MB_DATABASE_ROOT='/home/danny/Development/ISyCo Git/MALBOLGE-MB-DATABASE' python3 probe.py /tmp/g5b-p5-stage-20261117/run01/positive.mb
```

Estado: exit 1 en la comprobación de las llamadas esperadas. El intérprete local terminó (`halt`, 4680 pasos), pero solo hizo una llamada a `pc=38058`, visitó `15016` y emitió `62`. El valor compartido pasó de 12345 a 12130 con `d=40006`; flags y cola de operación quedaron intactas. Olmstead se ejecutó antes de la aserción y guardó sus flujos junto a la imagen original del prototipo.

La copia de `positive.mb` es byte idéntica a la imagen de `/tmp/g5b-p5-stage-20261117/run01/`. El error de aserción capturado está en [probe.stderr.raw.txt](probe.stderr.raw.txt). Este intento no se cuenta en las puertas P5 corregidas.

# G5b P5c — barrido exhaustivo de cinco llamadores

Fecha: 2026-11-24. Resultado: PASS, limitado a cinco hojas, una variable y un sitio crazy compartido.

Se auditaron run01 y run02 conservados de GLM y se generó run03 con el probe original, sin modificar las tandas anteriores. Las tres tandas cubren exactamente las 120 permutaciones; las imágenes coinciden byte por byte entre tandas y hay 120 SHA-256 distintos dentro de cada tanda. Olmstead nativo, clasesbolge y el trazador local aceptan cada imagen; salida hexadecimal 62e66ee66e, cinco llamadas y continuaciones 15000,15004,15008,15012,15016.

REA se ejecutó sobre las 120 imágenes de run01, con captura de prefijo y ventana final calculada como max(1, pasos-4095). Se verificó igualdad de estado final, estado inicial, salida, pasos y status entre ventanas. La ventana llega al último paso y recoge cinco eventos en 38058 con d=40006 y a=39999,12130,21990,7534,21990, además de las cinco continuaciones. rea.json conserva las mediciones por orden. El control negativo previo sigue en ../g5b_flag_return_v5b_rea_window; este cierre añade cobertura exhaustiva de órdenes positivas, no un nuevo control negativo.

## Reproducción desde este directorio

```sh
python3 -B sweep.py /tmp/g5b-p5c-new-run
node rea_sweep.mjs "$PWD" /home/danny/Development/rea/dist /tmp/g5b-p5c-rea.json
python3 verify.py "$PWD" /tmp/g5b-p5c-new-run
sha256sum -c hashes.sha256
```

La verificación lee rea.json conservado; para comprobar una captura nueva, compararla con ese archivo (el JSON es determinista). No reutilizar directorios de salida existentes.

## NOT_DEMONSTRATED

Más de cinco hojas, varias variables, entrada/EOF, recursión, un compilador general o universalidad. Las permutaciones cambian el layout compilado; no demuestran selección arbitraria de llamadas en una única imagen fija. No se modifica el veredicto histórico P5b ni su evidencia.

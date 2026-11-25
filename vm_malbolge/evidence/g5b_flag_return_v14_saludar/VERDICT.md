# G5b P14 — def saludar(): print("Hola"); saludar()

2026-11-24 México (2026-11-25 UTC). Base P13 e0d4934. PASS acotado para GATES.md.

```python
def saludar():
    print("Hola")

saludar()
```

Una imagen Classic autónoma de 39932 bytes implementa ese comportamiento con llamada y retorno reales, no solo una impresión puesta en línea. El llamador guarda la dirección numérica de continuación en slot=50000 usando el journal de P13 y salta a saludar en PC=20000. Solo el cuerpo de saludar ejecuta los cinco OUT de Hola seguido de LF. Después recupera el retorno mediante diez ROT y ejecuta JMP mem[50000]. El llamador reanuda en PC=30000, rearma slot/journal y termina.

## Resultados

| Imagen | Salida | Recorrido de saltos | Pasos locales/REA |
|---|---|---|---|
| saludar | Hola + LF | llamador→20000→30000 | 12872 |
| alternate | Hola + LF | llamador→20000→32000 | 12846 |
| broken_return | Hola + LF + ! | llamador→20000→29525 (error) | 12858 |
| bypass | vacía | llamador→30000, sin entrar en saludar | 12787 |

Las dos imágenes legítimas tienen código de saludar idéntico byte a byte; cambia la continuación numérica que proporciona el llamador. El control de retorno roto conserva la impresión pero no visita after_call, demostrando que stdout correcto por sí solo no prueba CALL/RET. El control bypass no ejecuta la función y no imprime. Los manejadores de error son código Malbolge real.

## Afirmaciones

| Afirmación | Estado | Evidencia |
|---|---|---|
| Salida exacta equivalente al programa Python | DEMONSTRATED | Python ejecutado, stdout nativo y tres intérpretes adicionales |
| Llamador y función separados, con retorno indirecto numérico | DEMONSTRATED | call, saludar_entry, print_0..4, ret, after_call y eventos JMP REA |
| Código de función independiente de la continuación 30000/32000 | DEMONSTRATED | comparación de los bytes del cuerpo |
| Controles distinguen impresión y llamada correcta | DEMONSTRATED | broken_return y bypass |
| Compilación general de funciones Python | NOT_DEMONSTRATED | traducción manual de este ejemplo |

Olmstead termina con rc=0, clasesbolge con end, trazador local con halt y REA con HALTED. Todas las salidas coinciden byte a byte; los positivos coinciden además con la ejecución de saludar.py. REA reconstruye el slot y el journal y verifica el PC inmediatamente posterior a cada salto. Capturas de hasta 4096 eventos se combinan con igualdad de solapamientos, digests, salida y pasos, cubriendo cada paso real.

run02/run03 son las generaciones finales idénticas en imágenes, planes, trazas, stdout/stderr y capturas REA. run01 conserva la primera generación; los metadatos finales eliminan un campo targets heredado de P13 que no intervenía en el programa. El binario nominal es run02/saludar.mb y se puede ejecutar sin Python mediante ejecutar.sh; GUIA.md contiene el comando probado y su salida.

## Reproducción técnica

```sh
python3 -B probe.py /tmp/g5b-p14-new-run
node rea.mjs "$REA_DIST" /tmp/g5b-p14-new-run
python3 verify.py .
sha256sum -c hashes.sha256
```

Usar un directorio nuevo. REA_DIST apunta al dist compilado de REA y MALBOLGE_MB_DATABASE_ROOT permite otro checkout. environment.json identifica dependencias, commands.json registra invocaciones y códigos de salida, y se conservan logs crudos. verify.py audita las generaciones finales; comparar nuevas imágenes con run02.

## NOT_DEMONSTRATED

Este es un descenso manual del ejemplo concreto a Classic, sin frontend Python nuevo. Hace una llamada por ejecución; no demuestra que las mismas instrucciones de saludar puedan invocarse varias veces después de cifrarse. No implementa argumentos, variables locales generales, recursión, stdin ni pila numérica de varias posiciones. El tamaño incluye el bootstrap nativo conservado de P5/P13 y no está optimizado.

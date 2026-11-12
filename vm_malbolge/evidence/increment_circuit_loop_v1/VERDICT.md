# Bucle de incremento con EOF y compilación especializada

2026-11-12. Base `8990c01`. Se produjo una imagen Malbolge Classic estricta que, en una sola ejecución, incrementa cada byte módulo 256 y hace HALT autónomo en EOF bajo Olmstead. Se genera desde `,+[-+.,+]` con el compilador especializado `vm_malbolge/tools/increment_bf/compile.py`; no se copia una imagen de incremento prefabricada.

| Puerta de este experimento | Resultado y alcance |
|---|---|
| G0: álgebra | PASS en el dominio finito de 256 bytes y EOF. `check_algebra.py` comprueba el acarreo y los destinos EOF; paridad CRAZY de 59049 celdas en `run02/parity.stdout.raw.txt`. |
| G1: bucle | PASS funcional en los casos medidos. `verification_v3.stdout.raw.txt`: las mismas posiciones IN=56725 y OUT=56707 se reutilizan; 10 000 bytes se transforman en una sola ejecución. Sin tabla de 256 entradas. El estado completo **no vuelve bit a bit** al mismo valor en cada IN: ver límite más abajo. |
| G2: EOF | PASS en los casos medidos: vacío, 256 entradas de un byte, flujos binarios y largos terminan con rc=0 y salida exacta. El modelo independiente y REA fuente con `olmstead_1998` observan HALT; el control que omite la escritura del código de EOF agota el límite. |
| G3: comparación | PASS para 517 casos finitos: Python, BF16 y Olmstead coinciden, incluidos todos los bytes individuales, 256 secuencias pseudoaleatorias, `00..ff` y 10 000 bytes. REA captura Python/BF y reproduce la imagen para ASCII, binario, los 256 bytes y vacío; se cotejan las ventanas de los cuatro replays con el modelo, hasta HALT. |
| G4: compilación | PASS especializado: acepta sólo `,+[-+.,+]`, BF16 wrap y EOF=65535; rechaza patrón y convenciones diferentes. Genera HeLL, disposición e instalador nuevos. Una compilación en árbol aislado, sin el checkout hermano BolgeForge ni imagen objetivo preexistente, fue idéntica byte a byte. No es un compilador BF general. |

## Construcción

El circuito calcula el acarreo ternario en paralelo mediante CRAZY y ROT. Para entrada de byte `x`, su palabra final es `x+1`; OUT emite el byte bajo, por lo que `ff → 00`. La separación EOF usa un prefijo de trits: todos los bytes llegan a uno de cuatro destinos y el valor Olmstead 59048 llega al destino de HALT. Las máscaras se regeneran y los temporales se limpian al usarse; instrucciones reutilizables y banderas despachan las operaciones. El instalador se ejecuta dentro de Malbolge antes de la primera entrada.

El backend incorpora código de síntesis derivado de BolgeForge bajo licencia MIT y un fragmento de bootstrap de `cat.mal` atribuido a Matthias Lutter. Utiliza el código fuente LMAO incluido en `third_party/lmao`, lo compila y lo modifica **sólo en un directorio temporal** para extraer la disposición; después sintetiza la imagen. Esta independencia es respecto al checkout hermano y a una imagen de incremento prefabricada, no una afirmación de ausencia total de componentes previos. La guía y los requisitos están en `vm_malbolge/tools/increment_bf/GUIA.md`.

## Controles y límites

- La imagen SHA-256 es `aec09e9fe64ae4b456818ce1960b7ecb92ccfae456592c2d5b8413b6190757f1`; el cargador Olmstead rechaza una celda de fuente no válida. Omitir una escritura del instalador produce SIGSEGV y omitir otra de la rama EOF provoca timeout. Esos son **fallos detectados**, no paradas limpias.
- El primer ensamblado con tabla y el primer intento con inicializador LMAO no cupieron; sus errores se preservan. La imagen final usa el circuito compacto y un instalador diferente.
- `state_observe_v3.stdout.raw.txt` compara las celdas inicializadas en cinco visitas a IN. Dos temporales conservan valores distintos en la frontera y se limpian a 29524 antes de reutilizarse; cambian también celdas de relleno y algunas celdas de código que decodifican sin efecto en ambas fases. Por ello no se afirma restauración bit a bit de **todo** el estado ni se eleva retroactivamente el G1 de `increment_stream_v2`, que exigía esa construcción específica. Los datos funcionales y la reutilización de código se reportan separadamente.
- La herramienta MCP REA conectada, con EOF legado implícito, no sirve para validar el EOF Olmstead: con entrada vacía el replay no termina dentro del presupuesto y emite bytes distintos. Esa observación está preservada. El servicio fuente local de REA (`32aade1ac`), invocado con `eof_mode=olmstead_1998`, sí termina; es un replay de fuente, no una actualización del servidor MCP conectado. Sus ventanas comienzan después del arranque y `events_truncated=true`; `rea_compare_v3.stdout.raw.txt` compara cada evento capturado hasta HALT con el modelo independiente.
- No se demuestra compilación de BF arbitrario, equivalencia temporal interactiva, infinitos streams ni todos los estados posibles. Los ensayos demuestran las entradas medidas y el contrato de EOF indicado.

## Reproducción

La guía de usuario tiene los comandos de compilación y ejecución. Para repetir la batería y el cotejo de ventanas guardadas, desde la raíz del repositorio:

```sh
python3 vm_malbolge/evidence/increment_circuit_loop_v1/verify.py vm_malbolge/evidence/increment_circuit_loop_v1/run02/increment.mb
python3 vm_malbolge/evidence/increment_circuit_loop_v1/rea_compare.py vm_malbolge/evidence/increment_circuit_loop_v1/run02
python3 vm_malbolge/evidence/increment_circuit_loop_v1/state_observe.py vm_malbolge/evidence/increment_circuit_loop_v1/run02
python3 vm_malbolge/evidence/increment_circuit_loop_v1/verify_compiler.py
```

Los comandos de evidencia imprimen JSON; no sobrescriben los resultados preservados. Olmstead, BF16 y el servicio fuente de REA son dependencias de verificación; el compilador tiene sus propias dependencias descritas en la guía. Los originales REA con rutas locales están en el estado privado local con hashes en el manifiesto; las copias del pack sustituyen la ruta de la imagen.

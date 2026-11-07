# Selector + almacén rearmable: composición híbrida por lote

## Pregunta e hipótesis

H1 acotada: dos imágenes Classic ya existentes pueden conectarse de manera que una selección dependiente del dato produzca uno de dos bytes, y una **única** ejecución del almacén exacto rearmable reciba una secuencia de esos resultados y la almacene/recupere sin pérdidas. H0: alguna selección, tránsito, escritura, rearme o recuperación falla en los protocolos medidos.

**Resultado: CONDITIONAL_PASS** para los tres protocolos ensayados (AB, BABA, AAAABBBBABAB). Selector: `epoch_resolver_dispatch_v0/dispatch.mb`; almacén: `epoch_reusable_store_v1/positive.mb`. El primero se ejecuta una vez por solicitud; el segundo se ejecuta una vez para todo el lote. El selector calcula `0x68` para la solicitud codificada `01 41 f2` y `0x21` para `f2 01 41`; la selección PUSH/POP ocurre en Malbolge. El supervisor Python traduce A/B a paquetes predefinidos, valida la terminación y el protocolo de un byte, elimina el LF añadido por el runner, y reenvía el byte sin computar ni sustituir su valor. Después de reunir las respuestas, alimenta el almacén de una vez.

## Medidas y controles

- 18 selecciones positivas, una por solicitud, con comparación salida/pasos entre oráculo y runner C. Traza Python adicional comprueba la ruta de entrada y visita al despachador común 34.
- Tres ejecuciones del almacén positivo: la salida coincide con el lote, los dos motores coinciden en bytes/pasos y la traza instrumentada verifica que `stack_scratch`/`stack_top` son C1 al inicio de cada solicitud y que `stack_top` contiene exactamente el byte tanto tras la escritura como al emitirlo.
- Control negativo del selector: sustituye el JMP inicial por NOP; las solicitudes A y B agotan el presupuesto y el puente las rechaza; ambos motores coinciden en resultado observable. El runner C devuelve código de proceso 0 incluso con TIMEOUT: se valida el estado, no solo el exit code.
- Control negativo del almacén: altera la transición para almacenar C1; emite `0x54` por solicitud y se observa 29524 en memoria. Para estos protocolos la salida incorrecta es diferente de la entrada.
- `stream_probe.py`: tras cada uno de dos bytes no se observó salida durante 1 segundo con `stdbuf -o0`; al cerrar stdin apareció `68 21 0a`. **No se ha demostrado por qué** no hubo salida; esto limita esta integración con este runner a un puente por lote. La observación no prueba que sea imposible el streaming con otro runner.

## No demostrado

No es un resolvedor PureEpoch integrado: no se llama/importa PureEpoch durante el experimento, no se busca o sintetiza una transición en ejecución y no se verifica una llamada/retorno general entre los dos componentes. El «retorno» es al despachador común del selector y a la siguiente entrada del almacén; el host coordina procesos separados. El selector reinicia para cada solicitud; no se ha mostrado selector rearmable en una sola VM. No es una operación de escritura a dirección arbitraria ni soporte general de palabras de 10 trits. El almacén se comprueba para dos bytes elegidos por el selector, no para todas las posibles estrategias o valores. La traza de memoria es Python instrumentado; el runner C se contrasta externamente, no expone memoria.

## Reproducir

Desde raíz: `python3 vm_malbolge/evidence/epoch_hybrid_resolver_v0/probe.py` y `python3 vm_malbolge/evidence/epoch_hybrid_resolver_v0/stream_probe.py`. El primer comando sobrescribe `results.json`: para conservar la evidencia original usar una copia del pack. Los artefactos de las pruebas previas se leen de sus rutas y se identifican por SHA-256 en `results.json`.

# Composición parcial: despacho y retorno

## Hipótesis
Un despacho determinado en runtime puede elegir dos transiciones y ambas pueden retornar a un punto común para procesar una segunda solicitud, sin intervención del host. Esta prueba instrumenta la imagen `mbir_dispatch2.mb` ya existente: **no constituye un resolvedor PureEpoch nuevo**.

H1: para 4 secuencias (PUSH A/POP, POP/PUSH A, PUSH B/POP y PUSH A/PUSH B), los dos motores coinciden, el primer salto alcanza su ruta y después se visita la dirección 34, el segundo despacho; la celda 46 se observa en la traza. H0: al menos una de estas condiciones falla.

Resultado: CONDITIONAL_PASS 4/4; un mutante sustituye el JMP inicial en la dirección 6 por NOP y el contrato rechaza las cuatro secuencias, con paridad de motores. La imagen se detiene tras la segunda instrucción: el «retorno» verificado es al **despacho compartido 34**, no al llamador arbitrario ni a una siguiente época ilimitada.

Limitaciones: PUSH guarda `crazy(byte,33)`, no el valor exacto; POP devuelve ese valor transformado. Las entradas eligen dos **operaciones** (PUSH/POP), no dos algoritmos de construcción de valores. 11 celdas de dato no pasan el loader estricto (véase `dispatch2.md`). Las trazas son una implementación Python instrumentada que coteja pasos y salida con el oráculo; el runner C solo verifica salida/estado observable. No se ha integrado PureEpoch ni conectado esta selección al almacén exacto reutilizable v1: el objetivo de un resolvedor con selección de transiciones y retorno general sigue **NOT_DEMONSTRATED**.

Reproducción: `python3 vm_malbolge/evidence/epoch_resolver_dispatch_v0/probe.py`. El script reescribe `mutant.mb` y `results.json`; para preservar evidencia usar una copia del pack.

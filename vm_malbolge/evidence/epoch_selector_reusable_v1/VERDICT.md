# Selector reutilizable de dos valores — experimento v1

## Pregunta y resultado

H1: una imagen Malbolge Classic recibe una secuencia de peticiones codificadas 01 y 02, selecciona en runtime una de dos ramas, emite respectivamente 50 y 52, restaura su estado relevante y regresa al mismo punto de entrada para repetir. H0: alguna entrada o control falla.

**CONDITIONAL_PASS, dominio binario {01,02}:** nueve flujos (vacío, ambos bytes individuales, 010201, 020102, ocho repeticiones de cada rama, dieciséis alternancias y 128 peticiones pseudoaleatorias con semilla 20261107). Salida y pasos concuerdan entre `oracle_classic.py` (`stop_on_eof=True`) y `runners/malbolge-original/malbolge`; el primero denomina EOF a la parada y el segundo HALTED. En cada IN y OUT la traza Python observa `marker_01=80` y `marker_02=82`; observa que cada petición usa solo su rama correspondiente y ejecuta diez ROT sobre el marcador de esa rama antes de emitir. El evento de rama se registra diez veces porque el bucle de rotaciones vuelve al mismo bloque de despacho; no son diez solicitudes de entrada.

Los valores de las cuatro etiquetas `MOVED`, `MARK_FLAG`, `MARK5` y `MARK2` coinciden al comienzo de cada vuelta medida, y el mismo PC de IN reaparece. **No se afirma identidad de memoria completa:** `NO_MORE_CARRY_FLAG` y `CARRY` varían. La traza instrumentada replica la semántica Python y no constituye un tercer motor de memoria independiente.

## Construcción y controles

La variante previa `rearm_moved` añade `R_MOVED` antes del salto de retorno desde las ramas, eliminando la caída accidental en la rama contigua, pero deja la constante del marcador rotada: para `010101` produce `50 e0 10`, no `50 50 50`, en ambos motores. Este es un control negativo conservado en el pack.

El candidato `marker_loop4` conserva el rearme de `MOVED`. Para las rutas 01 y 02 usa una celda dedicada (`marker_01='P'`, `marker_02='R'`) y una rutina `U_ROT` con `MARK_FLAG`, `MARK5` y `MARK2` que rota la misma celda 10 veces; al final del ciclo `rot^10` devuelve el marcador, con su valor exacto en el acumulador para OUT. El bucle repara `MOVED` también antes de cada salto a la rutina de rotación. Tras OUT regresa a `next_char_rearm`, que vuelve a preparar los datos antes de IN.

El mutante sustituye `MARK5 marker_01_five` por `MOVED marker_01_done`, saltándose el ciclo completo para la rama 01: para entrada `01`, los dos motores emiten `e0`, no `50`; para `02` ambos conservan `52` (control de especificidad). Para `010201`, el mutante hace que Python y C diverjan tras la primera salida; no se interpreta la ejecución Python posterior como equivalente al runner C. Esta divergencia es compatible con la diferencia de manejo de instrucciones no imprimibles documentada en `epoch_selector_divergence_v1`, pero no se ha trazado su punto exacto para este mutante.

El primer `probe.py` exigió una única visita a la etiqueta de rama y falló pese a salida correcta: la traza mostró diez visitas por la rutina de 10 rotaciones. Se conservan `first_attempt.raw.txt` y `first_attempt.json`; el predicado se corrigió para exigir las diez visitas y verificar además diez ROT sobre el mismo marcador. Esto documenta un error del harness, no un PASS anterior.

## Loader, reproducción y límites

Validación estática: las celdas fuente de la imagen positiva, tras quitar whitespace, son imprimibles y decodifican a opcodes válidos: 0 inválidas. No se ejecutó un loader estricto independiente. El archivo `.mb` y el mutante son instancias compiladas por LMAO, con hashes identificados en `results.json`; no se asume que LMAO sea byte-determinista.

`build.py <directorio-nuevo>` reconstruye ambas fuentes a partir de `epoch_selector_rearm_v0/rearmed2.hell` y las ensambla. Se verificó que las fuentes reconstruidas son idénticas y que el nuevo binario emite `505250` para 010201; ver `rebuild.raw.txt`. `probe.py` reproduce las pruebas sobre las instancias conservadas, pero sobrescribe `results.json`: usar una copia del pack para preservar la evidencia.

**NOT_DEMONSTRATED:** este selector no implementa el resolvedor general PureEpoch, no sintetiza/busca transiciones en ejecución, no guarda los resultados en una dirección dinámica ni está conectado al almacén exacto de la prueba anterior. El contrato se limita a bytes 01/02; el comportamiento de otras rutas heredadas no se valida. El `MOVED next_char_rearm` vuelve al selector, no demuestra una ABI de llamada/retorno general ni memoria totalmente restaurada.

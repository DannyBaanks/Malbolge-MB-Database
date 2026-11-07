# Experimento exploratorio v1: journal y fase después de restaurar

Se conserva esta primera construcción, donde la selección de fase ocurre **después** de restaurar la celda. Ambos motores coinciden en los nueve flujos y la traza comprueba journal, restauración y alternancia; `mutant_journal` y `mutant_phase` se rechazan. No se reivindica selección de la ruta antes de restaurar. El experimento posterior `epoch_journal_state_v2` desplaza la selección de fase antes de la restauración e incorpora un tercer control negativo.

Se preservan los dos fallos iniciales del harness: `first_attempt.raw.txt` contiene un error de comillas de Python; `second_attempt.raw.txt` y `second_attempt.json` contienen una comprobación que suponía erróneamente que la fase inicial debía ser 70. Al reubicar el código, el valor inicial de la imagen observada es 74: se corrigió el harness para determinar la fase inicial real y exigir alternancia 70↔74. No se modificaron las imágenes para convertir resultados fallidos en éxito. Esta corrección se limita a la instrumentación, no prueba que el selector general exista.

`probe.py` sobrescribe `results.json`; conservar el original copiando el pack antes de repetir. Fuente de la construcción: `journal.hell`; es una adaptación HeLL de la identidad del journal M1b de PureEpoch, no una copia binaria enlazada de M1b. La fuente y las tres imágenes se conservan para inspección, con hashes en el manifiesto.

## Integridad y redacción de ruta

`first_attempt.raw.txt` es una copia con el prefijo local reemplazado por `<REPO>/`. El original sin modificar se conserva en el archivo privado local de evidencia, identificado por SHA-256 `891cd75010647d06e66d390105281a11b783c1faf52576655724bdb7469e3ccc`. La redacción afecta únicamente a la ruta del traceback; no modifica el error ni el resultado.

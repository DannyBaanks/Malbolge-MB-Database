# Puertas preregistradas: incremento de bytes en runtime

2026-11-11. Base `eae037d`. Objetivo: imagen Malbolge Classic estricta que lee bytes arbitrarios, emite `(byte + 1) % 256` por cada lectura y hace HALT autónomo al EOF de Olmstead, sin bytes extra ni asistencia del host.

G0: referencias Python y BF genuino, 16 bits modulares con EOF=65535, se comparan en vacío, NUL, FF, todos los bytes, flujos variables y 10 000 bytes, más control mutado. G1: imagen Malbolge strict-loader aceptada y transformación realizada dentro de la imagen: 256 bytes individuales y vectores de longitud variable, incluyendo `00→01`, `ff→00`; medir también EOF y estados/controles. G2: evidencia REA con semántica `olmstead_1998`, contrastada con Olmstead nativo y cobertura explícita. G3: dos lecturas o más deben transformarse en una sola ejecución sin resembrar memoria desde el host; probar 10 000 bytes. G4: compilación BF→Malbolge sólo si el compilador comprueba el patrón y emite imagen cuya conducta se verifica; ninguna afirmación de compilador BF general.

Se permite registrar resultados parciales y negativos. Una función Python que fabrique el output o código fijo no demuestra cálculo Malbolge. Registrar hashes, comandos, resultados crudos, límites y controles; no sobrescribir evidencia anterior. Verificar orientación CRAZY antes de usar álgebra.

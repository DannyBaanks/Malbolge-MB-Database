# Cierre del analisis del hueco (2026-11-07)

## Las tres medidas que lo cierran

**1. El almacenamiento funciona.** crazy(A, C) con C=85 distingue 10/10 digitos.
El hueco de la prueba es real: el operando del CRAZY puede depender de la entrada.

**2. La combinacion colapsa.** crazy(B, crazy(A,C)) da solo 23-28 pares distintos
de 100. Y cada etapa adicional reduce la informacion, no la aumenta:
  crazy(B, almacenado)        -> 23-28/100
  + crazy(const 85)           -> 18/100
  + crazy(const 48)           -> 10/100
  + crazy(const 49)           -> 15/100

**3. La razon, medida trit a trit.** Descomponiendo crazy(A,85) en trits:
  trit 0: 3 valores distintos sobre los 10 digitos
  trit 1: 3 valores distintos
  trit 2: 2 valores distintos
  trit 3..9: 1 valor (no distingue nada)

Solo 3 de los 10 trits sobreviven con informacion. El partedependence es
equivalente a tener ~3 trits de estado sobre A.

## Conclusion

El hueco de la prueba esta cerrado. No es que la busqueda sea lenta: es que
la clase de funciones accesible con crazy dependiente de entrada NO tiene
capacidad de representar a<b sobre 100 pares. Hacen falta 100 valores
distintos y el sistema produce como maximo 28, ademas decreciendo con cada
etapa adicional.

Sumado a la prueba original (funciones separables), el resultado es:
NINGUNA cadena de operaciones Classic sobre dos operandos leidos de stdin
computa la comparacion. La regla se extiende de "separables" a
"separables + un crazy con operando almacenado".

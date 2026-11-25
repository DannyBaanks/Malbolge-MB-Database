# P7 — preregistro de dos variables, 2026-11-24

Base: P6 (26a9030). Hipótesis: el mismo sitio crazy y la bandera de retorno se pueden compartir entre dos variables persistentes V=41000 y W=43000, sin copiar el cuerpo de operación.

- G0: imagen imprimible Classic, un único sitio crazy de trabajo; dos variables distintas e inicializadas (12345 y 23456).
- G1: tres vueltas A(V) → B(W), misma imagen, seis llamadas y retornos A B A B A B; las continuaciones seleccionan la siguiente variable.
- G2: cada llamada escribe exactamente crazy(a, valor anterior) en la variable elegida; la otra conserva su valor antes/después. Vigilar cualquier modificación de ambas celdas durante toda la fase de trabajo; todas deben proceder del mismo pc crazy. Estado persistente, sin reinicializar variables entre vueltas.
- G3: bandera y sitio vuelven a 74 en las cuatro visitas al reloj. Colas JMP intactas.
- G4: controles: redirigir el segundo llamador a V deja W intacta; redirigir el primero a W deja V intacta. Ambos mantienen seis llamadas y retornos A/B, pero deben fallar el contrato de selección V,W alternada. Un caso adicional invierte las dos selecciones W,V y verifica el contrato invertido.
- G5: salidas y parada coinciden en Olmstead, clasesbolge, trazador local y REA; eventos REA confirman selección y retornos. Dos generaciones idénticas byte a byte.

Fuera de alcance: dirección de variable elegida por stdin, más variables, ejecución ilimitada, llamadas anidadas, pila general. Compartir operación no implica compartir/acoplar los valores: el acumulador sí transporta el resultado de una llamada a la siguiente.

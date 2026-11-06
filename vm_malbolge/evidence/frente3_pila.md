# Frente 3 — pila de profundidad > 2

## Veredicto: FALLA en profundidad 2 (no es un muro de presupuesto)

Sonda: `vm_malbolge/tools/stack_depth_probe.py` sobre `mbir_m2_loader.mb`
(40.310 B), dual-engine.

| Vector | Entrada | Esperado (LIFO) | Oráculo | Runner | Veredicto |
|---|---|---|---|---|---|
| profundidad 1 | `01 41 10 00` | `41` | `41` | `41` | **PASS** |
| profundidad 2 | `01 41 01 42 02 10 00` | `4241` | `41` | `41` | FALLO |
| profundidad 3 | `01 01 01 02 01 03 10 10 10 00` | `030201` | `01` | `01` | FALLO |
| profundidad 4 | `…01 04 10×4` | `04030201` | `01` | `01` | FALLO |
| profundidad 5 | `…01 05 10×5` | `0504030201` | `01` | `01` | FALLO |

Barrido de profundidad: **solo la 1 pasa**; de la 2 en adelante ambos motores
emiten exactamente un byte y detienen.

## Lo que significa

Los dos motores **coinciden en todos los casos** — no es divergencia de
implementación. La imagen simplemente no itera: tras el primer `OUT` se detiene
en lugar de volver al bucle de despacho para el segundo `PUSH`/`OUT`.

## Diferencia con el frente 1

El frente 1 midió que la imagen nativa del emisor **sí** itera (tres fetch con
`"35"`). La del cargador no. O sea: el bucle de vuelta al despacho es la
primitiva que falta, y ya está demostrada en otra imagen de este repo — no hace
falta inventarla, hay que trasplantarla.

## Coste medido del trasplante

El frente 2 midió que injertar la maquinaria del emisor sobre el andamio del
cargador cuesta **657 B** y deja 18.082 B de margen, con las 4 vectores M2
intactas. El bucle de retorno es una fracción de eso.

## Conclusión del frente

Sin bloqueante de presupuesto. El obstáculo es la ausencia del salto de retorno
al despacho, primitiva ya existente y medida en el frente 1.

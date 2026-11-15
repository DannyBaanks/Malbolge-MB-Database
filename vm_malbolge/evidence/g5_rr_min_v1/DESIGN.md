# Diseño: R/R2 de una celda + rearme lineal

## Por qué no islas v4 mutuas

Si cada isla tiene I=19 celdas de código y R tiene n_r islas para restaurar
R2+B, entonces |código R|=19 n_r y R2 necesita ≥19 n_r islas ⇒
n_r ≥ 19 n_r + |B| — imposible. Por eso `G5_DESIGN.md` con islas v4 mutuas
no escala; `g5_same_t_v1` además choca trampolines adyacentes (T+1/T+2).

## Brick mínimo

- R y R2: una celda cada una (JMP), alejadas del cuerpo.
- Rearme con sled lineal `op_at` (MOVD/CRAZY/ROT) sobre esa única celda —
  no toca vecinos de trampolines v4.
- Primitivas compartidas 74↔70 opcionales; el sled privado basta.
- HCLOCK pc≡2 valor 66 para HALT tras 2 ciclos.

Flujo:

```
R (cifra) → sled restaura R2 → R2 (cifra) → sled restaura R → HCLOCK → R …
```

Hasta que HCLOCK hace HALT.

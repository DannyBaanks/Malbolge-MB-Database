# Diseño: rearme auxiliar + segunda invocación

2026-11-12. Pack `shared_restore_two_v1`. Documento de implementación;
**ninguna imagen de este pack está demostrada todavía**. Base medida:
`shared_restore_one_v1` @ `4172c2e`.

## Hechos ya medidos (one_v1)

- Primitivas compartidas en PC 58057/58152/58268 (`74↔70`) vuelven a 74 al
  HALT; no son el obstáculo para una segunda llamada.
- Reloj en PC 58303, valor inicial 117, órbita bajo xlat2:
  `117→111→120→58→37→103→(117)`. Opcodes en ese PC:
  `46 NOP, 40 MOVD, 49 NOP, 81 HALT, …`.
- Tras la restauración exitosa de T, la cuarta visita al reloj **es** HALT.
  Por eso one_v1 no puede reentrarse: el despachador se autodestruye hacia
  parada, no por fallo de las primitivas.
- Constante C=57200 parte en `120 = rot^9(40)` y tras un ROT queda en 40
  (`ctrl` del objetivo 40).
- Cadena uniforme de reinicio (`code_rearm_multi_v1` / `algebraic_restart`):
  `e --crazy(ONE)--> x --crazy(x,x)--> 29524 --crazy(ctrl)--> want` con
  `ctrl=crazy(want,ONE)`.

## Álgebra comprobada en host (esta sesión, aún no nativa)

| Celda | e actual | want | ctrl | ¿cadena restaura? |
| --- | --- | --- | --- | --- |
| Reloj 58303 | 58 | 117 | 29407 | sí |
| Constante 57200 | 40 | 120 | 29404 | sí |
| Constante 57200 | 40 | 120 | (9× ROT) | sí (orden 10) |

Orientación: `crazy(acumulador, celda)` como en `verify_v2.py` / paridad
BolgeForge.

## Flujo propuesto

```
call1 (T1): fases reloj 0,1,2 + cuerpo shared → T1=40; reloj queda 58; C=40
            (no visitar reloj en fase 3 / HALT)
rearm:      cadena uniforme → reloj 58→117; C 40→120
            (reutilizar ROT/MOVD/CRAZY compartidas + celdas de control propias
             C_clock / C_const, o 9×ROT sobre C)
call2 (T2): misma composición sobre isla de trampolines de T2 → T2=40
            fase 3 del reloj → HALT
```

Desvío clave respecto a one_v1: la celda **T+3 = 57103** guarda `CLOCK-1`
(58302). Tras cada par CRAZY/NOP, el JMP sale con `d=57103` y cae en el
reloj (el +1 post-JMP convierte CLOCK-1 → CLOCK). Las cuatro vueltas usan
la misma celda; por eso hay que **reescribir 57103 después de la tercera
vuelta al reloj** (ventana scratch ~3338–3346) para que la cuarta vaya al
rearme y no a HALT. `algebra_check.py` confirma además que en este `CLOCK`
no existe valor imprimible con dos MOVD antes de HALT: no se pueden meter
dos despachos en una sola órbita xlat2.

## Por qué esto es el ladrillo G5

G5 pide R/R2 reentrables. one_v1 demostró el cuerpo compartido sobre una
celda. Este pack debe demostrar que el **estado auxiliar del despacho**
también se puede devolver y que la composición admite **dos entradas reales**
en la misma corrida. Sin eso, R↔R2 no cierra.

## Verificación prevista

1. Scratch propio (mismo motor que `verify_v2.py`) con visitas a T1, reloj, C,
   T2 y escrituras.
2. REA `event_start_step` tardío; ventana = scratch hasta HALT.
3. Olmstead: rc=0, stdout vacío; evidencia de celdas solo por trazas.
4. Control: corromper ctrl del rearme del reloj o de C → segundo objetivo ≠40.
5. Síntesis aislada + hashes; no escribir sobre `shared_restore_one_v1`.

## Estado de implementación (2026-11-12)

**PASS nativo.** Call2 usa CLOCK2 (58397) y C2 (57420) en lugar de rearmar el
reloj/constante de call1. STORE es solo JMP a S2. Verificado: T1=T2=40,
control 39/39, HALT en CLOCK2, Olmstead rc=0.

## Fuera de alcance (NOT_DEMONSTRATED aunque este pack pase)

- Ventana REA call1→call2.
- N≥3 invocaciones / bucle G5 con R y R2.
- Objetivos distintos de 40 o con trit 2 en la ruta `crazy(q,q)`.
- EOF / incremento de longitud arbitraria.
- Rearme in-place del mismo reloj (el pack evita ese problema con CLOCK2).

# Pila de profundidad 2 (LIFO) sobre flujo de bytes — frente 3, vía one-shot

## Resultado

`vm_malbolge/tools/stack2_oneshot_gen.py` emite `mbir_stack2_oneshot.mb`
(160 bytes, **sin LMAO**) que lee dos bytes de stdin, los almacena en dos celdas
de pila y los emite **en orden inverso**:

| stdin | salida | significado |
|---|---|---|
| `AB` | `63 68` | `[crazy(0x42,V0B), crazy(0x41,V0A)]` — el segundo byte sale primero |
| `BA` | `67 69` | `[crazy(0x41,V0B), crazy(0x42,V0A)]` — el orden se invierte con la entrada |
| `0102` | `55 56` | LIFO con operandos binarios |
| `7879` | `db e2` | idem |
| `A` | (vacío) | EOF tras el primer byte: parada limpia en los dos motores |
| (vacío) | (vacío) | idem |
| `ABC` | `63 68` | profundidad 2: el tercer byte no se consume |

**8/8 acuerdo byte a byte** entre `oracle_classic.py` (`stop_on_eof=True`) y
`runners/malbolge-original/malbolge`, 32 pasos, HALTED. Evidencia máquina:
`vm_malbolge/evidence/stack2_oneshot.json`.

Loader estricto **completo**: todas las celdas de código y todas las de dato
(el emisor lo verifica una a una con `valid_cell`).

## Arquitectura: por qué one-shot y no bucle

Un programa one-shot no paga la primitiva de restauración (cada celda se ejecuta
una sola vez), así que sus celdas de trabajo pueden estar en **cualquier**
dirección y no hay pares de punteros que colisionen. El flujo es una línea recta
de celdas consecutivas; el puntero de datos se gobierna con celdas-puntero
imprimibles colocadas en el camino de `d`, y sus direcciones se obtienen
**simulando** el flujo de `(c, d)` (`layout()`), no derivándolas a mano.

Diseño (k, pad1..3 = NOPs de relleno que la búsqueda elige):

```
k:          MOVD  d = V(k)                     (V(k)=((7-k) mod 94)+33, valor propio)
k+1:        IN    a = byte1
k+2+pad1:   MOVD  d = mem[pf1] = slotA-1
k+3+pad1:   CRAZY mem[slotA] = crazy(a, mem[slotA])        PUSH 1
k+4+pad1:   IN    a = byte2
k+5+pad1+pad2: MOVD d = mem[pf2] = slotB-1
k+6:        CRAZY mem[slotB] = crazy(a, mem[slotB])        PUSH 2
k+7:        OUT   emite a & 256 = mem[slotB]               POP cima (exacto, sale de a)
k+8+pad3:   MOVD  d = mem[pf3] = slotA
k+9..k+28:  10 x (MOVD, ROT)  a = rot^10(mem[slotA])       POP fondo (exacto)
k+29:       OUT   emite a & 256 = mem[slotA]
k+30:       HALT
```

Las 10 rotaciones son necesarias porque `ROT` rota un trit: `rot^10` es la
identidad, y cada `ROT` va precedido de un `MOVD` que devuelve `d` a la celda de
pila (la celda-puntero `slotA+1` contiene `slotA-1` y sirve para las 10 vueltas).
Así la lectura es **exacta**, no una aproximación.

## Lo que queda bloqueado, y la prueba

El frente pedía la pila sobre el **bucle** iterante. Eso sigue bloqueado, y ahora
con causa probada, no supuesta:

1. Toda celda ejecutada se cifra tras la instrucción. `XLAT2` tiene ciclos
   mezclados y **solo 70 y 74 forman un 2-ciclo** (medido: 2 valores de 94;
   0 puntos fijos). Un bucle necesita `ENC(ENC(v)) == v` ⇒ **2 direcciones
   utilizables por opcode dentro de una ventana de 94**: MOVD 60/64, IN 43/47,
   ROT 59/63, CRAZY 82/86, OUT 119/123, NOP 88/92. Doce celdas de trabajo en
   total para `[33,126]`.
2. Dos instrucciones que dejan `d` en la **misma** celda comparten sus celdas de
   puntero `(S+1, S+2)`, y los valores que necesitan no pueden coincidir. El
   `CRAZY` (escritura) y el `ROT` (lectura) de una celda de pila dejan ambos
   `d = S`. **Una celda no puede escribirse y leerse en el mismo ciclo.**
3. El valor no puede viajar en `a` entre fases porque cada `IN` lo sobrescribe.

Conclusión: dentro de la primitiva de restauración por 2-ciclo, una pila con
lectura y escritura de la misma celda es **no construible**. Salidas posibles
(documentadas, no emprendidas): una celda-puntero escrita en tiempo de ejecución
(cuesta un `CRAZY` más una carga de constante) o el selector buscado al estilo de
BolgeForge (un paseo `j/*` que diverge sobre la celda modificada por `crazy`).

## Relación con los otros hitos

- `native_fold_loop.md`: el bucle de fetch con estado entre bytes (sí funciona,
  9/9 + 4 KiB) usa una celda que **solo se escribe** — justo lo que la regla (2)
  permite.
- `frentes3y5_bloqueante_CORRECCION.md`: el bloqueante declarado queda refutado.

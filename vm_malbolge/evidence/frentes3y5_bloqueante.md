# Frentes 3 y 5 — obstáculo localizado: el flujo de control es fijo

## Intento

Injertar la cadena de salto computado (verificada en
`mbir_native_cmp_decimal.mb`) sobre el andamio del cargador, vía `.OFFSET` en
región libre. Generador: `vm_malbolge/tools/computed_jump_graft.py`.

## Medidas

| Medida | Valor |
|---|---|
| Injerto ensambla | **SÍ** — 40.591 B, margen 18.458 B, +16 líneas |
| Cargador tras el injerto | **4/4 PASS** (41, 42, vacío, vacío) |
| Sonda de profundidad | **idéntica al cargador base**: profundidad 1 PASS, 2-5 FALLO |

El injerto es **pasivo**: las celdas existen y son válidas, pero el flujo de
control del cargador no las alcanza.

## Obstrucción real, medida

Instrumentación del cargador base (`mbir_m2_loader.mb`) con stdin `"AB"`:

```
IN ejecutadas: 2
primera lectura de cada byte: {'A': c=60, 'B': c=65}
pasos: 40034
```

**El cargador lee exactamente dos bytes y ejecuta una secuencia fija.** No hay
vuelta al despacho: no es un bucle con una dirección de retorno que se pueda
redirigir, es una cadena de instrucciones escrita celda a celda que termina.

## Por qué no se puede arreglar añadiendo datos

El flujo de control de Classic lo determina el **cableado del `.CODE`** — qué
celda se ejecuta tras cuál. Añadir celdas de dato (barato, medido: 64 caben) no
cambia el flujo. Cambiarlo exige:

1. Nuevas celdas de **código** (flags, saltos) → E3 midió que **4 flags nuevos
   ya revientan** el inicializador sobre estas imágenes.
2. O reescribir la cadena de código existente → es un rediseño del `.hell`, no
   un parche.

## Veredicto de los frentes 3 y 5

| Frente | Estado |
|---|---|
| 3 (pila > 2) | ❌ **bloqueado**: el flujo fijo del cargador no itera, y modificarlo exige flags de código que el presupuesto no admite |
| 5 (lexer, 2º token) | ❌ **bloqueado por la misma causa**: el probe añadió `R_MOVED` + `MOVED ENTRY`, que modifica el flujo, y ahi aparece la divergencia de EOF |

**Este sí es un bloqueante**, y es de los que el objetivo dice que hay que
reportar: no se resuelve con un parche de datos ni con una posición de
instrucción. Exige o bien un rediseño del `.hell` con flags reutilizados, o
bien construir la imagen desde el emisor nativo (que ya itera, medido en el
frente 1) en lugar de extender el cargador de LMAO.

## Camino que sí queda abierto

El frente 1 midió que `mbir_native_cmp_decimal.mb` **ya itera** (3 fetch con
`"35"`) y que su cadena de salto computado es reproducible. La ruta es
construir la pila profunda sobre **esa** imagen, no sobre el cargador.

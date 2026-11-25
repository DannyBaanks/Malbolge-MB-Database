# Compilar Python literal a Malbolge Classic

```bash
cd '/home/danny/Development/ISyCo Git/MALBOLGE-MB-DATABASE'
d=$(mktemp -d /tmp/classic62-demo.XXXXXX)
python3 -B python/src/classic_compiler.py python/examples/saludar.py -o "$d/saludar.mb" --map "$d/saludar.json" --run
```

Salida real (el directorio temporal cambia cada vez):

```text
Compilado: /tmp/classic62-demo.Xd8lzg/saludar.mb (39932 bytes; 1 instancias de llamada)
Hola
```

**Regla de oro:** usa una ruta de salida nueva. No se ejecuta el Python de entrada; el compilador analiza su AST. El `.mb` resultante corre directamente en un intérprete Classic, sin Python, MBIR ni un runtime del compilador durante la ejecución.

## Más ejemplos

```bash
d=$(mktemp -d /tmp/classic62-examples.XXXXXX)
python3 -B python/src/classic_compiler.py python/examples/repetir.py -o "$d/repetir.mb" --map "$d/repetir.json" --run
```

```text
Compilado: /tmp/classic62-examples.4XHT92/repetir.mb (39932 bytes; 2 instancias de llamada)
Hola
Hola
```

```bash
python3 -B python/src/classic_compiler.py python/examples/anidada.py -o "$d/anidada.mb" --map "$d/anidada.json" --run
```

```text
Compilado: /tmp/classic62-examples.4XHT92/anidada.mb (39932 bytes; 4 instancias de llamada)
Inicio
¡Hola 🌎! Fin
Inicio
¡Hola 🌎! Fin
```

| Resultado | Significado / acción |
|---|---|
| `Compilado` y salida esperada | Imagen generada y, con `--run`, ejecutada con Olmstead. |
| `archivo.py:línea:columna: error` | Fuente fuera del subconjunto o inválida; corrige lo indicado. |
| `la salida ya existe` | No se reemplazó el archivo. Elige otro nombre. |
| `el programa supera...` | Límite de expansión o layout; reduce el programa. |
| `imagen guardada; no se encontró Olmstead` | El archivo ya existe; usa un intérprete Classic instalado. |

## Límites y trampas

- El compilador está escrito en Python; el código generado es Malbolge Classic puro. No es un compilador alojado en Malbolge.
- Admite funciones sin argumentos, `print` de cadenas literales (`sep`/`end` literales), llamadas directas repetidas/anidadas, `pass`, docstrings y `return` sin valor. UTF-8. No admite variables, bucles, recursión, despacho dinámico ni retorno de valores.
- Cada llamada tiene una instancia física de código de un solo uso; las instrucciones se cifran al ejecutarse. El retorno numérico sí es real y las llamadas internas preservan el retorno exterior.
- Topes del frontend: 64 KiB de fuente UTF-8, 256 bytes de salida expandida, 32 instancias y profundidad 16. El layout físico puede rechazar programas antes de estos topes.
- Para compilar necesita BolgeForge al lado del repositorio (o `BOLGEFORGE_ROOT`). Para `--run`, necesita Olmstead al lado del repositorio (o `--runner`). Para ejecutar la imagen ya compilada solo hace falta un intérprete Classic.
- Omite `--run` si solo quieres generar una imagen. `--map` es opcional y registra los PCs, slots e instancias.
- La imagen y el mapa se crean de forma exclusiva, no como transacción atómica conjunta; un error de E/S posterior puede dejar la imagen creada.

Evidencia reproducible: [classic_compiler_v0](evidence/classic_compiler_v0/VERDICT.md).

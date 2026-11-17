# Malbolge MB Database v2.0 — Base de Datos Reproducible y Laboratorio MBIR

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/DannyBaanks/Malbolge-MB-Database)
[![Quine Record](https://img.shields.io/badge/record-53562%20bytes%20quine-brightgreen.svg)]()
[![MBIR](https://img.shields.io/badge/IR-MBIR%20v0%20(18%20opcodes)-blueviolet.svg)]()

Base de datos reproducible y laboratorio de investigación para programas Malbolge sustanciales, runtimes de lenguajes de alto nivel alojados sobre Malbolge, y el middleware **MBIR** (*Malbolge Bytecode Intermediate Representation*) que conecta frontends con substratos de ejecución.

Núcleo de almacenamiento y catálogo de la **Suite de Datos y Runtimes v2.0** del ecosistema Malbolge de ISyCo.

## Resultado destacado

[UNIECO](MALBOLGE_CAPABILITIES.md#unieco-eco-binario-con-eof-y-relocalizacion) ejecuta un eco binario con EOF en una imagen Classic de 33 822 bytes; su alcance medido y sus controles están descritos en capacidades.

## Guías

| Tema | Documento |
|---|---|
| Arquitectura, límites y estructura | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Estado medido y registro de quine | [STATUS.md](STATUS.md) |
| Malbolge, MBIR y las pruebas G5b P2–P5 | [MALBOLGE_CAPABILITIES.md](MALBOLGE_CAPABILITIES.md) |
| PureEpoch | [PUREEPOCH.md](PUREEPOCH.md) |
| Hoja de ruta y pistas de lenguaje | [ROADMAP.md](ROADMAP.md) |
| Comandos de reproducción | [REPRODUCING.md](REPRODUCING.md) |

## Recursos

- [Base de datos y catálogo](DATABASE.md)
- [Quine récord: 53 562 bytes](quine/README.md)
- [Evidencia G5b P2: cuatro llamadores secuenciales](vm_malbolge/evidence/g5b_flag_return_v2/VERDICT.md)
- [Evidencia G5b P3: orden cruzado de cuatro llamadores](vm_malbolge/evidence/g5b_flag_return_v3/VERDICT.md)
- [Evidencia G5b P4: las 24 permutaciones](vm_malbolge/evidence/g5b_flag_return_v4/VERDICT.md)
- [Evidencia G5b P5: cinco llamadores](vm_malbolge/evidence/g5b_flag_return_v5/VERDICT.md)

Este índice enlaza la información por tema. Las capacidades, los estados y los límites permanecen en sus documentos específicos para que cada afirmación se lea junto a su evidencia.

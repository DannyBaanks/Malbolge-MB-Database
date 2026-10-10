# Milestone M2 + ALU + CMP — one image

## Status: NOT_DEMONSTRATED

No binary in this repo loads a program into RAM and also runs the 14 streaming ALU vectors and `CMP_EQ`.

The streaming ALU (`vm_malbolge/src/mbir_alu.mb`, 54,691 bytes) already uses the initializer's room. A probe copied `vm_malbolge/src/mbir_alu.hell` and added 12 `Nop/MovD` flags plus 8 scratch cells (`U_CRAZY`, `C1`, and three flag triples each). LMAO 0.6.0 refused it:

```
Error: Free space exceeded (Add Malbolge command).
Internal error: Cannot generate initialization code for cell 57855.
Error: Memory usage conflict while generating initialization code.
```

Fifteen bare `C1` cells on the same hell did assemble, and the file stayed 54,691 bytes. The limit that failed is the initializer, on flag cycles and address triples, which a RAM loader and a `CMP_EQ` path both need.

The M2 ALU image had already rejected a 15-cell addition. This probe does not replace that result. It shows the streaming image cannot absorb a loader-sized block either.

Stack depth greater than 2, `CMP_LT`, `CMP_GT`, and the language frontends were not started.

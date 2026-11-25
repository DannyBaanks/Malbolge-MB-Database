# Python literal-functions → autonomous Classic v0

User intent: turn the manually lowered saludar example into an actual compiler. Interpretation for this iteration: compiler runs on Python; generated code runs entirely on Classic Malbolge. A compiler itself hosted in Malbolge is out of scope.

Approaches: reuse MBIR frontend/runtime (existing frontend is broader but execution on Classic is incomplete); execute Python and compile its output (rejected: erases calls and executes user code); lower an AST subset directly using P13/P14 numeric returns (selected implementation choice, closest to demonstrated mechanism).

Subset: module-level functions with no parameters/decorators/annotations; literal-string print calls with literal sep/end; direct statement calls, pass, function docstrings and bare return. UTF-8 output. Calls may repeat and nest, acyclic and statically resolved. Functions must be defined by their invocation in module execution order. Unsupported syntax gets a source-position diagnostic. Compiler never evals/execs user code.

Each call receives a specialized body instance. Actual native CALL/JMP and numeric RET remain; repeated calls do not reexecute encrypted instruction cells. Slots/journals are allocated by static call depth and reused after reset. This is finite specialization, not recursion, loops, dynamic call dispatch or a general Python implementation. Maps must expose instances and call/return PCs.

Backend: independent production emitter based on the verified numeric-return protocol; no imports of experiment probes. Bootstrap uses existing BolgeForge resynthesis plus its strict Classic template. Sparse data-pointer headers and shared constant byte cells avoid quadratic initialization. ROT^10 reads preserve constants and return words; C1=29524 resets slot/journal. Main HALT precedes body instances physically; control reaches a function only through a call. Source length and preamble/code/data boundaries are checked.

Bounds: source 64 KiB, expanded output 256 UTF-8 bytes, 32 call instances, depth 16, plus actual Classic layout capacity. The compiler rejects oversized layouts before writing artifacts. Existing outputs are refused. CLI: python3 python/src/classic_compiler.py input.py -o output.mb [--map output.json] [--run]. Optional run uses Olmstead; output alone requires only a Classic interpreter.

Validation: compare generated programs to trusted CPython fixtures, Olmstead, clasesbolge and independent traces/REA; repeated and nested calls, empty bodies, early return, Unicode and module-order resolution. Reject unsupported syntax, recursive expansion, budget violations and overwrite attempts. Compile twice and compare bytes. Human guide commands run before documentation. Stop when this bounded compiler and evidence are complete; do not upgrade old MBIR frontend claims.

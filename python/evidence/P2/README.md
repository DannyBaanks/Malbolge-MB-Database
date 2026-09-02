# Python MB — P2 Evidence

## Status: FRONTEND_DEMONSTRATED

P2 is a **Python AST → MalPy bytecode frontend**.
Evidence kind: `FRONTEND` (host_language = Python).

It demonstrates:
- Python source → AST (via `ast.parse`) → MalPy bytecode → reference VM → output
- No eval/exec used in compilation
- Restricted subset: `print(<int> + <int>)`

It does NOT demonstrate:
- Execution on a Malbolge-hosted runtime (MALBOLGE_HOSTED_EXECUTION = NOT_DEMONSTRATED)

## Evidence Record

- `run_p2_compiler.json` — execution record (evidence_kind = FRONTEND)
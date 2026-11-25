"""Run the official greeting against the existing Classic differential harness."""

import importlib.util
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
spec = importlib.util.spec_from_file_location(
    "classic_smoke", PACK.parent / "classic_compiler_v0" / "smoke.py"
)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)
smoke.CORPUS = {
    "hola_tontos": (ROOT / "python/examples/hola_tontos.py").read_text(encoding="utf-8")
}

if __name__ == "__main__":
    smoke.main()

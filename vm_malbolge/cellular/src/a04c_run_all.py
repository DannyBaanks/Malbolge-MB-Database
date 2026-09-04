"""A04C experiment runner: WRITES evidence/ for every verified
case, fails loudly on any FAIL.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _hash(obj):
    s = json.dumps(obj, sort_keys=True, default=str).encode()
    return hashlib.sha256(s).hexdigest()


def main():
    import c4_value_transport
    import c5_control_advance
    import c6_composition

    results = {}

    t0 = time.time()
    c4 = c4_value_transport.experiment()
    ok_c4 = all(r["ok"] for r in c4)
    results["C4_VALUE_TRANSPORT"] = {
        "pass": ok_c4,
        "cases": c4,
        "hash": _hash(c4),
    }

    c5 = c5_control_advance.experiment()
    ok_c5 = c5["success"]
    results["C5_CONTROL_ADVANCE"] = {
        "pass": ok_c5,
        "detail": c5,
        "hash": _hash(c5),
    }

    # C6: composition (no special-case host tweaks between standalone and combined runs)
    import importlib
    c6 = importlib.import_module("c6_composition")
    va, na = c6.a_only(65, 4)
    nb, tb = c6.b_only(4)
    both = c6.combined(65, 4)
    ok_c6 = (
        va == 65
        and nb == 1
        and tb == [4]
        and both["data_count"] == na
        and both["token_count"] == nb
    )
    results["C6_COMPOSITION"] = {"pass": ok_c6, "detail": {
        "a_value": va, "a_count": na, "token_count": nb, "token_x": tb,
        "both_data_count": both["data_count"], "both_token_count": both["token_count"],
    }, "hash": _hash(both)}

    elapsed = time.time() - t0
    results["elapsed_seconds"] = round(elapsed, 3)

    evd = {"runs": results, "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    outdir = HERE.parent / "A04C" / "evidence"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "a04c_evidence.json").write_text(json.dumps(evd, indent=2))

    print(json.dumps({"total_seconds": round(elapsed, 3),
                      "C4": results["C4_VALUE_TRANSPORT"]["pass"],
                      "C5": results["C5_CONTROL_ADVANCE"]["pass"],
                      "C6": results["C6_COMPOSITION"]["pass"],
                      "evidence_dir": str(outdir)}, indent=2))
    not_ok = [k for k in ("C4_VALUE_TRANSPORT", "C5_CONTROL_ADVANCE", "C6_COMPOSITION") if not results[k]["pass"]]
    return 0 if not not_ok else 1


if __name__ == "__main__":
    sys.exit(main())

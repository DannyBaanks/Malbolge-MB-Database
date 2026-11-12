#!/usr/bin/env python3
"""Artefacto funcional UNIECO: una sola imagen, cargador estricto, eco binario
y halt limpio en EOF sin bytes extra.

La imagen verificada es una REFERENCIA ajena a este experimento:
Malbolge-PureEpoch/candidates/cat_real.mal (7 972 celdas), ya copiada como
reference_cat.mb en vm_malbolge/evidence/inout_loader_eof_v1. Se copia aqui
para que este pack sea autocontenido y se contrasta su hash contra el origen.

Este script NO demuestra la variante relocalizada (candidate.mb): demuestra el
requisito funcional de UNIECO sobre una imagen que el cargador de 1998 acepta.
Los controles separan la aceptacion del cargador, la semantica de EOF y el
framing del runner C.
"""
import base64, hashlib, importlib.util, json, pathlib, platform, re, shutil, subprocess, sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
SIB = ROOT / "vm_malbolge/evidence/inout_loader_eof_v1"
spec = importlib.util.spec_from_file_location(
    "compose", ROOT / "vm_malbolge/evidence/epoch_dload_compose_v1/probe.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
B = M.B
MAX = 30000000
WALL = 60
sha = lambda b: hashlib.sha256(b).hexdigest()

raw = P / "raw"
raw.mkdir(exist_ok=True)

# ------------------------------------------------------- imagen y su linaje
origin_mal = ROOT.parent / "Malbolge-PureEpoch/candidates/cat_real.mal"
sibling_mb = SIB / "reference_cat.mb"
image_path = P / "reference_cat_functional.mb"
shutil.copyfile(sibling_mb, image_path)
ref = image_path.read_bytes()
lineage = {
    "origin": "Malbolge-PureEpoch/candidates/cat_real.mal (repo hermano PureEpoch)",
    "origin_sha256": sha(origin_mal.read_bytes()) if origin_mal.exists() else None,
    "origin_exists": origin_mal.exists(),
    "sibling_pack_copy": "vm_malbolge/evidence/inout_loader_eof_v1/reference_cat.mb (este repo)",
    "sibling_sha256": sha(sibling_mb.read_bytes()),
    "copy_in_this_pack": "reference_cat_functional.mb (este pack)",
    "copy_sha256": sha(ref),
    "identical_to_sibling": sha(ref) == sha(sibling_mb.read_bytes()),
    "built_in_this_experiment": False,
    "note": "construccion de referencia de otro pack; aqui solo se re-verifica",
}

# --------------------------------------------------------- controles
valid = M.VALID
invalid_first = next(x for x in range(33, 127) if x % 94 not in valid)
bad_loader = bytes([invalid_first]) + ref[1:]
(P / "control_bad_loader.mb").write_bytes(bad_loader)
broken_eof = SIB / "reference_cat_bad_eof.mb"
have_broken = broken_eof.exists()

cases = {
    "empty": b"",
    "zero": b"\x00",
    "mixed": b"\x00\x0a\x80\xff",
    "all256": bytes(range(256)),
    "long10000": bytes((73 * i + 195) % 256 for i in range(10000)),
}
for name, data in cases.items():
    (raw / (name + ".input")).write_bytes(data)


def execute(argv, stdin, wall=WALL):
    try:
        r = subprocess.run(argv, input=stdin, capture_output=True, timeout=wall)
        return r.returncode, False, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        return None, True, e.stdout or b"", e.stderr or b""


def save(tag, stdout, stderr):
    (raw / (tag + ".stdout")).write_bytes(stdout)
    (raw / (tag + ".stderr")).write_bytes(stderr)
    return {"stdout_file": "raw/" + tag + ".stdout", "stdout_bytes": len(stdout),
            "stdout_sha256": sha(stdout), "stderr_file": "raw/" + tag + ".stderr",
            "stderr_sha256": sha(stderr)}


def native(tag, binpath, img, data, runner=False):
    cmd = [str(binpath), str(img)] + ([str(MAX)] if runner else [])
    rc, timed, stdout, stderr = execute(cmd, data)
    res = save(tag, stdout, stderr)
    match = re.search(rb"steps:\s*(\d+)\s*\|\s*status:\s*(\w+)", stderr) if runner else None
    res.update(rc=rc, timed_out=timed, stdout_equals_input=stdout == data,
               stdout_equals_input_plus_newline=stdout == data + b"\n",
               steps=int(match.group(1)) if match else None,
               status=match.group(2).decode() if match else None)
    return res


def worker(tag, kind, img, data):
    request = json.dumps({"engine": kind, "image": str(img),
                          "input": base64.b64encode(data).decode()}).encode()
    rc, timed, stdout, stderr = execute([sys.executable, "-I", str(P / "reference_functional.py"), "--worker"], request)
    out = b""
    parsed = None
    if rc == 0 and not timed:
        parsed = json.loads(stdout)
        out = base64.b64decode(parsed["out"])
    res = save(tag, out, stderr)
    res.update(rc=rc, timed_out=timed, stdout_equals_input=out == data,
               stdout_equals_input_plus_newline=out == data + b"\n",
               steps=parsed["steps"] if parsed else None,
               status=parsed["status"] if parsed else None)
    return res


if "--worker" in sys.argv:
    request = json.loads(sys.stdin.read())
    img = pathlib.Path(request["image"]).read_bytes()
    data = base64.b64decode(request["input"])
    kind = request["engine"]
    if kind == "scratch":
        r = M.SE.run(img, max_steps=MAX, stdin=data)
        out, steps, status = r["out"], r["steps"], r["status"]
    elif kind == "independent":
        ns = {}
        exec(compile(B.INDEP.read_text().split("def trits")[0], str(B.INDEP), "exec"), ns)
        r = ns["run"](list(img), list(data), maxs=MAX, guard=True)
        out, steps, status = r["out"], r["steps"], r["status"]
    elif kind in ("oracle_default", "oracle_stop"):
        r = M.O.oracle_run(request["image"], max_steps=MAX,
                           stdin_data=data.decode("latin1"),
                           stop_on_eof=(kind == "oracle_stop"))
        out, steps, status = r["output"].encode("latin1"), r["steps"], r["status"]
    print(json.dumps({"out": base64.b64encode(out).decode(), "steps": steps,
                      "status": status}))
    raise SystemExit(0)

report = {
    "purpose": "requisito funcional UNIECO sobre una imagen de referencia",
    "platform": platform.platform(),
    "wall_timeout_seconds": WALL,
    "step_limit": MAX,
    "lineage": lineage,
    "image": {"length": len(ref), "sha256": sha(ref),
              "valid_cells": sum((v + i) % 94 in valid for i, v in enumerate(ref)),
              "invalid_cells": sum((v + i) % 94 not in valid for i, v in enumerate(ref))},
    "inputs": {k: {"bytes": len(v), "sha256": sha(v)} for k, v in cases.items()},
    "runs": {},
    "controls": {},
}
print("image", report["image"], flush=True)

for name, data in cases.items():
    z = {"olmstead": native("ref_" + name + "_olmstead", B.OLMSTEAD, image_path, data),
         "runner_c": native("ref_" + name + "_runner", B.C_RUNNER, image_path, data, True)}
    for kind in ("scratch", "independent", "oracle_default", "oracle_stop"):
        z[kind] = worker("ref_" + name + "_" + kind, kind, image_path, data)
    report["runs"][name] = z
    print(name, {k: (v["status"], v["timed_out"], v["stdout_equals_input"],
                     v["stdout_equals_input_plus_newline"]) for k, v in z.items()},
          flush=True)

# controles: (1) cargador debe rechazar la celda alterada; (2) una ruta de EOF
# rota NO debe comportarse como un halt limpio
report["controls"]["bad_loader"] = native("ctrl_bad_loader", B.OLMSTEAD,
                                          P / "control_bad_loader.mb", cases["mixed"])
if have_broken:
    report["controls"]["bad_eof"] = native("ctrl_bad_eof", B.OLMSTEAD,
                                            broken_eof, cases["mixed"])
    report["controls"]["bad_eof"]["source"] = (
        "vm_malbolge/evidence/inout_loader_eof_v1/reference_cat_bad_eof.mb (este repo)")
    report["controls"]["bad_eof"]["sha256"] = sha(broken_eof.read_bytes())

ol = {k: v["olmstead"] for k, v in report["runs"].items()}
report["summary"] = {
    "olmstead_accepts_image": report["image"]["invalid_cells"] == 0,
    "olmstead_echo_exact_all_cases": all(
        (not v["timed_out"]) and v["rc"] == 0 and v["stdout_equals_input"]
        for v in ol.values()),
    "olmstead_empty_input_no_bytes": report["runs"]["empty"]["olmstead"]["stdout_bytes"] == 0,
    "olmstead_all256_exact": report["runs"]["all256"]["olmstead"]["stdout_equals_input"],
    "olmstead_long10000_exact": report["runs"]["long10000"]["olmstead"]["stdout_equals_input"],
    "runner_c_framing_is_single_newline": all(
        v["runner_c"]["stdout_equals_input_plus_newline"] for v in report["runs"].values()),
    "loader_control_rejected": report["controls"]["bad_loader"]["rc"] == 1
    and not report["controls"]["bad_loader"]["timed_out"],
    "eof_control_not_clean": (not have_broken) or (
        report["controls"]["bad_eof"]["rc"] != 0
        or report["controls"]["bad_eof"]["timed_out"]
        or not report["controls"]["bad_eof"]["stdout_equals_input"]),
    "not_claimed": ("esta imagen es una referencia de otro pack; no demuestra "
                    "la variante relocalizada candidate.mb, que sigue sin "
                    "deteccion de EOF"),
}
(P / "reference_functional.results.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
print("summary", json.dumps(report["summary"], indent=2, sort_keys=True), flush=True)

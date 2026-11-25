#!/usr/bin/env python3
"""Compile a literal-functions Python subset to autonomous Classic Malbolge."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tokenize
from pathlib import Path

from classic_backend import compile_program, repository_root
from classic_frontend import CompileError, parse_program


def compile_text(source, forge_root=None):
    return compile_program(parse_program(source), forge_root)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Python literal (def/print/llamadas) → Malbolge Classic autónomo"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument(
        "--map",
        dest="map_path",
        type=Path,
        help="guardar mapa de instancias y CALL/RET",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="ejecutar la imagen con Olmstead después de compilar",
    )
    parser.add_argument(
        "--runner", type=Path, help="ruta alternativa al intérprete Classic"
    )
    args = parser.parse_args(argv)
    try:
        paths = [args.output] + ([args.map_path] if args.map_path else [])
        if len({p.resolve() for p in paths}) != len(paths):
            raise CompileError("la imagen y el mapa requieren rutas distintas")
        for path in paths:
            if path.exists() or path.is_symlink():
                raise CompileError(
                    "la salida ya existe; elige una ruta nueva: " + str(path)
                )
        try:
            with tokenize.open(args.source) as stream:
                source = stream.read()
        except SyntaxError as error:
            raise CompileError(
                error.msg, error.lineno or 1, error.offset or 1
            ) from None
        artifact = compile_text(source)
        # Exclusive creation also protects against an output appearing during compilation.
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(artifact.image)
        if args.map_path:
            with args.map_path.open("x", encoding="utf-8") as stream:
                json.dump(artifact.mapping, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        print(
            f"Compilado: {args.output} ({len(artifact.image)} bytes; {len(artifact.mapping['instances'])} instancias de llamada)",
            file=sys.stderr,
        )
        if args.run:
            runner = (
                args.runner
                or repository_root().parent / "Malbolge-PureEpoch/build/olmstead"
            )
            try:
                return subprocess.run(
                    [str(runner.resolve()), str(args.output.resolve())],
                    timeout=30,
                    check=False,
                ).returncode
            except FileNotFoundError:
                raise CompileError(
                    "imagen guardada; no se encontró Olmstead, usa --runner"
                ) from None
        return 0
    except CompileError as error:
        print(
            f"{args.source}:{error.line}:{error.column}: error: {error}",
            file=sys.stderr,
        )
        return 1
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

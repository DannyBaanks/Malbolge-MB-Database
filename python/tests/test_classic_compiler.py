import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE if (HERE / "classic_frontend.py").exists() else HERE.parent / "src"
sys.path.insert(0, str(SRC))
from classic_backend import repository_root
from classic_compiler import compile_text
from classic_frontend import CompileError, parse_program

REPO = repository_root()
RUNNER = REPO.parent / "Malbolge-PureEpoch/build/olmstead"
CORPUS = {
    "saludar": 'def saludar():\n print("Hola")\nsaludar()\n',
    "repeated": 'def f():\n print("Hola")\nf()\nf()\n',
    "nested": 'def inner():\n print("¡Hola 🌎!",end=" ")\ndef outer():\n print("Inicio")\n inner()\n print("Fin")\nouter()\nouter()\n',
    "empty": "def f():\n pass\nf()\nf()\n",
    "early_return": 'def f():\n print("uno")\n return\n print("no")\nf()\n',
    "forward": 'def a():\n b()\ndef b():\n print("b")\na()\n',
    "module": '"doc"\nprint("a","b",sep="/",end="!")\nprint()\nprint("\\x00")\n',
    "nothing": "pass\n",
}


class FrontendTests(unittest.TestCase):
    def test_repeated_and_nested_invocations(self):
        p = parse_program(
            'def inner():\n print("Hola")\ndef outer():\n inner()\n print("fin")\nouter()\nouter()\n'
        )
        self.assertEqual(
            [x.name for x in p.instances], ["outer", "inner", "outer", "inner"]
        )
        self.assertEqual([x.depth for x in p.instances], [1, 2, 1, 2])
        self.assertEqual(p.output_bytes, len(b"Hola\nfin\n") * 2)

    def test_early_return_excludes_unreachable_calls(self):
        p = parse_program('def f():\n print("a")\n return\n f()\nf()\n')
        self.assertEqual(len(p.instances), 1)

    def test_forward_function_resolves_at_invocation(self):
        parse_program("def a():\n b()\ndef b():\n pass\na()\n")

    def test_definition_order_is_respected(self):
        for source in (
            "f()\ndef f():\n pass\n",
            "def a():\n b()\na()\ndef b():\n pass\n",
        ):
            with self.assertRaises(CompileError):
                parse_program(source)

    def test_unicode_and_print_keywords(self):
        p = parse_program('print("¡Hola", "🌎", sep="-", end="!")\nprint()')
        self.assertEqual(p.output_bytes, len("¡Hola-🌎!\n".encode()))

    def test_unsupported_source_is_never_executed(self):
        with tempfile.TemporaryDirectory() as d:
            victim = Path(d) / "unexpected"
            with self.assertRaises(CompileError):
                parse_program(f'open({str(victim)!r},"w").write("bad")')
            self.assertFalse(victim.exists())

    def test_unsupported_constructs_have_locations(self):
        sources = [
            "x=1",
            "while True:\n pass",
            "import os",
            "def f(x):\n pass",
            "def f():\n return 1",
            "def print():\n pass",
            "print(1)",
            'print("a",file="x")',
            "return",
            "@x\ndef f():\n pass",
            "def f():\n pass\ndef f():\n pass",
            "def f():\n f()\nf()",
            'print("\\ud800")',
        ]
        for source in sources:
            with self.subTest(source=source):
                with self.assertRaises(CompileError) as error:
                    parse_program(source)
                self.assertGreaterEqual(error.exception.line, 1)

    def test_reserved_debug_name(self):
        source = "def __debug__():\n pass\n__debug__()\n"
        with self.assertRaises(SyntaxError):
            compile(source, "<fixture>", "exec")
        with self.assertRaises(CompileError):
            parse_program(source)

    def test_resource_limits(self):
        deep = (
            "".join(
                f"def f{i}():\n " + (f"f{i + 1}()" if i < 16 else "pass") + "\n"
                for i in range(17)
            )
            + "f0()\n"
        )
        for source in (
            'print("' + ("x" * 257) + '")',
            "def f():\n pass\n" + "f()\n" * 33,
            "#" + "x" * 65536,
            deep,
        ):
            with self.assertRaises(CompileError):
                parse_program(source)


class NativeTests(unittest.TestCase):
    def test_corpus_against_real_python(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, source in CORPUS.items():
                with self.subTest(name=name):
                    artifact = compile_text(source)
                    mb = Path(folder) / (name + ".mb")
                    mb.write_bytes(artifact.image)
                    native = subprocess.run(
                        [str(RUNNER), str(mb)],
                        input=b"",
                        capture_output=True,
                        timeout=10,
                        check=True,
                    )
                    expected = subprocess.run(
                        [sys.executable, "-c", source],
                        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                        capture_output=True,
                        timeout=10,
                        check=True,
                    )
                    self.assertEqual(native.stdout, expected.stdout)
                    self.assertTrue(
                        all(
                            33 <= x <= 126
                            and (x + i) % 94 in {4, 5, 23, 39, 40, 62, 68, 81}
                            for i, x in enumerate(artifact.image)
                        )
                    )

    def test_determinism_and_nested_slot_isolation(self):
        first = compile_text(CORPUS["nested"])
        second = compile_text(CORPUS["nested"])
        self.assertEqual(first.image, second.image)
        self.assertEqual(first.mapping, second.mapping)
        instances = first.mapping["instances"]
        self.assertEqual([i["depth"] for i in instances], [1, 2, 1, 2])
        self.assertEqual(len({i["entry"] for i in instances}), 4)
        self.assertEqual(instances[0]["slot"], instances[2]["slot"])
        self.assertNotEqual(instances[0]["slot"], instances[1]["slot"])

    def test_cli_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.py"
            source.write_text(CORPUS["saludar"])
            output = Path(folder) / "program.mb"
            output.write_bytes(b"preserve")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SRC / "classic_compiler.py"),
                    str(source),
                    "-o",
                    str(output),
                ],
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(output.read_bytes(), b"preserve")

    def test_cli_rejection_does_not_create_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.py"
            source.write_text("print(1)")
            output = Path(folder) / "program.mb"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SRC / "classic_compiler.py"),
                    str(source),
                    "-o",
                    str(output),
                ],
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn(b":1:7:", result.stderr)
            self.assertFalse(output.exists())

    def test_invalid_encoding_diagnostic(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.py"
            source.write_bytes(b"# coding: imaginary-codec\npass\n")
            output = Path(folder) / "program.mb"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SRC / "classic_compiler.py"),
                    str(source),
                    "-o",
                    str(output),
                ],
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn(b":1:1: error:", result.stderr)
            self.assertNotIn(b"Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_actual_layout_capacity_is_rejected(self):
        source = "print(" + repr("".join("x" + chr(i) for i in range(100))) + ")"
        with self.assertRaisesRegex(CompileError, "cabecera"):
            compile_text(source)

    def test_existing_map_is_preserved_without_new_image(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.py"
            source.write_text(CORPUS["saludar"])
            output = Path(folder) / "program.mb"
            mapping = Path(folder) / "map.json"
            mapping.write_text("preserve")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SRC / "classic_compiler.py"),
                    str(source),
                    "-o",
                    str(output),
                    "--map",
                    str(mapping),
                ],
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(mapping.read_text(), "preserve")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

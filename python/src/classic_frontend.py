"""Validated, non-executing Python AST subset for the Classic native backend."""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass, field


class CompileError(Exception):
    def __init__(self, message, line=1, column=1):
        super().__init__(message)
        self.line = line
        self.column = column


def fail(message, node=None):
    raise CompileError(
        message, getattr(node, "lineno", 1), getattr(node, "col_offset", 0) + 1
    )


@dataclass
class Print:
    data: bytes
    line: int
    column: int


@dataclass
class Call:
    identifier: int
    name: str
    depth: int
    line: int
    column: int
    body: list = field(default_factory=list)


@dataclass
class Program:
    body: list
    instances: list[Call]
    source_sha256: str
    output_bytes: int


def parse_program(source: str) -> Program:
    try:
        raw = source.encode("utf-8")
    except UnicodeError:
        fail("el fuente contiene Unicode no válido")
    if len(raw) > 65536:
        fail("el fuente supera 64 KiB")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise CompileError(e.msg, e.lineno or 1, e.offset or 1) from None
    functions = {}

    def literal(node):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            fail("print solo admite textos literales", node)
        return node.value

    def statement(node, in_function):
        if isinstance(node, ast.Pass):
            return None
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return None
        if isinstance(node, ast.Return):
            if not in_function:
                fail("return fuera de una función", node)
            if node.value is not None:
                fail("solo se admite return sin valor", node)
            return ("return", node)
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            fail("instrucción no admitida: " + type(node).__name__, node)
        call = node.value
        if not isinstance(call.func, ast.Name):
            fail("solo se admiten llamadas directas por nombre", call)
        if call.func.id == "print":
            options = {}
            for keyword in call.keywords:
                if keyword.arg not in ("sep", "end") or keyword.arg in options:
                    fail("print solo admite sep/end literales", call)
                options[keyword.arg] = literal(keyword.value)
            text = options.get("sep", " ").join(
                literal(arg) for arg in call.args
            ) + options.get("end", "\n")
            try:
                data = text.encode("utf-8")
            except UnicodeError:
                fail("el texto no se puede codificar como UTF-8", call)
            return Print(data, node.lineno, node.col_offset + 1)
        if call.args or call.keywords:
            fail("las funciones no admiten argumentos", call)
        return ("call", call.func.id, node)

    def body(nodes, in_function):
        return [s for node in nodes if (s := statement(node, in_function)) is not None]

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            args = node.args
            if node.name in {"print", "__debug__"} or node.name in functions:
                fail("nombre de función reservado o duplicado: " + node.name, node)
            if (
                args.posonlyargs
                or args.args
                or args.kwonlyargs
                or args.vararg
                or args.kwarg
                or node.decorator_list
                or node.returns
                or getattr(node, "type_params", [])
            ):
                fail(
                    "función sin parámetros, decoradores ni anotaciones requerida", node
                )
            functions[node.name] = body(node.body, True)
    instances = []
    total = 0

    def expand(statements, defined, trail):
        nonlocal total
        result = []
        for s in statements:
            if isinstance(s, Print):
                total += len(s.data)
                if total > 256:
                    raise CompileError(
                        "la salida expandida supera 256 bytes UTF-8", s.line, s.column
                    )
                result.append(s)
            elif s[0] == "return":
                break
            else:
                _, name, node = s
                if name not in defined:
                    fail("función no definida en este punto: " + name, node)
                if name in trail:
                    fail("recursión no admitida: " + " → ".join((*trail, name)), node)
                if len(trail) >= 16:
                    fail("profundidad estática superior a 16", node)
                if len(instances) >= 32:
                    fail("más de 32 instancias de llamada", node)
                invocation = Call(
                    len(instances),
                    name,
                    len(trail) + 1,
                    node.lineno,
                    node.col_offset + 1,
                )
                instances.append(invocation)
                invocation.body = expand(functions[name], defined, (*trail, name))
                result.append(invocation)
        return result

    defined = set()
    main = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            defined.add(node.name)
        else:
            main.extend(expand(body([node], False), defined, ()))
    return Program(main, instances, hashlib.sha256(raw).hexdigest(), total)

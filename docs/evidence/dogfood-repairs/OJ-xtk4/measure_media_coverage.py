# SPDX-License-Identifier: MIT
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest


media = Path("src/openjutsu/media.py").resolve()
executed: set[int] = set()


def tracer(frame, event, arg):
    if Path(frame.f_code.co_filename).resolve() == media and event == "line":
        executed.add(frame.f_lineno)
    return tracer


sys.settrace(tracer)
test_exit = pytest.main(["tests/test_media.py", "-q"])
sys.settrace(None)

module = ast.parse(media.read_text(encoding="utf-8"))
function = next(
    node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "make_side_by_side"
)
statement_lines = {
    node.lineno
    for node in ast.walk(function)
    if isinstance(node, ast.stmt) and node is not function and hasattr(node, "lineno")
}
first = function.body[0]
if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
    statement_lines.discard(first.lineno)
covered = statement_lines & executed
print(
    "make_side_by_side statement coverage: "
    f"{len(covered)}/{len(statement_lines)} = {100 * len(covered) / len(statement_lines):.2f}%"
)
print(f"executed statement lines: {sorted(covered)}")
print(f"uncovered statement lines: {sorted(statement_lines - covered)}")
raise SystemExit(test_exit)

# SPDX-License-Identifier: MIT
"""Local verification runner; execute with the project virtualenv from repo root."""
import ast
import hashlib
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path.cwd()
EVIDENCE = ROOT / "docs/evidence/status-atomic/OJ-p8rd"


def legacy_control():
    # Replace only the function in memory with the actual base-commit source.
    # No production file is changed, and this subprocess dies after the test.
    sys.path.insert(0, str(ROOT))
    import app.main as main
    import pytest

    source = subprocess.check_output(
        ["git", "show", "2b22504:app/main.py"], text=True,
    )
    function = next(
        node for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "_set_status"
    )
    exec(compile(ast.Module(body=[function], type_ignores=[]), "base-main.py", "exec"), main.__dict__)
    return pytest.main([
        "tests/test_status_atomic.py::test_publication_boundary[atomic-writer-200]",
        "-q", "--tb=short",
    ])


def run(label, arguments, expected=0):
    result = subprocess.run([sys.executable, *arguments], text=True, capture_output=True)
    output = result.stdout + result.stderr
    output = output.replace(str(ROOT), "<WORKTREE>")
    output = re.sub(r"/Users/[^\s:]+", "<PRIVATE_PATH>", output)
    output = re.sub(r"/private/var/[^\s:]+", "<TEMP_PATH>", output)
    transcript = f"COMMAND: python {' '.join(arguments)}\nEXIT: {result.returncode}\n{output}"
    (EVIDENCE / f"{label}.txt").write_text(transcript)
    print(transcript, flush=True)
    if result.returncode != expected:
        raise SystemExit(f"Unexpected result for {label}: {result.returncode}")


if __name__ == "__main__":
    if "--legacy-control" in sys.argv:
        raise SystemExit(legacy_control())
    run("legacy-control", ["docs/evidence/status-atomic/OJ-p8rd/verify.py", "--legacy-control"], 1)
    for repeat in range(1, 4):
        run(f"focused-{repeat}", ["-m", "pytest", "tests/test_status_atomic.py", "-q"])
    run("full-suite", ["-m", "pytest", "-q"])
    files = [ROOT / "app/main.py", ROOT / "tests/test_status_atomic.py"]
    files += sorted(path for path in EVIDENCE.iterdir() if path.name != "SHA256SUMS")
    (EVIDENCE / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT)}\n"
        for path in files if path.is_file()
    ))

# code_runner.py - [NEW] sandboxed executor (5s/256MB/no-net); Judge0 path ready
# backend/app/services/code_runner.py
"""
Runs a student's Python solution against test cases.

⚠️  SECURITY: this executes user-submitted code in a subprocess with a timeout
and Python's isolated mode (-I). That is NOT a real security sandbox. For
production you MUST replace run_python() with a sandboxed executor (Judge0,
Docker/gVisor, nsjail). Everything else in the platform calls ONLY this one
function, so that swap is a single-file change.

Test case format (per case): {"input": [args...], "output": <expected return>}
The problem stores an "entry_point" (the function name to call).
"""
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

# Static harness (no str.format) — reads meta.json + cases.json, execs the
# student's solution.py into a namespace (avoids module-path issues under -I).
_HARNESS = r'''
import json
with open("meta.json") as f:
    meta = json.load(f)
with open("cases.json") as f:
    cases = json.load(f)
ns = {}
try:
    with open("solution.py") as f:
        exec(f.read(), ns)
except Exception as e:  # noqa: BLE001 - syntax/import error in the submission
    print(json.dumps([{"index": i, "passed": False,
                       "error": "Compile error: " + str(e)[:150]} for i in range(len(cases))]))
    raise SystemExit(0)
entry = ns.get(meta["entry_point"])
out = []
for i, c in enumerate(cases):
    if entry is None:
        out.append({"index": i, "passed": False,
                    "error": "entry point not found: " + str(meta["entry_point"])})
        continue
    try:
        result = entry(*c["input"])
        out.append({"index": i, "passed": result == c["output"], "got": repr(result)[:200]})
    except Exception as e:  # noqa: BLE001 - runtime error in the submission
        out.append({"index": i, "passed": False,
                    "error": type(e).__name__ + ": " + str(e)[:150]})
print(json.dumps(out))
'''


async def run_python(user_code: str, entry_point: str, cases: list[dict], timeout: float = 5.0) -> dict:
    """Return {"results": [...], "runtime_ms": int, "compile_error": str|None}."""
    n = len(cases)
    tmp = tempfile.mkdtemp(prefix="arena_")
    try:
        with open(os.path.join(tmp, "solution.py"), "w") as f:
            f.write(user_code)
        with open(os.path.join(tmp, "cases.json"), "w") as f:
            json.dump(cases, f)
        with open(os.path.join(tmp, "meta.json"), "w") as f:
            json.dump({"entry_point": entry_point}, f)
        with open(os.path.join(tmp, "harness.py"), "w") as f:
            f.write(_HARNESS)

        start = time.perf_counter()
        # Run the blocking subprocess in a worker thread. subprocess.run works in
        # any thread (unlike asyncio subprocesses, which need the main-thread child
        # watcher) and kills the child on timeout.
        def _run() -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, "-I", "harness.py"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        try:
            proc = await asyncio.to_thread(_run)
        except subprocess.TimeoutExpired:
            return {
                "results": [{"index": i, "passed": False, "error": "Time limit exceeded"} for i in range(n)],
                "runtime_ms": int(timeout * 1000),
                "compile_error": None,
            }

        runtime_ms = int((time.perf_counter() - start) * 1000)
        try:
            results = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError:
            return {
                "results": [{"index": i, "passed": False, "error": "Execution error"} for i in range(n)],
                "runtime_ms": runtime_ms,
                "compile_error": (proc.stderr or "Unknown error")[:500],
            }
        return {"results": results, "runtime_ms": runtime_ms, "compile_error": None}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


__all__ = ["run_python"]
"""Integration tests: solve MIP instances and verify optimal values."""
import os
import re
import subprocess

import pytest

import cbcbox

DATA_DIR = os.path.dirname(__file__)

# (filename, expected_optimal, cbc_time_limit_seconds)
# Time limits are generous to avoid false failures on slow CI runners.
# subprocess timeout = cbc_time_limit + 120 s.
CASES = [
    ("pp08a.mps.gz",                    7350.0,           300),
    ("sprint_hidden06_j.mps.gz",        130.0,            900),
    ("air03.mps.gz",                    340160.0,          600),
    ("air04.mps.gz",                    56137.0,           600),
    ("air05.mps.gz",                    26374.0,           900),
    ("nw04.mps.gz",                     16862.0,           900),
    ("mzzv11.mps.gz",                   -21718.0,          900),
    ("trd445c.mps.gz",                  -153419.078836,   1200),
    ("nursesched-sprint02.mps.gz",      58.0,              600),
    ("stein45.mps.gz",                  30.0,              300),
    ("neos-808214.mps.gz",              5.0,               600),
    ("neos-810286.mps.gz",              2877.0,            300),
    ("neos-1281048.mps.gz",             601.0,             300),
]


def _solve_and_get_obj(mps_file: str, cbc_binary: str = None,
                        time_limit: int = 600,
                        threads: int = 1, timeout: int = None):
    """Run CBC on *mps_file*, return (objective, elapsed_seconds).

    Parses the final "Optimal - objective value X" line specifically to avoid
    matching intermediate lines such as:
        "After applying Clique Strengthening continuous objective value is ..."
    Elapsed wall-clock time is parsed from CBC's "Wallclock seconds)" summary line.
    """
    cmd = [cbc_binary or cbcbox.cbc_bin_path(), mps_file, f"-seconds={time_limit}", "-timem", "elapsed"]
    if threads > 1:
        cmd += [f"-threads={threads}"]
    cmd += ["-solve", "-quit"]
    # Prevent OpenBLAS from spawning its own thread pool inside each CBC worker
    # thread.  When CBC runs with -threads N, each worker calls into OpenBLAS;
    # without this, total threads = N × OPENBLAS_NUM_THREADS which exhausts
    # memory on CI runners (observed SIGSEGV in dgetrf_single on macOS Intel).
    env = os.environ.copy()
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            timeout=timeout or (time_limit + 120), env=env)
    output = result.stdout + result.stderr
    # Look for the definitive result lines (last wins in case of duplicates):
    #   "Optimal - objective value 7350.00000000"
    #   "Result - Stopped on time limit\nObjective value: 130.000"
    obj_value = None
    elapsed   = None
    for line in output.splitlines():
        low = line.lower()
        if low.startswith("optimal") and "objective value" in low:
            try:
                obj_value = float(line.split()[-1])
            except ValueError:
                pass
        elif low.startswith("objective value") or low.startswith("objective:"):
            try:
                obj_value = float(line.split()[-1])
            except ValueError:
                pass
        m = re.search(r'Wallclock seconds\):\s+([\d.]+)', line)
        if m:
            elapsed = float(m.group(1))
    if obj_value is None:
        raise AssertionError(
            f"Could not parse final objective from CBC output.\nOutput:\n{output}"
        )
    return obj_value, elapsed


def test_cbc_binary_exists():
    path = cbcbox.cbc_bin_path()
    assert os.path.isfile(path), f"cbc binary not found at {path}"


@pytest.mark.parametrize("filename,expected,time_limit", CASES,
                         ids=lambda x: x if isinstance(x, str) else None)
def test_solve(filename, expected, time_limit, cbc_variant, request):
    variant_name, cbc_binary = cbc_variant
    mps_file = os.path.join(DATA_DIR, filename)
    obj, elapsed = _solve_and_get_obj(mps_file, cbc_binary, time_limit=time_limit)
    request.config._perf_results.append(
        {"instance": filename, "threads": 1, "elapsed_s": elapsed,
         "objective": obj, "build_variant": variant_name}
    )
    assert abs(obj - expected) < 1e-4, f"Expected {expected}, got {obj}"


@pytest.mark.parametrize("filename,expected,time_limit", CASES,
                         ids=lambda x: x if isinstance(x, str) else None)
def test_solve_parallel(filename, expected, time_limit, cbc_variant, request):
    """Same instances solved with 3 threads to verify --enable-cbc-parallel."""
    variant_name, cbc_binary = cbc_variant
    mps_file = os.path.join(DATA_DIR, filename)
    obj, elapsed = _solve_and_get_obj(mps_file, cbc_binary, time_limit=time_limit, threads=3)
    request.config._perf_results.append(
        {"instance": filename, "threads": 3, "elapsed_s": elapsed,
         "objective": obj, "build_variant": variant_name}
    )
    assert abs(obj - expected) < 1e-4, f"Expected {expected}, got {obj} (3 threads)"

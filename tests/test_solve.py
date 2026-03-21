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
    ("pp08a.mps.gz",                    7350.0,           2000),
    ("sprint_hidden06_j.mps.gz",        130.0,            2000),
    ("air03.mps.gz",                    340160.0,         2000),
    ("air04.mps.gz",                    56137.0,          2000),
    ("air05.mps.gz",                    26374.0,          2000),
    ("nw04.mps.gz",                     16862.0,          2000),
    ("mzzv11.mps.gz",                   -21718.0,         2000),
    ("trd445c.mps.gz",                  -153419.078836,   2000),
    ("nursesched-sprint02.mps.gz",      58.0,             2000),
    ("stein45.mps.gz",                  30.0,             2000),
    ("neos-810286.mps.gz",              2877.0,           2000),
    ("neos-1281048.mps.gz",             601.0,            2000),
    ("j3050_8.mps.gz",                  1.0,              2000),
    ("qiu.mps.gz",                      -132.873136947,   2000),
    ("gesa2-o.mps.gz",                  25779856.3717,    2000),
    ("pk1.mps.gz",                      11.0,             2000),
    ("mas76.mps.gz",                    40005.054142,     2000),
    ("app1-1.mps.gz",                  -3.0,             2000),
    ("eil33-2.mps.gz",                  934.007916,       2000),
    ("fiber.mps.gz",                    405935.18,        2000),
    ("neos-2987310-joes.mps.gz",        -607702988.291,   2000),
    ("neos-827175.mps.gz",              112.00152,        2000),
    ("neos-3083819-nubu.mps.gz",        6307996.0,        2000),
    ("markshare_4_0.mps.gz",           1.0,              2000),
    ("nu25-pr12.mps.gz",               53905.0,          2000),
    ("swath1.mps.gz",                  379.07129575,     2000),
    ("physiciansched6-2.mps.gz",       49324.0,          2000),
    ("mzzv42z.mps.gz",                 -20540.0,         2000),
    ("neos-860300.mps.gz",             3201.0,           2000),
]

_REL_TOL = 1e-6   # relative tolerance for objective comparison
_ABS_TOL = 1e-4   # absolute tolerance (used when expected is near zero)


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
    tol = max(_ABS_TOL, _REL_TOL * abs(expected))
    assert abs(obj - expected) <= tol, f"Expected {expected}, got {obj}"


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
    tol = max(_ABS_TOL, _REL_TOL * abs(expected))
    assert abs(obj - expected) <= tol, f"Expected {expected}, got {obj} (3 threads)"

"""Integration tests: solve MIP instances and verify optimal values."""
import os
import re
import subprocess

import pytest

import cbcbox

DATA_DIR = os.path.dirname(__file__)

CASES = [
    ("pp08a.mps.gz", 7350.0),
    ("sprint_hidden06_j.mps.gz", 130.0),
    ("air04.mps.gz", 56137.0),
]

# CBC time limit for tests (seconds); prevents long runs on slow CI machines.
CBC_TIME_LIMIT = 240


def _solve_and_get_obj(mps_file: str, time_limit: int = CBC_TIME_LIMIT,
                       threads: int = 1, timeout: int = 300):
    """Run CBC on *mps_file*, return (objective, elapsed_seconds).

    Parses the final "Optimal - objective value X" line specifically to avoid
    matching intermediate lines such as:
        "After applying Clique Strengthening continuous objective value is ..."
    Elapsed wall-clock time is parsed from CBC's "Wallclock seconds)" summary line.
    """
    cmd = [cbcbox.cbc_bin_path(), mps_file, f"-seconds={time_limit}", "-timem", "elapsed"]
    if threads > 1:
        cmd += [f"-threads={threads}"]
    cmd += ["-solve", "-quit"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
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


@pytest.mark.parametrize("filename,expected", CASES)
def test_solve(filename, expected, request):
    mps_file = os.path.join(DATA_DIR, filename)
    obj, elapsed = _solve_and_get_obj(mps_file)
    request.config._perf_results.append(
        {"instance": filename, "threads": 1, "elapsed_s": elapsed, "objective": obj}
    )
    assert abs(obj - expected) < 1e-4, f"Expected {expected}, got {obj}"


@pytest.mark.parametrize("filename,expected", CASES)
def test_solve_parallel(filename, expected, request):
    """Same instances solved with 3 threads to verify --enable-cbc-parallel."""
    mps_file = os.path.join(DATA_DIR, filename)
    obj, elapsed = _solve_and_get_obj(mps_file, threads=3)
    request.config._perf_results.append(
        {"instance": filename, "threads": 3, "elapsed_s": elapsed, "objective": obj}
    )
    assert abs(obj - expected) < 1e-4, f"Expected {expected}, got {obj} (3 threads)"

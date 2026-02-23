"""Integration tests: solve MIP instances and verify optimal values."""
import os
import subprocess

import pytest

import cbcbox

DATA_DIR = os.path.dirname(__file__)

CASES = [
    ("pp08a.mps.gz", 7350.0),
    ("sprint_hidden06_j.mps.gz", 130.0),
]


def _solve_and_get_obj(mps_file: str, timeout: int = 300) -> float:
    """Run CBC on *mps_file*, return the reported optimal objective value."""
    result = subprocess.run(
        [cbcbox.cbc_bin_path(), mps_file, "-solve", "-quit"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = result.stdout + result.stderr
    # CBC prints "Optimal - objective value XXXX.XXXXXXXX"
    for line in output.splitlines():
        if "objective value" in line.lower():
            try:
                return float(line.split()[-1])
            except ValueError:
                continue
    raise AssertionError(
        f"Could not find 'objective value' in CBC output.\nOutput:\n{output}"
    )


def test_cbc_binary_exists():
    path = cbcbox.cbc_bin_path()
    assert os.path.isfile(path), f"cbc binary not found at {path}"


@pytest.mark.parametrize("filename,expected", CASES)
def test_solve(filename, expected):
    mps_file = os.path.join(DATA_DIR, filename)
    obj = _solve_and_get_obj(mps_file)
    assert abs(obj - expected) < 1e-4, f"Expected {expected}, got {obj}"

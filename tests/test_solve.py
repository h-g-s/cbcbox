"""Integration test: solve pp08a.mps.gz and verify the optimal value."""
import os
import subprocess
import sys

import pytest

import cbcbox

DATA_DIR = os.path.join(os.path.dirname(__file__))
MPS_FILE = os.path.join(DATA_DIR, "pp08a.mps.gz")

EXPECTED_OBJ = 7350.0


def test_cbc_binary_exists():
    path = cbcbox.cbc_bin_path()
    assert os.path.isfile(path), f"cbc binary not found at {path}"


def test_solve_pp08a():
    """Solve pp08a MIP and verify optimal objective value = 7350."""
    result = subprocess.run(
        [cbcbox.cbc_bin_path(), MPS_FILE, "solve", "quit"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr

    # CBC prints "Optimal - objective value XXXX.XXXXXXXX"
    obj_value = None
    for line in output.splitlines():
        if "objective value" in line.lower():
            try:
                obj_value = float(line.split()[-1])
                break
            except ValueError:
                continue

    assert obj_value is not None, (
        f"Could not find 'objective value' in CBC output.\nOutput:\n{output}"
    )
    assert abs(obj_value - EXPECTED_OBJ) < 1e-4, (
        f"Expected objective {EXPECTED_OBJ}, got {obj_value}.\nOutput:\n{output}"
    )

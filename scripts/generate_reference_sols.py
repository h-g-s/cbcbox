#!/usr/bin/env python3
"""Generate/refresh reference .sol files under tests/sols/ for every instance
listed in tests/test_solve.py's CASES table.

Reference solutions are used by the mip-debug-cuts CI diagnostic (see
tests/conftest.py) to activate Cbc/Osi's row-cut debugger whenever a
test_solve/test_solve_parallel run produces the wrong optimal objective: the
debugger flags any cut, bound-fixing, or branching decision that would have
excluded the (independently verified) reference solution, pinpointing which
component introduced the regression.

For each instance this script:
  1. Solves the .mps.gz with HiGHS (highspy) to (near-)optimality.
  2. Cross-checks the resulting objective against the `expected` value
     hard-coded in tests/test_solve.py's CASES table (within the same
     tolerance used by the tests themselves).
  3. Writes tests/sols/<name>.sol in Cbc's native solution format:
         <col-index> <col-name> <value> 0
     one line per NONZERO variable, preceded by a header line
     "Optimal - objective value <obj>" -- the same format Cbc itself writes
     via `-solve -solu <file>` and the format mip-sanity-data /
     Cbc/test/mip-debug-cuts.cpp's readSolFile() already expect.

Usage:
    python scripts/generate_reference_sols.py [instance_name ...]

With no arguments, (re)generates .sol files for every CASES instance that
does not already have one in tests/sols/. Pass explicit instance name(s)
(without the .mps.gz suffix) to force regeneration of specific instances.

Requires: pip install highspy
"""
import gzip
import os
import re
import shutil
import sys
import tempfile

try:
    import highspy
except ImportError:
    sys.exit("highspy is required: pip install highspy")

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)
TESTS_DIR = os.path.join(REPO_ROOT, "tests")
SOLS_DIR = os.path.join(TESTS_DIR, "sols")

_REL_TOL = 1e-6
_ABS_TOL = 1e-4


def _load_cases():
    """Parse the CASES table out of tests/test_solve.py without importing it
    (avoids requiring cbcbox/the compiled cbc binary to be installed)."""
    cases = []
    pattern = re.compile(
        r'\(\s*"([^"]+)\.mps\.gz"\s*,\s*([-\d.eE]+)\s*,\s*(\d+)\s*\)'
    )
    with open(os.path.join(TESTS_DIR, "test_solve.py")) as f:
        for line in f:
            m = pattern.search(line)
            if m:
                cases.append((m.group(1), float(m.group(2))))
    return cases


def _solve_with_highs(mps_gz_path, time_limit):
    tmpdir = tempfile.mkdtemp(prefix="cbcbox_gensol_")
    try:
        mps_path = os.path.join(tmpdir, "instance.mps")
        with gzip.open(mps_gz_path, "rb") as fin, open(mps_path, "wb") as fout:
            shutil.copyfileobj(fin, fout)

        h = highspy.Highs()
        h.setOptionValue("output_flag", False)
        h.setOptionValue("time_limit", float(time_limit))
        h.setOptionValue("mip_rel_gap", 1e-9)
        h.setOptionValue("mip_abs_gap", 1e-9)
        h.readModel(mps_path)
        h.run()

        status = str(h.getModelStatus())
        info = h.getInfo()
        sol = h.getSolution()
        lp = h.getLp()
        return status, info.objective_function_value, lp.col_names_, list(sol.col_value)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _write_sol_file(path, status_label, obj, col_names, col_values):
    with open(path, "w") as f:
        f.write(f"{status_label} - objective value {obj:.8f}\n")
        idx = 0
        for name, value in zip(col_names, col_values):
            if abs(value) > 1e-11:
                f.write(f"{idx:>7d} {name:<24s}{value:>15.8f}{0:>24d}\n")
            idx += 1


def generate(name, expected, time_limit, force=False):
    sol_path = os.path.join(SOLS_DIR, f"{name}.sol")
    if os.path.exists(sol_path) and not force:
        print(f"[skip] {name}: tests/sols/{name}.sol already exists")
        return True

    mps_gz = os.path.join(TESTS_DIR, f"{name}.mps.gz")
    if not os.path.isfile(mps_gz):
        print(f"[error] {name}: {mps_gz} not found")
        return False

    print(f"[solve] {name}: running HiGHS (time_limit={time_limit}s)...")
    status, obj, col_names, col_values = _solve_with_highs(mps_gz, time_limit)

    tol = max(_ABS_TOL, _REL_TOL * abs(expected))
    if abs(obj - expected) > tol:
        print(f"[MISMATCH] {name}: HiGHS obj={obj!r} vs expected={expected!r} "
              f"(tol={tol!r}, status={status}) -- NOT writing .sol, please "
              f"investigate manually (increase time_limit? wrong expected "
              f"value in test_solve.py?)")
        return False

    is_optimal = "kOptimal" in status
    label = "Optimal" if is_optimal else "Feasible"
    os.makedirs(SOLS_DIR, exist_ok=True)
    _write_sol_file(sol_path, label, obj, col_names, col_values)
    print(f"[OK] {name}: obj={obj!r} status={status} -> tests/sols/{name}.sol")
    return True


def main():
    requested = sys.argv[1:]
    cases = _load_cases()
    by_name = {name: expected for name, expected in cases}

    if requested:
        targets = [(n, by_name[n]) for n in requested if n in by_name]
        missing = set(requested) - set(by_name)
        if missing:
            sys.exit(f"Unknown instance name(s) not in tests/test_solve.py CASES: {sorted(missing)}")
        force = True
    else:
        targets = cases
        force = False

    failures = []
    for name, expected in targets:
        # Generous time limit: this is a one-off, offline generation step,
        # not part of the CI test run itself.
        if not generate(name, expected, time_limit=600, force=force):
            failures.append(name)

    if failures:
        sys.exit(f"\nFailed/mismatched instances: {failures}")


if __name__ == "__main__":
    main()

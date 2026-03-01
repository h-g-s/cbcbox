# cbcbox – Copilot Instructions

cbcbox is a Python wheel that packages pre-built, self-contained binaries for the
[CBC](https://github.com/coin-or/Cbc) MILP solver (COIN-OR Branch and Cut).
The Python layer is a thin wrapper; the bulk of the work is in `setup.py`, which
compiles all C/C++/Fortran dependencies from source and bundles them into the wheel.

## Commands

```bash
# Install from source (triggers the full C++ build)
pip install -e .

# Build a wheel
python setup.py bdist_wheel

# Run all tests
pytest tests/ -v

# Run a single test
pytest tests/test_solve.py::test_cbc_binary_exists -v
pytest "tests/test_solve.py::test_solve[pp08a.mps.gz-7350.0]" -v
```

Tests require the package to be installed (the `cbc` binary must exist at
`cbcbox/cbc_dist/bin/cbc`). The `cbc_dist/` directory is built by `setup.py`
and is **not** committed to git.

## Architecture

```
src/                     # Python package (cbcbox/)
  __init__.py            # Path helpers: cbc_bin_path(), cbc_lib_dir(), cbc_include_dir()
  __main__.py            # CLI entry point: python -m cbcbox <args>
setup.py                 # Main build driver — compiles everything from source
tests/
  test_solve.py          # Integration tests: solve MIP instances and verify objectives
  conftest.py            # pytest hooks: collect CBC timing and write perf_report.{md,json}
  *.mps.gz               # Test MIP instances
.github/workflows/
  wheel.yml              # cibuildwheel CI: builds + tests on 5 platforms, optional PyPI publish
.github/scripts/
  combine_perf_reports.py  # Merges per-platform perf_report.json files into a single table
```

### Build pipeline (setup.py)

`setup.py` performs the full from-source build when `pip install` or
`python setup.py bdist_wheel` is invoked. Build order is strict (each depends
on the previous):

1. **OpenBLAS** (`v0.3.31`) — optimised BLAS/LAPACK
2. **SuiteSparse AMD** (`v7.12.2`) — sparse fill-reducing ordering for Clp barrier
3. **Nauty** (`2.8.9`) — symmetry detection for MIP presolve
4. **CoinUtils → Osi → Clp → Cgl → Cbc** — COIN-OR stack (all from `master`)

After building, `setup.py` bundles dynamic dependencies (libgfortran, libopenblas,
libquadmath, etc.) by:
- **Linux**: using `patchelf` to rewrite RPATHs to `$ORIGIN`
- **macOS**: rewriting `install_name` / `@rpath` entries with `install_name_tool`
- **Windows**: copying DLLs next to the `cbc.exe` binary in `bin/`

### Wheel layout

The installed wheel places everything under `cbcbox/cbc_dist/`:
```
cbc_dist/bin/   — cbc (and clp) binaries
cbc_dist/lib/   — static (.a) and shared (.so/.dylib/.dll) libraries + pkgconfig
cbc_dist/include/coin/  — COIN-OR headers
```

The wheel tag is always `py3-none-<platform>` (not CPython-specific) because the
package contains only pre-built native binaries.

## Key Conventions

- **Tests are integration tests only.** They invoke the real `cbc` binary via
  `subprocess` and parse its stdout for `"Optimal - objective value X"` or
  `"Objective value: X"` lines.
- **`conftest.py` writes side-effect files.** After each test run,
  `tests/perf_report.json` and `tests/perf_report.md` are written with timing
  data. These are gitignored but consumed by the CI `combine_reports` job.
- **Windows uses MSYS2/MinGW64.** All `autotools` builds on Windows run inside
  `C:\msys64\usr\bin\bash.exe`. The helper `_win_to_msys2()` in `setup.py`
  converts Windows paths (e.g. `C:\foo`) to MSYS2 format (`/c/foo`).
- **`CIBW_BUILD` targets `cp313-*` and `pp3*-*`.** Only CPython 3.13 and
  PyPy 3 wheels are built in CI. The wheel itself is `py3-none` so it runs on
  any Python ≥ 3.8.
- **Publishing uses OIDC (Trusted Publisher).** No API tokens are stored in
  secrets. Trigger the `wheel.yml` workflow manually and select `pypi` or
  `testpypi` in the **Publish** input.
- **Source repos are cloned into the working directory.** `Clp/`, `CoinUtils/`,
  `Osi/` etc. at the repo root are the cloned COIN-OR source trees used during
  the build. They are not submodules.

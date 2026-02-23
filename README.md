# cbcbox

[![](https://img.shields.io/pypi/v/cbcbox.svg?color=brightgreen)](https://pypi.org/pypi/cbcbox/)

**cbcbox** is a Python wheel distribution of pre-built, self-contained binaries for the
[CBC](https://github.com/coin-or/Cbc) MILP solver (COIN-OR Branch and Cut),
built from the latest master branch of the COIN-OR repositories.

All dynamic dependencies (OpenBLAS, libgfortran, etc.) are bundled inside the
wheel — no system libraries or separate installation steps are needed.

## Supported platforms

| Platform | Wheel tag |
|---|---|
| Linux x86\_64 | `manylinux2014_x86_64` |
| Linux aarch64 | `manylinux2014_aarch64` |
| macOS arm64 (Apple Silicon) | `macosx_11_0_arm64` |
| macOS x86\_64 | `macosx_10_9_x86_64` |
| Windows AMD64 | `win_amd64` |

## Installation

```
pip install cbcbox
```

## Usage

### Command line

Invoke the CBC solver directly via the Python module entry point:

```bash
python -m cbcbox mymodel.lp -solve -quit
python -m cbcbox mymodel.mps.gz -solve -quit
python -m cbcbox mymodel.mps -solve -quit -sec 60
```

CBC accepts LP, MPS and compressed MPS (`.mps.gz`) files. Pass `-help` for the
full list of options, or `-quit` to exit after solving.

### Python API

The package exposes helpers to locate the installed files:

```python
import cbcbox
import subprocess

# Path to the cbc binary (cbc.exe on Windows).
cbcbox.cbc_bin_path()
# e.g. '/home/user/.venv/lib/python3.13/site-packages/cbcbox/cbc_dist/bin/cbc'

# Directory containing the static and dynamic libraries.
cbcbox.cbc_lib_dir()
# e.g. '.../cbcbox/cbc_dist/lib'

# Directory containing the COIN-OR C/C++ headers.
cbcbox.cbc_include_dir()
# e.g. '.../cbcbox/cbc_dist/include/coin'

# Run CBC programmatically.
result = subprocess.run(
    [cbcbox.cbc_bin_path(), "mymodel.mps", "-solve", "-quit"],
    capture_output=True, text=True,
)
print(result.stdout)
```

## What is built

The build pipeline compiles all components from source inside the CI runner,
in the following order:

| Component | Version / branch | Purpose |
|---|---|---|
| **OpenBLAS** | v0.3.31 | Optimised BLAS/LAPACK for LP basis factorisation |
| **AMD** (SuiteSparse v7.12.2) | v7.12.2 | Sparse matrix fill-reducing ordering |
| **Nauty** | 2.8.9 | Symmetry detection for MIP presolve |
| **CoinUtils** | master | Utility library (shared by all COIN-OR packages) |
| **Osi** | master | Open Solver Interface |
| **Clp** | master | Simplex LP solver (used as the MIP node relaxation) |
| **Cgl** | master | Cut generation library |
| **Cbc** | master | Branch-and-cut MIP solver |

All COIN-OR components are linked **statically** into the final binaries.
OpenBLAS is shipped as a shared library and bundled inside the wheel.

## Wheel contents

The wheel installs under `cbcbox/cbc_dist/` inside the site-packages directory.
The layout is:

```
cbc_dist/
├── bin/
│   ├── cbc           # CBC MIP solver binary  (cbc.exe on Windows)
│   └── clp           # Clp LP solver binary   (clp.exe on Windows)
├── lib/
│   ├── libCbc.a                 # CBC solver (static)
│   ├── libCbcSolver.a           # CBC solver front-end (static)
│   ├── libClp.a                 # Clp LP solver (static)
│   ├── libCgl.a                 # Cut generation (static)
│   ├── libOsi.a                 # Solver interface (static)
│   ├── libOsiClp.a              # Clp OSI binding (static)
│   ├── libOsiCbc.a              # CBC OSI binding (static)
│   ├── libCoinUtils.a           # COIN-OR utilities (static)
│   ├── libamd.a                 # AMD sparse ordering (static)
│   ├── libsuitesparseconfig.a   # SuiteSparse config (static)
│   ├── libnauty.a               # Nauty symmetry detection (static)
│   ├── libopenblas.a            # OpenBLAS BLAS/LAPACK (static)
│   ├── pkgconfig/               # .pc files for all libraries
│   └── <bundled shared libs>    # Platform-specific — see below
└── include/
    ├── coin/      # COIN-OR headers (CoinUtils, Osi, Clp, Cgl, Cbc)
    ├── nauty/     # Nauty headers
    └── *.h        # SuiteSparse / AMD headers
```

### Bundled dynamic libraries

Because the static COIN-OR libraries link to OpenBLAS, which in turn links to
the Fortran runtime, the following shared libraries are bundled inside the wheel
and their paths are rewritten so no system installation is required.

#### Linux (`lib/` directory, RPATH set to `$ORIGIN`)

| Library | Description |
|---|---|
| `libopenblas.so.0` | OpenBLAS BLAS/LAPACK |
| `libgfortran.so.5` | GNU Fortran runtime |
| `libquadmath.so.0` | Quad-precision math (dependency of libgfortran) |

#### macOS (`lib/` directory, install names rewritten to `@rpath/`)

| Library | Description |
|---|---|
| `libopenblas.dylib` | OpenBLAS BLAS/LAPACK |
| `libgfortran.5.dylib` | GNU Fortran runtime |
| `libgcc_s.1.1.dylib` | GCC runtime |
| `libquadmath.0.dylib` | Quad-precision math |

#### Windows (`bin/` directory, DLLs placed next to the executable)

| Library | Description |
|---|---|
| `libopenblas.dll` | OpenBLAS BLAS/LAPACK |
| `libgfortran-5.dll` | GNU Fortran runtime |
| `libgcc_s_seh-1.dll` | GCC SEH runtime |
| `libquadmath-0.dll` | Quad-precision math |
| `libstdc++-6.dll` | C++ standard library (MinGW64) |
| `libwinpthread-1.dll` | POSIX thread emulation |

## CI / build pipeline

Wheels are built and tested automatically via GitHub Actions using
[cibuildwheel](https://cibuildwheel.pypa.io).  The workflow
(`.github/workflows/wheel.yml`) runs on five separate runners:

| Runner | Produces |
|---|---|
| `ubuntu-latest` | `manylinux2014_x86_64` wheel |
| `ubuntu-24.04-arm` | `manylinux2014_aarch64` wheel |
| `macos-15` | `macosx_11_0_arm64` wheel |
| `macos-15-intel` | `macosx_10_9_x86_64` wheel |
| `windows-latest` | `win_amd64` wheel |

After each wheel is built, the test suite in `tests/` is run against the
installed wheel to verify correctness.

### Integration tests

The test suite (`pytest`) solves two MIP instances and checks the optimal
objective values:

| Instance | Rows | Columns | Expected optimal |
|---|---|---|---|
| `pp08a.mps.gz` | 240 | 182 | 7350 |
| `sprint_hidden06_j.mps.gz` | 3694 | 10210 | 130 |

### Publishing

To publish wheels to PyPI, trigger the workflow manually and select
`pypi` (or `testpypi`) in the **Publish** input.  Trusted Publisher
(OIDC) authentication is used — no API tokens are stored as secrets.

## License

CBC and all COIN-OR components are distributed under the
[Eclipse Public License 2.0](https://opensource.org/licenses/EPL-2.0).
OpenBLAS is distributed under the BSD 3-Clause licence.
SuiteSparse AMD is distributed under the BSD 3-Clause licence.
Nauty is distributed under the Apache 2.0 licence.


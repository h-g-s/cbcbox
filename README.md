# cbcbox

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

> **Note:** cbcbox is not yet published to PyPI. Use the manual installation
> instructions below to install directly from the pre-built wheel artifacts.

### Installing from a pre-built wheel (recommended)

1. Go to the [Actions tab](../../actions/workflows/wheel.yml) of this repository.
2. Open the latest successful workflow run.
3. Download the artifact matching your platform:

   | Artifact name | Platform |
   |---|---|
   | `cibw-wheels-Linux-X64` | Linux x86\_64 |
   | `cibw-wheels-Linux-ARM64` | Linux aarch64 |
   | `cibw-wheels-macOS-ARM64` | macOS Apple Silicon |
   | `cibw-wheels-macOS-X64` | macOS x86\_64 |
   | `cibw-wheels-Windows-X64` | Windows AMD64 |

4. Unzip the artifact and install the `.whl` file:

   ```bash
   pip install cbcbox-*.whl
   ```

### Installing from PyPI (once available)

```
pip install cbcbox
```

## Usage

### Command line

Invoke the CBC solver directly via the Python module entry point:

```bash
python -m cbcbox mymodel.lp -solve -quit
python -m cbcbox mymodel.mps.gz -solve -quit
python -m cbcbox mymodel.mps -seconds 60 -timem elapsed -solve -quit
python -m cbcbox mymodel.mps -dualp pesteep -solve -quit
```

CBC accepts LP, MPS and compressed MPS (`.mps.gz`) files. Pass `-help` for the
full list of options, or `-quit` to exit after solving.

Parallel branch-and-cut is supported — use `-threads=N` to enable it:

```bash
python -m cbcbox mymodel.mps -threads=4 -solve -quit
```

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
| **Cbc** | master | Branch-and-cut MIP solver |
| **Cgl** | master | Cut generation library |
| **Clp** | master | Simplex LP solver (used as the MIP node relaxation) |
| **Osi** | master | Open Solver Interface |
| **CoinUtils** | master | Utility library (shared by all COIN-OR packages) |
| **Nauty** | 2.8.9 | Symmetry detection for MIP presolve |
| **AMD** (SuiteSparse v7.12.2) | v7.12.2 | Sparse matrix fill-reducing ordering |
| **OpenBLAS** | v0.3.31 | Optimised BLAS/LAPACK for LP basis factorisation |

All COIN-OR components are linked into both **static** (`.a`) and **shared**
(`.so` / `.dylib`) libraries on Linux and macOS. On Windows only **shared**
libraries (`.dll`) are produced — MinGW's autotools does not support building
static and DLL simultaneously. The shared libraries are patched with
self-relative RPATHs and bundled inside the wheel, making them directly usable
via `cffi` or `ctypes` without any system installation.

## Wheel contents

The wheel installs under `cbcbox/cbc_dist/` inside the site-packages directory.
The layout is:

```
cbc_dist/
├── bin/
│   ├── cbc           # CBC MIP solver binary  (cbc.exe on Windows)
│   └── clp           # Clp LP solver binary   (clp.exe on Windows)
├── lib/
│   ├── libCbc.a / libCbc.so            # CBC solver
│   ├── libCbcSolver.a / libCbcSolver.so
│   ├── libClp.a / libClp.so            # Clp LP solver
│   ├── libCgl.a / libCgl.so            # Cut generation
│   ├── libOsi.a / libOsi.so            # Solver interface
│   ├── libOsiClp.a / libOsiClp.so      # Clp OSI binding
│   ├── libOsiCbc.a / libOsiCbc.so      # CBC OSI binding (where available)
│   ├── libCoinUtils.a / libCoinUtils.so
│   ├── libamd.a                        # AMD sparse ordering (static only)
│   ├── libsuitesparseconfig.a          # SuiteSparse config (static only)
│   ├── libnauty.a                      # Nauty (static only)
│   ├── libopenblas.a / libopenblas.so  # OpenBLAS BLAS/LAPACK
│   ├── pkgconfig/                      # .pc files for all libraries
│   └── <bundled runtime shared libs>   # Platform-specific — see below
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
objective values, both in single-threaded and parallel (2-thread) modes:

| Test | Instance | Expected optimal |
|---|---|---|
| `test_solve[pp08a]` | `pp08a.mps.gz` (240×182) | 7350 |
| `test_solve[sprint_hidden06_j]` | `sprint_hidden06_j.mps.gz` (3694×10210) | 130 |
| `test_solve_parallel[pp08a]` | same, `-threads=3` | 7350 |
| `test_solve_parallel[sprint_hidden06_j]` | same, `-threads=3` | 130 |

The parallel tests verify that `--enable-cbc-parallel` is functional.

### Publishing to PyPI

> **Note:** cbcbox is not yet registered on PyPI.  When ready, trigger the
> workflow manually and select `pypi` (or `testpypi`) in the **Publish** input.
> Trusted Publisher (OIDC) authentication is used — no API tokens are stored as
> secrets.

## License

CBC and all COIN-OR components are distributed under the
[Eclipse Public License 2.0](https://opensource.org/licenses/EPL-2.0).
OpenBLAS is distributed under the BSD 3-Clause licence.
SuiteSparse AMD is distributed under the BSD 3-Clause licence.
Nauty is distributed under the Apache 2.0 licence.


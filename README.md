# cbcbox

**cbcbox** is a Python wheel distribution of pre-built, self-contained binaries for the
[CBC](https://github.com/coin-or/Cbc) MILP solver (COIN-OR Branch and Cut),
built from the latest master branch of the COIN-OR repositories.

All dynamic dependencies (OpenBLAS, libgfortran, etc.) are bundled inside the
wheel — no system libraries or separate installation steps are needed.

### Highlights

- **Parallel branch-and-cut** — built with `--enable-cbc-parallel`. Use `-threads=N` to
  solve with multiple threads. CBC distributes the branch-and-bound tree across threads,
  giving significant speedups on multi-core machines for hard MIP instances.

- **AMD fill-reducing ordering** — SuiteSparse AMD is compiled in, enabling the
  high-quality `UniversityOfFlorida` Cholesky factorization for Clp's barrier (interior
  point) solver. Compared to the built-in native Cholesky, AMD reordering produces much
  less fill-in on large sparse problems, making barrier substantially faster.
  Activate it with `-barrier -cholesky UniversityOfFlorida` (see [barrier usage](#barrier-interior-point-solver) below).

- **Optimised BLAS** — linked against OpenBLAS for fast dense linear algebra.
  The generic build uses OpenBLAS `DYNAMIC_ARCH=1` (runtime CPU dispatch) for
  maximum portability; an additional **AVX2-optimised build** is included on
  x86_64 Linux and macOS (see [Build variants](#build-variants) below).

## Build variants

On **x86_64 Linux and macOS**, the wheel ships two complete sets of binaries:

| Variant | OpenBLAS kernel | Clp SIMD | Minimum CPU |
|---|---|---|---|
| `generic` | `DYNAMIC_ARCH` (runtime dispatch) | standard | any x86_64 |
| `avx2` | `HASWELL` (256-bit AVX2/FMA) | `DCOIN_AVX2=4` (4-double AVX2 layout) | Haswell (2013+) |

At import time `cbcbox` automatically selects `avx2` when it is available **and**
the running CPU supports AVX2; otherwise it falls back to `generic`.

You can override this selection with the `CBCBOX_BUILD` environment variable:

```bash
# Force generic (portable) build
CBCBOX_BUILD=generic python -m cbcbox mymodel.mps -solve -quit

# Force AVX2-optimised build (raises an error if not available)
CBCBOX_BUILD=avx2 python -m cbcbox mymodel.mps -solve -quit
```

When `CBCBOX_BUILD` is set, a short summary of the selected build is printed to
stdout on every call — useful for tagging experiment results:

```
[cbcbox] CBCBOX_BUILD=avx2
[cbcbox]   binary  : .../cbcbox/cbc_dist_avx2/bin/cbc
[cbcbox]   lib dir : .../cbcbox/cbc_dist_avx2/lib
[cbcbox]   libs    : libCbc.so.3, libClp.so.3, libopenblas.so.0
```

> **Non-x86_64 platforms** (Linux aarch64, macOS arm64, Windows AMD64) ship
> only the `generic` build. `CBCBOX_BUILD=avx2` will raise a `RuntimeError` on
> those platforms.

## Supported platforms

| Platform | Wheel tag |
|---|---|
| Linux x86\_64 | `manylinux2014_x86_64` |
| Linux aarch64 | `manylinux2014_aarch64` |
| macOS arm64 (Apple Silicon) | `macosx_11_0_arm64` |
| macOS x86\_64 | `macosx_10_9_x86_64` |
| Windows AMD64 | `win_amd64` |

## Installation

> **Note:** cbcbox is now available on PyPI — `pip install cbcbox`.
> Pre-built wheel artifacts are also available from the CI runs (see below).

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

### Installing from PyPI

```bash
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

#### Parallel branch-and-cut

This build includes parallel branch-and-cut (`--enable-cbc-parallel`).
Use `-threads=N` to distribute the search tree across N threads:

```bash
python -m cbcbox mymodel.mps -threads=4 -timem elapsed -solve -quit
```

Use `-timem elapsed` when running parallel so that time limits and reported
times reflect wall-clock seconds rather than CPU-time (which would be ~N× the
wall time).

#### Barrier (interior-point) solver

Clp's barrier solver can be faster than simplex for large LP relaxations.
This build includes SuiteSparse AMD, which enables the high-quality
`UniversityOfFlorida` Cholesky factorization — significantly reducing fill-in
compared to the built-in native Cholesky:

```bash
# Solve LP relaxation with barrier + AMD Cholesky, then crossover to simplex basis
python -m cbcbox mymodel.mps -barrier -cholesky UniversityOfFlorida -solve -quit

# Useful as a root-node strategy inside MIP (let CBC use simplex for B&B):
python -m cbcbox mymodel.mps -barrier -cholesky UniversityOfFlorida -solve -quit
```

Without AMD, only `-cholesky native` (less efficient) is available.

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

On x86_64 Linux and macOS the entire stack is compiled **twice**: once for the
`generic` variant (OpenBLAS `DYNAMIC_ARCH=1`) and once for the `avx2` variant
(`TARGET=HASWELL`, `CXXFLAGS=-O3 -mavx2 -mfma -DCOIN_AVX2=4`).  AMD and Nauty
are built only once (they are pure combinatorial code with no BLAS dependency)
and reused by both COIN-OR variants.

All COIN-OR components are linked into both **static** (`.a`) and **shared**
(`.so` / `.dylib`) libraries on Linux and macOS. On Windows only **shared**
libraries (`.dll`) are produced — MinGW's autotools does not support building
static and DLL simultaneously. The shared libraries are patched with
self-relative RPATHs and bundled inside the wheel, making them directly usable
via `cffi` or `ctypes` without any system installation.

## Wheel contents

The wheel installs under `cbcbox/` inside the site-packages directory.
On x86_64 Linux and macOS it contains **two** dist trees; other platforms
contain only `cbc_dist/`:

```
cbc_dist/           ← generic build (all platforms)
cbc_dist_avx2/      ← AVX2-optimised build (x86_64 Linux/macOS only)
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
│   ├── libamd.a                        # AMD sparse ordering (static only, generic only)
│   ├── libsuitesparseconfig.a          # SuiteSparse config (static only, generic only)
│   ├── libnauty.a                      # Nauty (static only, generic only)
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

The test suite (`pytest`) solves three MIP instances and checks the optimal
objective values, in both single-threaded and parallel (3-thread) modes.
On x86_64 Linux and macOS **each test is run twice** — once against the
`generic` binary and once against the `avx2` binary — and a side-by-side
performance comparison is recorded:

| Test | Instance | Expected optimal |
|---|---|---|
| `test_solve[pp08a-generic]` | `pp08a.mps.gz` (240×182) | 7350 |
| `test_solve[pp08a-avx2]` | same, AVX2 build | 7350 |
| `test_solve[sprint_hidden06_j-generic]` | `sprint_hidden06_j.mps.gz` (3694×10210) | 130 |
| `test_solve[air04-generic]` | `air04.mps.gz` | 56137 |
| `test_solve_parallel[pp08a-generic]` | same, `-threads=3` | 7350 |
| … | … | … |

The `perf_report.md` artifact produced by each CI run includes a table like:

```
| Instance            | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| pp08a.mps.gz        | 2.10        | 1.65      | 1.27×        |
| air04.mps.gz        | 45.3        | 36.1      | 1.25×        |
```

The combined cross-platform report (uploaded as `perf-report-combined`) adds a
**Build** column so generic and AVX2 rows appear side-by-side for each platform.

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


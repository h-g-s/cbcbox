# cbcbox

[![PyPI version](https://img.shields.io/pypi/v/cbcbox.svg?color=brightgreen)](https://pypi.org/project/cbcbox/)
[![PyPI downloads](https://img.shields.io/pypi/dm/cbcbox.svg?color=blue)](https://pypi.org/project/cbcbox/)
[![CI](https://github.com/h-g-s/cbcbox/actions/workflows/wheel.yml/badge.svg)](https://github.com/h-g-s/cbcbox/actions/workflows/wheel.yml)
[![Platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20macOS%20%7C%20Windows-informational)](https://pypi.org/project/cbcbox/)
[![License](https://img.shields.io/badge/license-EPL--2.0-blue.svg)](https://opensource.org/licenses/EPL-2.0)

**cbcbox** is a high-performance, self-contained Python distribution of the
[CBC](https://github.com/coin-or/Cbc) MILP solver (COIN-OR Branch and Cut),
built from the latest COIN-OR master branch.

On x86_64 (Linux, macOS, Windows) the wheel ships both a **[Haswell](https://en.wikipedia.org/wiki/Haswell_(microarchitecture))-optimised** binary
([AVX2](https://en.wikipedia.org/wiki/Advanced_Vector_Extensions)/[FMA](https://en.wikipedia.org/wiki/FMA_instruction_set)) for maximum speed and a **generic** build with
runtime CPU dispatch for compatibility with any x86_64 machine — selected automatically.
All dynamic dependencies ([OpenBLAS](https://github.com/OpenMathLib/OpenBLAS), libgfortran, etc.) are bundled; no system libraries
or separate installation steps are needed.

### Highlights

- **Haswell-optimised & generic builds** — on x86_64 Linux, macOS, and Windows the wheel
  ships two complete solver stacks: a *Haswell* build (OpenBLAS AVX2/FMA kernel) for
  maximum throughput, and a *generic* build (`DYNAMIC_ARCH` runtime dispatch) for
  compatibility with any x86_64 CPU. The best available variant is selected
  automatically at import time (see [Build variants](#build-variants)).

- **Parallel branch-and-cut** — built with `--enable-cbc-parallel`. Use `-threads=N` to
  distribute the search tree across N threads, giving significant speedups on multi-core
  machines for hard MIP instances.

- **AMD fill-reducing ordering** — [SuiteSparse AMD](https://github.com/DrTimothyAldenDavis/SuiteSparse) is compiled in, enabling the
  high-quality `UniversityOfFlorida` Cholesky factorization for Clp's barrier (interior
  point) solver. AMD reordering produces much less fill-in on large sparse problems than
  the built-in native Cholesky, making barrier substantially faster.
  Activate with `-cholesky UniversityOfFlorida -barrier` (see [barrier usage](#barrier-interior-point-solver)).

## Performance (x86\_64)

> *Auto-updated by CI after each successful [workflow run](../../actions/workflows/wheel.yml).
> Single-threaded solve time — lower is better.*

<!-- PERF_SPEEDUP_START -->

The AVX2/Haswell build is **~3.1×** faster than the generic build on average (geometric mean across 30 instances, 2 x86_64 platforms: Darwin x86_64, Windows AMD64).

<!-- PERF_SPEEDUP_END -->

<!-- PERF_PLOT_START -->

![CBC solve time — generic vs AVX2/Haswell (Linux x86_64)](https://raw.githubusercontent.com/h-g-s/cbcbox/master/docs/perf_avx2_speedup.png)

*Single-threaded solve time across benchmark instances on Linux x86_64, sorted by solve time. Speedup factor shown above each pair. Lower is better.*

See also: [Windows AMD64 + macOS x86_64 summary](https://raw.githubusercontent.com/h-g-s/cbcbox/master/docs/perf_avx2_other.png)

<!-- PERF_PLOT_END -->

## Build variants

On **x86_64 Linux, macOS, and Windows**, the wheel ships two complete sets of binaries:

| Variant | OpenBLAS kernel | Clp SIMD | Minimum CPU |
|---|---|---|---|
| `generic` | `DYNAMIC_ARCH=1` (runtime dispatch, Nehalem–Zen targets) | standard | any x86_64 |
| `avx2` | `DYNAMIC_ARCH=1` + `DYNAMIC_LIST=HASWELL SKYLAKEX` | `-march=haswell -DCOIN_AVX2=4` | Haswell (2013+) |

At import time `cbcbox` automatically selects `avx2` when it is available **and**
the running CPU supports AVX2; otherwise it falls back to `generic`.

You can override this selection with the `CBCBOX_BUILD` environment variable:

```bash
# Force generic (portable) build
CBCBOX_BUILD=generic cbc mymodel.mps -solve -quit

# Force AVX2-optimised build (raises an error if not available)
CBCBOX_BUILD=avx2 cbc mymodel.mps -solve -quit
```

When `CBCBOX_BUILD` is set, a short summary of the selected build is printed to
stdout on every call — useful for tagging experiment results:

```
[cbcbox] CBCBOX_BUILD=avx2
[cbcbox]   binary  : .../cbcbox/cbc_dist_avx2/bin/cbc
[cbcbox]   lib dir : .../cbcbox/cbc_dist_avx2/lib
[cbcbox]   libs    : libCbc.so.3, libClp.so.3, libopenblas.so.0
```

> **Non-x86_64 platforms** (Linux aarch64, macOS arm64) ship the `generic`
> build only.  `CBCBOX_BUILD=avx2` will raise a `RuntimeError` on those
> platforms.

## Supported platforms

| Platform | Wheel tag |
|---|---|
| Linux x86\_64 | `manylinux2014_x86_64` |
| Linux aarch64 | `manylinux2014_aarch64` |
| macOS arm64 (Apple Silicon) | `macosx_11_0_arm64` |
| macOS x86\_64 | `macosx_10_9_x86_64` |
| Windows AMD64 | `win_amd64` |

## Installation

```bash
pip install cbcbox
```

## Usage

### Command line

After installation, CBC is available directly as the `cbc` command (pip installs
the entry point into the environment's `bin/` on Linux/macOS or `Scripts/` on Windows,
which is already on PATH):

```bash
cbc mymodel.lp -solve -quit
cbc mymodel.mps.gz -solve -quit
cbc mymodel.mps -seconds 60 -timem elapsed -solve -quit
cbc mymodel.mps -dualp pesteep -solve -quit
```

Alternatively, invoke via the Python module entry point:

```bash
python -m cbcbox mymodel.lp -solve -quit
```

CBC accepts LP, MPS and compressed MPS (`.mps.gz`) files. Pass `-help` for the
full list of options, or `-quit` to exit after solving.

#### Parallel branch-and-cut

This build includes parallel branch-and-cut (`--enable-cbc-parallel`).
Use `-threads=N` to distribute the search tree across N threads:

```bash
cbc mymodel.mps -threads=4 -solve -quit
```

#### Barrier (interior-point) solver

Clp's barrier solver can be faster than simplex for large LP relaxations.
This build includes SuiteSparse AMD, which enables the high-quality
`UniversityOfFlorida` Cholesky factorization — significantly reducing fill-in
compared to the built-in native Cholesky:

```bash
# Solve LP relaxation with barrier + AMD Cholesky, then crossover to simplex basis
cbc mymodel.mps -cholesky UniversityOfFlorida -barrier -solve -quit

# Useful as a root-node strategy inside MIP (let CBC use simplex for B&B):
cbc mymodel.mps -cholesky UniversityOfFlorida -barrier -solve -quit
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

# Directory containing the shared libraries.
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
| **[Nauty](https://pallini.di.uniroma1.it/)** | 2.8.9 | Symmetry detection for MIP presolve |
| **[AMD](https://github.com/DrTimothyAldenDavis/SuiteSparse)** (SuiteSparse v7.12.2) | v7.12.2 | Sparse matrix fill-reducing ordering |
| **[OpenBLAS](https://github.com/OpenMathLib/OpenBLAS)** | v0.3.31 | Optimised BLAS/LAPACK for LP basis factorisation |

On x86_64 Linux, macOS, and Windows the entire stack is compiled **twice**: once for the
`generic` variant (OpenBLAS `DYNAMIC_ARCH=1` with a broad set of x86_64 targets for
runtime dispatch) and once for the `avx2` variant (OpenBLAS `DYNAMIC_ARCH=1` restricted
to Haswell/Skylake targets via `DYNAMIC_LIST`, COIN-OR compiled with
`-march=haswell -DCOIN_AVX2=4`). Both variants use `NO_CBLAS=1` (COIN-OR only calls
the Fortran BLAS interface). AMD and Nauty are built only once (they are pure
combinatorial code with no BLAS dependency) and reused by both COIN-OR variants.

All COIN-OR components are built as **shared** (`.so` / `.dylib` / `.dll`)
libraries. The shared libraries are patched with
self-relative RPATHs and bundled inside the wheel, making them directly usable
via `cffi` or `ctypes` without any system installation.

## Wheel contents

The wheel installs under `cbcbox/` inside the site-packages directory.
On x86_64 Linux, macOS, and Windows it contains **two** dist trees; other platforms
contain only `cbc_dist/`:

```
cbc_dist/           ← generic build (all platforms)
cbc_dist_avx2/      ← AVX2-optimised build (x86_64 Linux/macOS/Windows)
├── bin/
│   ├── cbc           # CBC MIP solver binary  (cbc.exe on Windows)
│   └── clp           # Clp LP solver binary   (clp.exe on Windows)
├── lib/
│   ├── libCbc.so / libCbc.dylib / libCbc.dll  # CBC solver
│   ├── libCbcSolver.so ...
│   ├── libClp.so ...                          # Clp LP solver
│   ├── libCgl.so ...                          # Cut generation
│   ├── libOsi.so ...                          # Solver interface
│   ├── libOsiClp.so ...                       # Clp OSI binding
│   ├── libOsiCbc.so ...                       # CBC OSI binding (where available)
│   ├── libCoinUtils.so ...
│   ├── libopenblas.so / .dylib / .dll         # OpenBLAS BLAS/LAPACK
│   ├── pkgconfig/                             # .pc files for all libraries
│   └── <bundled runtime shared libs>          # Platform-specific — see below
└── include/
    ├── coin/      # COIN-OR headers (CoinUtils, Osi, Clp, Cgl, Cbc)
    ├── nauty/     # Nauty headers
    └── *.h        # SuiteSparse / AMD headers
```

### Bundled dynamic libraries

Because OpenBLAS links to the Fortran runtime, the following shared libraries are bundled inside the wheel
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
(`.github/workflows/wheel.yml`) runs independent compile jobs in parallel,
then packages each platform:

| Compile jobs | Runner | Produces |
|---|---|---|
| `compile-linux-x64-generic` + `compile-linux-x64-avx2` | `ubuntu-latest` | `manylinux2014_x86_64` wheel |
| `compile-linux-arm64-generic` | `ubuntu-24.04-arm` | `manylinux2014_aarch64` wheel |
| `compile-macos-arm64-generic` | `macos-15` | `macosx_11_0_arm64` wheel |
| `compile-macos-intel-generic` + `compile-macos-intel-avx2` | `macos-15-intel` | `macosx_10_9_x86_64` wheel |
| `compile-windows-generic` + `compile-windows-avx2` | `windows-latest` | `win_amd64` wheel |

Each platform's compile jobs run in parallel. Once all compile jobs for a
platform finish, the corresponding `package-*` job assembles the wheel via
cibuildwheel and runs the test suite against the installed wheel.

A final `combine_reports` job collects per-platform performance results and
commits the updated `README.md` to the repository.

### Integration tests

The test suite (`pytest`) solves 24 MIP instances and checks the optimal
objective values, in both single-threaded and parallel (3-thread) modes.
On x86_64 Linux, macOS, and Windows **each test is run twice** — once against
the `generic` binary and once against the `avx2` binary — and a side-by-side
performance comparison is recorded:

| Instance | Expected optimal | Time limit |
|---|---|---|
| `pp08a` | 7 350 | 2000 s |
| `sprint_hidden06_j` | 130 | 2000 s |
| `air03` | 340 160 | 2000 s |
| `air04` | 56 137 | 2000 s |
| `air05` | 26 374 | 2000 s |
| `nw04` | 16 862 | 2000 s |
| `mzzv11` | −21 718 | 2000 s |
| `trd445c` | −153 419.078836 | 2000 s |
| `nursesched-sprint02` | 58 | 2000 s |
| `stein45` | 30 | 2000 s |
| `neos-810286` | 2 877 | 2000 s |
| `neos-1281048` | 601 | 2000 s |
| `j3050_8` | 1 | 2000 s |
| `qiu` | −132.873136947 | 2000 s |
| `gesa2-o` | 25 779 856.3717 | 2000 s |
| `pk1` | 11 | 2000 s |
| `mas76` | 40 005.054142 | 2000 s |
| `app1-1` | −3 | 2000 s |
| `eil33-2` | 934.007916 | 2000 s |
| `fiber` | 405 935.18 | 2000 s |
| `neos-2987310-joes` | −607 702 988.291 | 2000 s |
| `neos-827175` | 112.00152 | 2000 s |
| `neos-3083819-nubu` | 6307996 | 2000 s |
| `markshare_4_0` | 1 | 2000 s |

Time limits are generous to avoid false failures on slow CI runners.

## Performance results

> *Auto-updated by CI after each successful
> [workflow run](../../actions/workflows/wheel.yml).*

<!-- PERF_RESULTS_START -->

## Summary

Geometric mean solve time (seconds) across all test instances.

### 1 thread

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Darwin x86_64 | 67.39 | 19.86 | 3.39× |
| Darwin arm64 | 42.57 | — | — |
| Windows AMD64 | 60.72 | 21.99 | 2.76× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Darwin x86_64 | 54.21 | 18.85 | 2.88× |
| Darwin arm64 | 38.90 | — | — |
| Windows AMD64 | 50.92 | 20.93 | 2.43× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 4.56 | 14.31 | 0.32× |
| Darwin x86_64 | generic | 9.79 | 13.96 | 0.70× |
| Darwin arm64 | generic | 9.64 | 23.03 | 0.42× |
| Windows AMD64 | avx2 | 5.28 | 16.80 | 0.31× |
| Windows AMD64 | generic | 12.68 | 21.63 | 0.59× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 45.63 | 50.97 | 0.90× |
| Darwin x86_64 | generic | 191.76 | 210.65 | 0.91× |
| Darwin arm64 | generic | 130.45 | 118.53 | 1.10× |
| Windows AMD64 | avx2 | 92.81 | 105.48 | 0.88× |
| Windows AMD64 | generic | 240.15 | 216.40 | 1.11× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 1.64 | 1.67 | 0.98× |
| Darwin x86_64 | generic | 7.16 | 7.02 | 1.02× |
| Darwin arm64 | generic | 4.16 | 3.96 | 1.05× |
| Windows AMD64 | avx2 | 2.92 | 3.16 | 0.92× |
| Windows AMD64 | generic | 7.26 | 6.12 | 1.19× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 50.07 | 36.58 | 1.37× |
| Darwin x86_64 | generic | 131.19 | 77.70 | 1.69× |
| Darwin arm64 | generic | 109.12 | 82.09 | 1.33× |
| Windows AMD64 | avx2 | 43.02 | 38.17 | 1.13× |
| Windows AMD64 | generic | 168.05 | 88.42 | 1.90× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 23.50 | 18.05 | 1.30× |
| Darwin x86_64 | generic | 64.27 | 44.90 | 1.43× |
| Darwin arm64 | generic | 49.46 | 34.84 | 1.42× |
| Windows AMD64 | avx2 | 21.34 | 19.60 | 1.09× |
| Windows AMD64 | generic | 56.56 | 44.95 | 1.26× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 12.22 | 12.67 | 0.96× |
| Darwin x86_64 | generic | 41.82 | 37.00 | 1.13× |
| Darwin arm64 | generic | 35.10 | 34.24 | 1.03× |
| Windows AMD64 | avx2 | 17.35 | 19.93 | 0.87× |
| Windows AMD64 | generic | 64.80 | 60.02 | 1.08× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 119.35 | 71.43 | 1.67× |
| Darwin x86_64 | generic | 603.41 | 330.88 | 1.82× |
| Darwin arm64 | generic | 246.59 | 184.16 | 1.34× |
| Windows AMD64 | avx2 | 132.51 | 158.80 | 0.83× |
| Windows AMD64 | generic | 251.46 | 246.21 | 1.02× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 103.11 | 96.67 | 1.07× |
| Darwin x86_64 | generic | 311.17 | 199.63 | 1.56× |
| Darwin arm64 | generic | 170.21 | 187.60 | 0.91× |
| Windows AMD64 | avx2 | 113.35 | 137.32 | 0.83× |
| Windows AMD64 | generic | 221.54 | 222.21 | 1.00× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 29.77 | 31.22 | 0.95× |
| Darwin x86_64 | generic | 113.48 | 89.04 | 1.27× |
| Darwin arm64 | generic | 83.63 | 89.22 | 0.94× |
| Windows AMD64 | avx2 | 37.79 | 37.74 | 1.00× |
| Windows AMD64 | generic | 105.93 | 78.02 | 1.36× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 8.46 | 8.50 | 1.00× |
| Darwin x86_64 | generic | 28.23 | 15.72 | 1.80× |
| Darwin arm64 | generic | 17.92 | 10.28 | 1.74× |
| Windows AMD64 | avx2 | 8.70 | 8.09 | 1.08× |
| Windows AMD64 | generic | 26.16 | 16.61 | 1.57× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 12.21 | 12.89 | 0.95× |
| Darwin x86_64 | generic | 47.65 | 38.81 | 1.23× |
| Darwin arm64 | generic | 23.70 | 23.92 | 0.99× |
| Windows AMD64 | avx2 | 16.33 | 15.49 | 1.05× |
| Windows AMD64 | generic | 34.23 | 44.68 | 0.77× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 17.98 | 7.39 | 2.43× |
| Darwin x86_64 | generic | 128.26 | 16.92 | 7.58× |
| Darwin arm64 | generic | 36.47 | 16.08 | 2.27× |
| Windows AMD64 | avx2 | 14.38 | 16.22 | 0.89× |
| Windows AMD64 | generic | 36.21 | 26.19 | 1.38× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 3.86 | 3.31 | 1.16× |
| Darwin x86_64 | generic | 7.21 | 7.23 | 1.00× |
| Darwin arm64 | generic | 7.01 | 6.28 | 1.12× |
| Windows AMD64 | avx2 | 2.30 | 2.54 | 0.91× |
| Windows AMD64 | generic | 7.99 | 6.87 | 1.16× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 42.31 | 13.36 | 3.17× |
| Darwin x86_64 | generic | 73.65 | 24.51 | 3.01× |
| Darwin arm64 | generic | 80.63 | 29.20 | 2.76× |
| Windows AMD64 | avx2 | 25.37 | 12.46 | 2.04× |
| Windows AMD64 | generic | 79.29 | 39.26 | 2.02× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 4.70 | 4.41 | 1.07× |
| Darwin x86_64 | generic | 13.09 | 9.43 | 1.39× |
| Darwin arm64 | generic | 8.70 | 7.42 | 1.17× |
| Windows AMD64 | avx2 | 3.67 | 3.58 | 1.03× |
| Windows AMD64 | generic | 10.95 | 11.59 | 0.95× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 33.49 | 41.33 | 0.81× |
| Darwin x86_64 | generic | 98.88 | 57.22 | 1.73× |
| Darwin arm64 | generic | 65.84 | 40.55 | 1.62× |
| Windows AMD64 | avx2 | 37.23 | 30.55 | 1.22× |
| Windows AMD64 | generic | 97.32 | 59.97 | 1.62× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 17.79 | 51.58 | 0.34× |
| Darwin x86_64 | generic | 64.89 | 63.74 | 1.02× |
| Darwin arm64 | generic | 40.24 | 39.83 | 1.01× |
| Windows AMD64 | avx2 | 20.57 | 37.33 | 0.55× |
| Windows AMD64 | generic | 46.98 | 55.66 | 0.84× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 5.65 | 7.48 | 0.76× |
| Darwin x86_64 | generic | 783.14 | 711.91 | 1.10× |
| Darwin arm64 | generic | 12.95 | 176.54 | 0.07× |
| Windows AMD64 | avx2 | 22.73 | 7.24 | 3.14× |
| Windows AMD64 | generic | 88.35 | 35.52 | 2.49× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 37.48 | 22.29 | 1.68× |
| Darwin x86_64 | generic | 173.65 | 88.02 | 1.97× |
| Darwin arm64 | generic | 109.19 | 61.54 | 1.77× |
| Windows AMD64 | avx2 | 46.41 | 23.86 | 1.95× |
| Windows AMD64 | generic | 153.49 | 64.35 | 2.39× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 1.14 | 1.41 | 0.81× |
| Darwin x86_64 | generic | 7.94 | 7.55 | 1.05× |
| Darwin arm64 | generic | 1.89 | 2.17 | 0.87× |
| Windows AMD64 | avx2 | 2.14 | 2.28 | 0.94× |
| Windows AMD64 | generic | 3.73 | 4.03 | 0.92× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 21.51 | 22.21 | 0.97× |
| Darwin x86_64 | generic | 130.41 | 114.65 | 1.14× |
| Darwin arm64 | generic | 76.45 | 84.96 | 0.90× |
| Windows AMD64 | avx2 | 26.53 | 26.95 | 0.98× |
| Windows AMD64 | generic | 87.48 | 88.10 | 0.99× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 15.41 | 16.80 | 0.92× |
| Darwin x86_64 | generic | 52.55 | 43.87 | 1.20× |
| Darwin arm64 | generic | 30.44 | 34.56 | 0.88× |
| Windows AMD64 | avx2 | 12.35 | 12.69 | 0.97× |
| Windows AMD64 | generic | 44.98 | 45.49 | 0.99× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 21.32 | 13.75 | 1.55× |
| Darwin x86_64 | generic | 51.11 | 59.61 | 0.86× |
| Darwin arm64 | generic | 38.45 | 17.00 | 2.26× |
| Windows AMD64 | avx2 | 45.23 | 11.32 | 4.00× |
| Windows AMD64 | generic | 212.22 | 68.76 | 3.09× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 22.44 | 226.64 | 0.10× |
| Darwin x86_64 | generic | 61.35 | 224.74 | 0.27× |
| Darwin arm64 | generic | 28.79 | 98.61 | 0.29× |
| Windows AMD64 | avx2 | 20.00 | 92.47 | 0.22× |
| Windows AMD64 | generic | 54.14 | 144.59 | 0.37× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 9.63 | 10.64 | 0.90× |
| Darwin x86_64 | generic | 45.45 | 41.02 | 1.11× |
| Darwin arm64 | generic | 35.10 | 39.35 | 0.89× |
| Windows AMD64 | avx2 | 13.23 | 12.71 | 1.04× |
| Windows AMD64 | generic | 29.06 | 29.45 | 0.99× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 42.52 | 29.48 | 1.44× |
| Darwin x86_64 | generic | 164.82 | 117.94 | 1.40× |
| Darwin arm64 | generic | 91.68 | 66.07 | 1.39× |
| Windows AMD64 | avx2 | 68.45 | 38.06 | 1.80× |
| Windows AMD64 | generic | 145.81 | 118.94 | 1.23× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 63.11 | 21.33 | 2.96× |
| Darwin x86_64 | generic | 28.42 | 34.76 | 0.82× |
| Darwin arm64 | generic | 124.46 | 38.32 | 3.25× |
| Windows AMD64 | avx2 | 32.41 | 17.09 | 1.90× |
| Windows AMD64 | generic | 127.63 | 83.41 | 1.53× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 39.54 | 41.08 | 0.96× |
| Darwin x86_64 | generic | 109.40 | 130.83 | 0.84× |
| Darwin arm64 | generic | 75.24 | 74.63 | 1.01× |
| Windows AMD64 | avx2 | 50.83 | 51.12 | 0.99× |
| Windows AMD64 | generic | 89.41 | 89.86 | 0.99× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 107.38 | 109.24 | 0.98× |
| Darwin x86_64 | generic | 141.13 | 181.26 | 0.78× |
| Darwin arm64 | generic | 223.94 | 231.93 | 0.97× |
| Windows AMD64 | avx2 | 63.32 | 58.92 | 1.07× |
| Windows AMD64 | generic | 134.75 | 133.99 | 1.01× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 135.29 | 29.70 | 4.55× |
| Darwin x86_64 | generic | 121.35 | 83.92 | 1.45× |
| Darwin arm64 | generic | 227.99 | 87.99 | 2.59× |
| Windows AMD64 | avx2 | 67.54 | 66.55 | 1.01× |
| Windows AMD64 | generic | 256.57 | 210.97 | 1.22× |


<!-- PERF_RESULTS_END -->

## NAQ — Never Asked Questions

### Why not benchmark on the full [MIPLIB 2017](https://miplib.zib.de/) library?

Several practical constraints shape the benchmark set:

1. **CI time limits.**  GitHub Actions enforces a 6-hour wall-clock limit per
   job.  The full MIPLIB 2017 collection contains ~240 instances, many of
   which take hours even on fast hardware.  Including all of them would make
   every CI run time out before producing any useful measurements.

2. **Comparing apples to apples requires instances solved to optimality.**  If
   some instances are only solved within a time limit (i.e., a gap > 0 %), a
   meaningful performance comparison must account for both solve time *and*
   solution quality simultaneously.  This greatly complicates analysis and
   makes plots harder to interpret.  Restricting to instances that CBC reliably
   solves to proven optimality keeps the comparison clean: a single elapsed-time
   number per instance is all that is needed.

3. **The instance set is intentionally biased toward set packing / covering /
   partitioning structure.**  Most instances in the benchmark (`pp08a`,
   `sprint_hidden06_j`, `nw04`, `mzzv11`, `nursesched-sprint02`, `air0x`,
   `trd445c`) contain large blocks of set packing, covering, or partitioning
   constraints.  This structure arises naturally in applications such as crew
   scheduling, nurse scheduling, vehicle routing, and cutting stock —
   exactly the domain where [column generation](https://en.wikipedia.org/wiki/Column_generation)
   is most valuable.  Since the benchmark focuses on this problem class rather
   than providing a general-purpose solver survey, it is a specially interesting use case.

## Local debug builds

The released wheels are fully optimised and stripped.  To debug CBC itself
(e.g. with GDB or LLDB), use the scripts in `scripts/` to build a local
debug-enabled binary.  These produce the same full feature set as the release
wheels (OpenBLAS, AMD, Nauty, pthreads) but compiled with `-O1 -g` and, on
x86_64, with `-march=haswell -DCOIN_AVX2=4` so you can debug AVX2-specific
code paths.

| Script | Platform | Environment | Output directory |
|---|---|---|---|
| `scripts/build_debug.sh` | Linux, macOS | native (host compiler) | `cbc_dist_debug_avx2/` (x86_64) or `cbc_dist_debug/` (ARM64) |
| `scripts/build_debug_manylinux.sh` | Linux | Docker — manylinux2014 container (exact CI parity) | same as above |
| `scripts/build_debug_windows.ps1` | Windows | MSYS2 / MinGW64 | `cbc_dist_debug_avx2\` |

### Quick start

**Linux / macOS (native build):**

```bash
# x86_64 → debug + AVX2 → cbc_dist_debug_avx2/bin/cbc
# ARM64  → debug only  → cbc_dist_debug/bin/cbc
./scripts/build_debug.sh

# With AddressSanitizer:
./scripts/build_debug.sh --asan

# With ThreadSanitizer:
./scripts/build_debug.sh --tsan

# Force a clean rebuild from scratch (required when switching sanitizers):
./scripts/build_debug.sh --asan --clean
```

**Linux (manylinux2014 container — matches CI exactly):**

```bash
# Requires Docker; the script prints install instructions if it is missing.
./scripts/build_debug_manylinux.sh
./scripts/build_debug_manylinux.sh --asan
./scripts/build_debug_manylinux.sh --tsan
```

**Windows (PowerShell):**

```powershell
# Requires MSYS2 at C:\msys64.  Note: sanitizers are not supported on Windows/MinGW.
.\scripts\build_debug_windows.ps1
.\scripts\build_debug_windows.ps1 -Clean   # force full rebuild
```

### Debugging

```bash
# GDB (Linux):
gdb cbc_dist_debug_avx2/bin/cbc
(gdb) run mymodel.mps -solve -quit

# LLDB (macOS):
lldb cbc_dist_debug/bin/cbc
(lldb) run mymodel.mps -solve -quit
```

### Sanitizer tips

| Sanitizer | Flag | What it catches | Runtime env var |
|---|---|---|---|
| AddressSanitizer | `--asan` | heap/stack buffer overflows, use-after-free, memory leaks | `ASAN_OPTIONS=detect_leaks=0` to suppress system-lib false positives |
| ThreadSanitizer  | `--tsan` | data races between threads | `TSAN_OPTIONS=halt_on_error=0` to log races without aborting |

ASan and TSan are mutually exclusive.  Neither is available on Windows/MinGW.
Always pass `--clean` when switching from one sanitizer to another to avoid
linking mismatched object files.

OpenBLAS is always built **without** sanitizer flags to avoid false positives
from hand-optimised BLAS assembly; only the COIN-OR stack is instrumented.

> **Note:** Debug binaries are not included in the published wheels because
> of their size.  They are intended for local development only.

## License

CBC and all COIN-OR components are distributed under the
[Eclipse Public License 2.0](https://opensource.org/licenses/EPL-2.0).
OpenBLAS is distributed under the BSD 3-Clause licence.
SuiteSparse AMD is distributed under the BSD 3-Clause licence.
Nauty is distributed under the Apache 2.0 licence.


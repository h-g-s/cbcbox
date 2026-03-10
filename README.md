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

The AVX2/Haswell build is **~3.4×** faster than the generic build on average (geometric mean across 24 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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
| Linux aarch64 | 44.80 | — | — |
| Darwin x86_64 | 69.13 | 21.35 | 3.24× |
| Darwin arm64 | 40.22 | — | — |
| Linux x86_64 | 49.93 | 14.38 | 3.47× |
| Windows AMD64 | — | 16.51 | — |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 35.22 | — | — |
| Darwin x86_64 | 57.56 | 23.24 | 2.48× |
| Darwin arm64 | 34.60 | — | — |
| Linux x86_64 | 38.03 | 13.63 | 2.79× |
| Windows AMD64 | — | 16.86 | — |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 8.92 | 5.81 | 1.54× |
| Darwin x86_64 | avx2 | 6.84 | 12.07 | 0.57× |
| Darwin x86_64 | generic | 13.07 | 11.41 | 1.15× |
| Darwin arm64 | generic | 10.11 | 24.61 | 0.41× |
| Linux x86_64 | avx2 | 4.49 | 8.52 | 0.53× |
| Linux x86_64 | generic | 10.02 | 6.42 | 1.56× |
| Windows AMD64 | avx2 | 4.93 | 8.01 | 0.62× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 218.78 | 202.31 | 1.08× |
| Darwin x86_64 | avx2 | 60.77 | 70.19 | 0.87× |
| Darwin x86_64 | generic | 247.80 | 256.70 | 0.97× |
| Darwin arm64 | generic | 143.39 | 143.21 | 1.00× |
| Linux x86_64 | avx2 | 56.04 | 52.79 | 1.06× |
| Linux x86_64 | generic | 241.21 | 218.60 | 1.10× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.48 | 5.77 | 0.95× |
| Darwin x86_64 | avx2 | 1.80 | 2.56 | 0.70× |
| Darwin x86_64 | generic | 8.53 | 10.18 | 0.84× |
| Darwin arm64 | generic | 4.68 | 4.84 | 0.97× |
| Linux x86_64 | avx2 | 2.02 | 2.11 | 0.96× |
| Linux x86_64 | generic | 6.15 | 6.37 | 0.96× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 138.98 | 74.61 | 1.86× |
| Darwin x86_64 | avx2 | 54.17 | 48.12 | 1.13× |
| Darwin x86_64 | generic | 166.29 | 116.92 | 1.42× |
| Darwin arm64 | generic | 135.47 | 98.40 | 1.38× |
| Linux x86_64 | avx2 | 34.10 | 26.18 | 1.30× |
| Linux x86_64 | generic | 152.73 | 84.24 | 1.81× |
| Windows AMD64 | avx2 | 33.09 | 26.86 | 1.23× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.91 | 35.75 | 1.42× |
| Darwin x86_64 | avx2 | 25.36 | 20.29 | 1.25× |
| Darwin x86_64 | generic | 82.26 | 71.22 | 1.16× |
| Darwin arm64 | generic | 56.57 | 45.57 | 1.24× |
| Linux x86_64 | avx2 | 15.08 | 12.99 | 1.16× |
| Linux x86_64 | generic | 57.40 | 42.59 | 1.35× |
| Windows AMD64 | avx2 | 17.63 | 13.27 | 1.33× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.11 | 40.77 | 0.98× |
| Darwin x86_64 | avx2 | 13.81 | 20.31 | 0.68× |
| Darwin x86_64 | generic | 50.09 | 57.64 | 0.87× |
| Darwin arm64 | generic | 38.24 | 39.95 | 0.96× |
| Linux x86_64 | avx2 | 11.42 | 12.07 | 0.95× |
| Linux x86_64 | generic | 57.40 | 54.88 | 1.05× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 209.78 | 175.60 | 1.19× |
| Darwin x86_64 | avx2 | 128.56 | 105.02 | 1.22× |
| Darwin x86_64 | generic | 642.59 | 548.68 | 1.17× |
| Darwin arm64 | generic | 327.23 | 173.30 | 1.89× |
| Linux x86_64 | avx2 | 131.82 | 122.70 | 1.07× |
| Linux x86_64 | generic | 219.32 | 193.99 | 1.13× |
| Windows AMD64 | avx2 | 119.86 | 277.52 | 0.43× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 202.60 | 203.17 | 1.00× |
| Darwin x86_64 | avx2 | 103.29 | 122.07 | 0.85× |
| Darwin x86_64 | generic | 242.89 | 300.57 | 0.81× |
| Darwin arm64 | generic | 227.38 | 203.70 | 1.12× |
| Linux x86_64 | avx2 | 76.14 | 73.79 | 1.03× |
| Linux x86_64 | generic | 218.17 | 217.21 | 1.00× |
| Windows AMD64 | avx2 | 106.55 | 118.93 | 0.90× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 98.12 | 72.74 | 1.35× |
| Darwin x86_64 | avx2 | 30.80 | 49.13 | 0.63× |
| Darwin x86_64 | generic | 92.85 | 126.74 | 0.73× |
| Darwin arm64 | generic | 92.14 | 100.56 | 0.92× |
| Linux x86_64 | avx2 | 25.32 | 25.39 | 1.00× |
| Linux x86_64 | generic | 109.31 | 82.62 | 1.32× |
| Windows AMD64 | avx2 | 26.94 | 26.77 | 1.01× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.73 | 12.65 | 1.88× |
| Darwin x86_64 | avx2 | 11.58 | 14.14 | 0.82× |
| Darwin x86_64 | generic | 26.33 | 25.15 | 1.05× |
| Darwin arm64 | generic | 21.05 | 13.01 | 1.62× |
| Linux x86_64 | avx2 | 8.25 | 6.58 | 1.25× |
| Linux x86_64 | generic | 26.45 | 16.40 | 1.61× |
| Windows AMD64 | avx2 | 8.55 | 8.89 | 0.96× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 33.64 | 31.48 | 1.07× |
| Darwin x86_64 | avx2 | 16.80 | 19.14 | 0.88× |
| Darwin x86_64 | generic | 44.76 | 49.78 | 0.90× |
| Darwin arm64 | generic | 27.44 | 30.62 | 0.90× |
| Linux x86_64 | avx2 | 20.16 | 19.97 | 1.01× |
| Linux x86_64 | generic | 36.25 | 35.90 | 1.01× |
| Windows AMD64 | avx2 | 13.23 | 12.62 | 1.05× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 31.21 | 15.97 | 1.95× |
| Darwin x86_64 | avx2 | 25.91 | 11.36 | 2.28× |
| Darwin x86_64 | generic | 119.79 | 26.00 | 4.61× |
| Darwin arm64 | generic | 44.12 | 21.22 | 2.08× |
| Linux x86_64 | avx2 | 20.45 | 7.72 | 2.65× |
| Linux x86_64 | generic | 33.12 | 19.71 | 1.68× |
| Windows AMD64 | avx2 | 13.81 | 14.91 | 0.93× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.14 | 5.95 | 1.03× |
| Darwin x86_64 | avx2 | 6.34 | 4.90 | 1.29× |
| Darwin x86_64 | generic | 7.45 | 11.16 | 0.67× |
| Darwin arm64 | generic | 9.78 | 7.42 | 1.32× |
| Linux x86_64 | avx2 | 2.15 | 2.22 | 0.97× |
| Linux x86_64 | generic | 6.88 | 6.82 | 1.01× |
| Windows AMD64 | avx2 | 2.24 | 2.30 | 0.97× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 59.28 | 24.09 | 2.46× |
| Darwin x86_64 | avx2 | 60.84 | 21.06 | 2.89× |
| Darwin x86_64 | generic | 66.10 | 42.05 | 1.57× |
| Darwin arm64 | generic | 98.55 | 31.09 | 3.17× |
| Linux x86_64 | avx2 | 33.27 | 16.84 | 1.98× |
| Linux x86_64 | generic | 62.81 | 30.80 | 2.04× |
| Windows AMD64 | avx2 | 24.24 | 13.71 | 1.77× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 9.94 | 9.03 | 1.10× |
| Darwin x86_64 | avx2 | 6.79 | 6.21 | 1.09× |
| Darwin x86_64 | generic | 13.21 | 14.46 | 0.91× |
| Darwin arm64 | generic | 10.86 | 10.08 | 1.08× |
| Linux x86_64 | avx2 | 3.13 | 3.06 | 1.02× |
| Linux x86_64 | generic | 10.60 | 10.32 | 1.03× |
| Windows AMD64 | avx2 | 3.40 | 3.31 | 1.03× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 88.38 | 49.10 | 1.80× |
| Darwin x86_64 | avx2 | 45.87 | 51.20 | 0.90× |
| Darwin x86_64 | generic | 112.67 | 93.49 | 1.21× |
| Darwin arm64 | generic | 81.35 | 69.57 | 1.17× |
| Linux x86_64 | avx2 | 33.31 | 32.71 | 1.02× |
| Linux x86_64 | generic | 103.06 | 70.67 | 1.46× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 48.39 | 47.61 | 1.02× |
| Darwin x86_64 | avx2 | 25.38 | 75.79 | 0.33× |
| Darwin x86_64 | generic | 63.80 | 96.42 | 0.66× |
| Darwin arm64 | generic | 48.61 | 47.54 | 1.02× |
| Linux x86_64 | avx2 | 19.11 | 24.70 | 0.77× |
| Linux x86_64 | generic | 53.37 | 62.67 | 0.85× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.18 | 49.44 | 0.75× |
| Darwin x86_64 | avx2 | 9.23 | 12.06 | 0.77× |
| Darwin x86_64 | generic | 847.23 | 58.84 | 14.40× |
| Darwin arm64 | generic | 14.21 | 16.30 | 0.87× |
| Linux x86_64 | avx2 | 9.46 | 6.66 | 1.42× |
| Linux x86_64 | generic | 35.94 | 34.27 | 1.05× |
| Windows AMD64 | avx2 | 20.86 | 18.18 | 1.15× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.39 | 61.72 | 2.21× |
| Darwin x86_64 | avx2 | 53.60 | 30.35 | 1.77× |
| Darwin x86_64 | generic | 197.59 | 84.17 | 2.35× |
| Darwin arm64 | generic | 119.86 | 57.13 | 2.10× |
| Linux x86_64 | avx2 | 46.26 | 22.83 | 2.03× |
| Linux x86_64 | generic | 163.17 | 69.22 | 2.36× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 4.36 | 4.46 | 0.98× |
| Darwin x86_64 | avx2 | 2.16 | 1.77 | 1.22× |
| Darwin x86_64 | generic | 9.79 | 7.98 | 1.23× |
| Darwin arm64 | generic | 2.19 | 2.37 | 0.92× |
| Linux x86_64 | avx2 | 0.75 | 0.75 | 0.99× |
| Linux x86_64 | generic | 4.89 | 5.44 | 0.90× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 100.14 | 101.14 | 0.99× |
| Darwin x86_64 | avx2 | 36.28 | 33.59 | 1.08× |
| Darwin x86_64 | generic | 150.55 | 119.44 | 1.26× |
| Darwin arm64 | generic | 88.04 | 83.34 | 1.06× |
| Linux x86_64 | avx2 | 18.52 | 18.15 | 1.02× |
| Linux x86_64 | generic | 108.96 | 113.79 | 0.96× |
| Windows AMD64 | avx2 | 24.91 | 25.25 | 0.99× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 43.32 | 43.79 | 0.99× |
| Darwin x86_64 | avx2 | 24.31 | 27.79 | 0.87× |
| Darwin x86_64 | generic | 56.68 | 45.07 | 1.26× |
| Darwin arm64 | generic | 38.67 | 34.02 | 1.14× |
| Linux x86_64 | avx2 | 13.48 | 13.75 | 0.98× |
| Linux x86_64 | generic | 38.58 | 39.54 | 0.98× |
| Windows AMD64 | avx2 | 12.47 | 12.53 | 1.00× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 189.34 | 39.71 | 4.77× |
| Darwin x86_64 | avx2 | 27.90 | 16.36 | 1.71× |
| Darwin x86_64 | generic | 69.13 | 73.28 | 0.94× |
| Darwin arm64 | generic | 46.60 | 18.79 | 2.48× |
| Linux x86_64 | avx2 | 10.34 | 7.95 | 1.30× |
| Linux x86_64 | generic | 203.50 | 14.56 | 13.97× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 48.09 | 150.43 | 0.32× |
| Darwin x86_64 | avx2 | 34.40 | 300.64 | 0.11× |
| Darwin x86_64 | generic | 81.01 | 188.74 | 0.43× |
| Darwin arm64 | generic | 37.89 | 104.26 | 0.36× |
| Linux x86_64 | avx2 | 19.56 | 87.99 | 0.22× |
| Linux x86_64 | generic | 74.89 | 145.34 | 0.52× |


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


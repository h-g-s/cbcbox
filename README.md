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

The AVX2/Haswell build is **~3.2×** faster than the generic build on average (geometric mean across 30 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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
| Linux aarch64 | 52.98 | — | — |
| Darwin x86_64 | 65.43 | 22.04 | 2.97× |
| Darwin arm64 | 44.77 | — | — |
| Linux x86_64 | 58.58 | 16.70 | 3.51× |
| Windows AMD64 | 60.69 | 19.35 | 3.14× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 42.11 | — | — |
| Darwin x86_64 | 52.76 | 22.68 | 2.33× |
| Darwin arm64 | 41.25 | — | — |
| Linux x86_64 | 49.41 | 15.30 | 3.23× |
| Windows AMD64 | 51.08 | 17.25 | 2.96× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 8.92 | 5.97 | 1.49× |
| Darwin x86_64 | avx2 | 4.77 | 12.70 | 0.38× |
| Darwin x86_64 | generic | 9.20 | 9.71 | 0.95× |
| Darwin arm64 | generic | 9.37 | 15.22 | 0.62× |
| Linux x86_64 | avx2 | 4.49 | 7.53 | 0.60× |
| Linux x86_64 | generic | 9.89 | 8.66 | 1.14× |
| Windows AMD64 | avx2 | 4.93 | 8.51 | 0.58× |
| Windows AMD64 | generic | 13.32 | 19.90 | 0.67× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 217.52 | 201.74 | 1.08× |
| Darwin x86_64 | avx2 | 47.56 | 54.66 | 0.87× |
| Darwin x86_64 | generic | 174.86 | 171.08 | 1.02× |
| Darwin arm64 | generic | 123.33 | 126.70 | 0.97× |
| Linux x86_64 | avx2 | 58.91 | 54.63 | 1.08× |
| Linux x86_64 | generic | 241.22 | 203.51 | 1.19× |
| Windows AMD64 | generic | 250.32 | 278.99 | 0.90× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.58 | 5.79 | 0.96× |
| Darwin x86_64 | avx2 | 1.68 | 1.93 | 0.87× |
| Darwin x86_64 | generic | 6.37 | 6.21 | 1.03× |
| Darwin arm64 | generic | 4.00 | 4.27 | 0.94× |
| Linux x86_64 | avx2 | 2.04 | 2.13 | 0.96× |
| Linux x86_64 | generic | 6.24 | 6.41 | 0.97× |
| Windows AMD64 | generic | 5.99 | 6.44 | 0.93× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 137.63 | 75.68 | 1.82× |
| Darwin x86_64 | avx2 | 50.25 | 38.77 | 1.30× |
| Darwin x86_64 | generic | 118.14 | 75.09 | 1.57× |
| Darwin arm64 | generic | 104.27 | 75.11 | 1.39× |
| Linux x86_64 | avx2 | 34.01 | 25.75 | 1.32× |
| Linux x86_64 | generic | 153.16 | 122.92 | 1.25× |
| Windows AMD64 | avx2 | 32.91 | 27.01 | 1.22× |
| Windows AMD64 | generic | 154.18 | 93.47 | 1.65× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.03 | 35.82 | 1.40× |
| Darwin x86_64 | avx2 | 24.62 | 22.05 | 1.12× |
| Darwin x86_64 | generic | 59.63 | 44.22 | 1.35× |
| Darwin arm64 | generic | 47.31 | 37.76 | 1.25× |
| Linux x86_64 | avx2 | 14.86 | 12.59 | 1.18× |
| Linux x86_64 | generic | 57.16 | 42.25 | 1.35× |
| Windows AMD64 | avx2 | 17.60 | 14.23 | 1.24× |
| Windows AMD64 | generic | 57.47 | 59.22 | 0.97× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 39.44 | 40.77 | 0.97× |
| Darwin x86_64 | avx2 | 12.33 | 14.77 | 0.84× |
| Darwin x86_64 | generic | 37.35 | 37.73 | 0.99× |
| Darwin arm64 | generic | 33.51 | 40.00 | 0.84× |
| Linux x86_64 | avx2 | 11.62 | 12.02 | 0.97× |
| Linux x86_64 | generic | 57.36 | 54.87 | 1.05× |
| Windows AMD64 | generic | 57.12 | 68.52 | 0.83× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 208.46 | 247.74 | 0.84× |
| Darwin x86_64 | avx2 | 122.88 | 91.60 | 1.34× |
| Darwin x86_64 | generic | 527.16 | 344.79 | 1.53× |
| Darwin arm64 | generic | 248.73 | 180.52 | 1.38× |
| Linux x86_64 | avx2 | 133.68 | 151.00 | 0.89× |
| Linux x86_64 | generic | 220.28 | 225.39 | 0.98× |
| Windows AMD64 | avx2 | 119.27 | 141.15 | 0.84× |
| Windows AMD64 | generic | 253.99 | 251.45 | 1.01× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 203.04 | 204.48 | 0.99× |
| Darwin x86_64 | avx2 | 124.89 | 112.72 | 1.11× |
| Darwin x86_64 | generic | 232.07 | 219.29 | 1.06× |
| Darwin arm64 | generic | 181.09 | 201.26 | 0.90× |
| Linux x86_64 | avx2 | 78.91 | 73.05 | 1.08× |
| Linux x86_64 | generic | 222.84 | 222.44 | 1.00× |
| Windows AMD64 | avx2 | 102.69 | 121.22 | 0.85× |
| Windows AMD64 | generic | 235.17 | 232.03 | 1.01× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 97.95 | 72.64 | 1.35× |
| Darwin x86_64 | avx2 | 30.43 | 35.50 | 0.86× |
| Darwin x86_64 | generic | 112.58 | 104.24 | 1.08× |
| Darwin arm64 | generic | 85.77 | 95.90 | 0.89× |
| Linux x86_64 | avx2 | 26.03 | 25.96 | 1.00× |
| Linux x86_64 | generic | 109.29 | 82.17 | 1.33× |
| Windows AMD64 | avx2 | 27.37 | 26.99 | 1.01× |
| Windows AMD64 | generic | 112.40 | 85.33 | 1.32× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.99 | 12.90 | 1.86× |
| Darwin x86_64 | avx2 | 8.75 | 9.90 | 0.88× |
| Darwin x86_64 | generic | 38.58 | 18.84 | 2.05× |
| Darwin arm64 | generic | 19.37 | 14.96 | 1.29× |
| Linux x86_64 | avx2 | 8.31 | 6.96 | 1.20× |
| Linux x86_64 | generic | 26.60 | 18.51 | 1.44× |
| Windows AMD64 | avx2 | 8.55 | 6.67 | 1.28× |
| Windows AMD64 | generic | 26.78 | 17.23 | 1.55× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 33.56 | 38.60 | 0.87× |
| Darwin x86_64 | avx2 | 14.41 | 13.54 | 1.06× |
| Darwin x86_64 | generic | 60.37 | 48.02 | 1.26× |
| Darwin arm64 | generic | 37.06 | 32.77 | 1.13× |
| Linux x86_64 | avx2 | 20.91 | 20.80 | 1.00× |
| Linux x86_64 | generic | 35.97 | 36.18 | 0.99× |
| Windows AMD64 | avx2 | 13.89 | 12.80 | 1.09× |
| Windows AMD64 | generic | 35.50 | 47.01 | 0.76× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 31.28 | 16.26 | 1.92× |
| Darwin x86_64 | avx2 | 20.02 | 7.38 | 2.71× |
| Darwin x86_64 | generic | 147.32 | 18.25 | 8.07× |
| Darwin arm64 | generic | 39.34 | 15.85 | 2.48× |
| Linux x86_64 | avx2 | 20.53 | 7.86 | 2.61× |
| Linux x86_64 | generic | 33.59 | 23.72 | 1.42× |
| Windows AMD64 | avx2 | 13.76 | 23.09 | 0.60× |
| Windows AMD64 | generic | 36.61 | 21.98 | 1.67× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.01 | 5.89 | 1.02× |
| Darwin x86_64 | avx2 | 3.88 | 4.02 | 0.96× |
| Darwin x86_64 | generic | 8.49 | 8.70 | 0.98× |
| Darwin arm64 | generic | 7.58 | 6.43 | 1.18× |
| Linux x86_64 | avx2 | 2.12 | 1.99 | 1.06× |
| Linux x86_64 | generic | 6.86 | 7.00 | 0.98× |
| Windows AMD64 | avx2 | 2.20 | 2.36 | 0.93× |
| Windows AMD64 | generic | 8.32 | 6.99 | 1.19× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 58.99 | 24.37 | 2.42× |
| Darwin x86_64 | avx2 | 48.69 | 15.41 | 3.16× |
| Darwin x86_64 | generic | 73.08 | 30.30 | 2.41× |
| Darwin arm64 | generic | 87.17 | 25.56 | 3.41× |
| Linux x86_64 | avx2 | 33.30 | 14.65 | 2.27× |
| Linux x86_64 | generic | 63.99 | 34.56 | 1.85× |
| Windows AMD64 | avx2 | 24.23 | 11.68 | 2.07× |
| Windows AMD64 | generic | 80.53 | 40.56 | 1.99× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 10.01 | 9.12 | 1.10× |
| Darwin x86_64 | avx2 | 6.53 | 5.95 | 1.10× |
| Darwin x86_64 | generic | 13.47 | 10.06 | 1.34× |
| Darwin arm64 | generic | 9.28 | 8.31 | 1.12× |
| Linux x86_64 | avx2 | 3.20 | 3.02 | 1.06× |
| Linux x86_64 | generic | 10.79 | 10.39 | 1.04× |
| Windows AMD64 | avx2 | 3.44 | 3.32 | 1.04× |
| Windows AMD64 | generic | 11.04 | 10.64 | 1.04× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 87.71 | 54.44 | 1.61× |
| Darwin x86_64 | avx2 | 45.33 | 37.86 | 1.20× |
| Darwin x86_64 | generic | 87.58 | 74.60 | 1.17× |
| Darwin arm64 | generic | 65.76 | 55.65 | 1.18× |
| Linux x86_64 | avx2 | 33.21 | 27.93 | 1.19× |
| Linux x86_64 | generic | 105.24 | 73.49 | 1.43× |
| Windows AMD64 | generic | 103.14 | 72.06 | 1.43× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.83 | 44.67 | 1.07× |
| Darwin x86_64 | avx2 | 25.94 | 47.38 | 0.55× |
| Darwin x86_64 | generic | 52.27 | 76.18 | 0.69× |
| Darwin arm64 | generic | 41.74 | 41.22 | 1.01× |
| Linux x86_64 | avx2 | 19.30 | 26.44 | 0.73× |
| Linux x86_64 | generic | 54.88 | 64.97 | 0.84× |
| Windows AMD64 | generic | 53.26 | 69.55 | 0.77× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 36.62 | 53.21 | 0.69× |
| Darwin x86_64 | avx2 | 7.53 | 69.02 | 0.11× |
| Darwin x86_64 | generic | 808.49 | 31.82 | 25.41× |
| Darwin arm64 | generic | 13.91 | 176.22 | 0.08× |
| Linux x86_64 | avx2 | 9.56 | 6.74 | 1.42× |
| Linux x86_64 | generic | 36.25 | 41.29 | 0.88× |
| Windows AMD64 | avx2 | 20.66 | 7.27 | 2.84× |
| Windows AMD64 | generic | 82.04 | 20.76 | 3.95× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.39 | 56.16 | 2.43× |
| Darwin x86_64 | avx2 | 50.26 | 25.02 | 2.01× |
| Darwin x86_64 | generic | 163.61 | 92.74 | 1.76× |
| Darwin arm64 | generic | 115.95 | 70.94 | 1.63× |
| Linux x86_64 | avx2 | 46.41 | 19.15 | 2.42× |
| Linux x86_64 | generic | 164.24 | 74.38 | 2.21× |
| Windows AMD64 | generic | 165.96 | 73.91 | 2.25× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 4.31 | 4.50 | 0.96× |
| Darwin x86_64 | avx2 | 1.60 | 1.39 | 1.15× |
| Darwin x86_64 | generic | 6.87 | 8.29 | 0.83× |
| Darwin arm64 | generic | 2.10 | 2.47 | 0.85× |
| Linux x86_64 | avx2 | 0.74 | 0.70 | 1.06× |
| Linux x86_64 | generic | 4.96 | 5.25 | 0.94× |
| Windows AMD64 | generic | 3.92 | 4.18 | 0.94× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 98.68 | 100.97 | 0.98× |
| Darwin x86_64 | avx2 | 29.45 | 26.86 | 1.10× |
| Darwin x86_64 | generic | 117.18 | 124.11 | 0.94× |
| Darwin arm64 | generic | 80.90 | 92.75 | 0.87× |
| Linux x86_64 | avx2 | 17.92 | 18.42 | 0.97× |
| Linux x86_64 | generic | 112.65 | 113.29 | 0.99× |
| Windows AMD64 | avx2 | 24.86 | 25.19 | 0.99× |
| Windows AMD64 | generic | 72.41 | 72.85 | 0.99× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 43.88 | 44.16 | 0.99× |
| Darwin x86_64 | avx2 | 17.20 | 19.94 | 0.86× |
| Darwin x86_64 | generic | 42.92 | 48.42 | 0.89× |
| Darwin arm64 | generic | 33.12 | 39.06 | 0.85× |
| Linux x86_64 | avx2 | 13.57 | 13.80 | 0.98× |
| Linux x86_64 | generic | 38.77 | 38.88 | 1.00× |
| Windows AMD64 | avx2 | 12.47 | 12.63 | 0.99× |
| Windows AMD64 | generic | 39.56 | 39.92 | 0.99× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 188.50 | 44.57 | 4.23× |
| Darwin x86_64 | avx2 | 21.83 | 13.47 | 1.62× |
| Darwin x86_64 | generic | 49.53 | 71.30 | 0.69× |
| Darwin arm64 | generic | 41.68 | 22.69 | 1.84× |
| Linux x86_64 | avx2 | 10.71 | 14.45 | 0.74× |
| Linux x86_64 | generic | 202.29 | 73.57 | 2.75× |
| Windows AMD64 | generic | 212.21 | 69.36 | 3.06× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.48 | 154.53 | 0.31× |
| Darwin x86_64 | avx2 | 23.31 | 233.26 | 0.10× |
| Darwin x86_64 | generic | 60.70 | 253.73 | 0.24× |
| Darwin arm64 | generic | 31.29 | 99.87 | 0.31× |
| Linux x86_64 | avx2 | 19.60 | 100.39 | 0.20× |
| Linux x86_64 | generic | 77.34 | 129.21 | 0.60× |
| Windows AMD64 | generic | 68.45 | 160.41 | 0.43× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.62 | 32.36 | 0.95× |
| Darwin x86_64 | avx2 | 9.68 | 11.23 | 0.86× |
| Darwin x86_64 | generic | 46.84 | 45.49 | 1.03× |
| Darwin arm64 | generic | 37.02 | 43.94 | 0.84× |
| Linux x86_64 | avx2 | 7.69 | 7.42 | 1.04× |
| Linux x86_64 | generic | 38.68 | 39.60 | 0.98× |
| Windows AMD64 | generic | 30.37 | 31.00 | 0.98× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 159.32 | 77.22 | 2.06× |
| Darwin x86_64 | avx2 | 44.00 | 31.35 | 1.40× |
| Darwin x86_64 | generic | 169.81 | 121.14 | 1.40× |
| Darwin arm64 | generic | 95.15 | 67.49 | 1.41× |
| Linux x86_64 | avx2 | 62.17 | 33.99 | 1.83× |
| Linux x86_64 | generic | 138.44 | 116.05 | 1.19× |
| Windows AMD64 | generic | 143.60 | 118.80 | 1.21× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 79.46 | 35.56 | 2.23× |
| Darwin x86_64 | avx2 | 66.61 | 34.11 | 1.95× |
| Darwin x86_64 | generic | 29.26 | 63.18 | 0.46× |
| Darwin arm64 | generic | 128.19 | 31.78 | 4.03× |
| Linux x86_64 | avx2 | 24.99 | 10.75 | 2.32× |
| Linux x86_64 | generic | 80.70 | 37.52 | 2.15× |
| Windows AMD64 | avx2 | 27.86 | 10.62 | 2.62× |
| Windows AMD64 | generic | 124.13 | 62.19 | 2.00× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 83.89 | 84.17 | 1.00× |
| Darwin x86_64 | avx2 | 42.45 | 47.97 | 0.88× |
| Darwin x86_64 | generic | 108.04 | 123.81 | 0.87× |
| Darwin arm64 | generic | 71.38 | 71.97 | 0.99× |
| Linux x86_64 | avx2 | 32.81 | 32.24 | 1.02× |
| Linux x86_64 | generic | 84.67 | 85.40 | 0.99× |
| Windows AMD64 | avx2 | 48.34 | 49.33 | 0.98× |
| Windows AMD64 | generic | 89.83 | 90.70 | 0.99× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 187.46 | 186.93 | 1.00× |
| Darwin x86_64 | avx2 | 110.64 | 129.21 | 0.86× |
| Darwin x86_64 | generic | 142.28 | 165.34 | 0.86× |
| Darwin arm64 | generic | 232.41 | 229.25 | 1.01× |
| Linux x86_64 | avx2 | 46.33 | 46.24 | 1.00× |
| Linux x86_64 | generic | 198.92 | 197.59 | 1.01× |
| Windows AMD64 | generic | 135.64 | 136.26 | 1.00× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 227.47 | 127.41 | 1.79× |
| Darwin x86_64 | avx2 | 96.00 | 38.20 | 2.51× |
| Darwin x86_64 | generic | 124.26 | 97.24 | 1.28× |
| Darwin arm64 | generic | 273.30 | 92.93 | 2.94× |
| Linux x86_64 | avx2 | 34.79 | 35.70 | 0.97× |
| Linux x86_64 | generic | 208.38 | 131.48 | 1.58× |
| Windows AMD64 | avx2 | 58.34 | 55.67 | 1.05× |
| Windows AMD64 | generic | 221.82 | 166.01 | 1.34× |


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


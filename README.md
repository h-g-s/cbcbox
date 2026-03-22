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

The AVX2/Haswell build is **~3.0×** faster than the generic build on average (geometric mean across 30 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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
| Linux aarch64 | 53.12 | — | — |
| Darwin x86_64 | 59.25 | 21.46 | 2.76× |
| Darwin arm64 | 47.43 | — | — |
| Linux x86_64 | 58.71 | 17.50 | 3.36× |
| Windows AMD64 | — | 19.41 | — |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 41.32 | — | — |
| Darwin x86_64 | 52.59 | 17.47 | 3.01× |
| Darwin arm64 | 40.91 | — | — |
| Linux x86_64 | 50.20 | 15.90 | 3.16× |
| Windows AMD64 | — | 15.91 | — |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 8.93 | 6.23 | 1.43× |
| Darwin x86_64 | avx2 | 4.75 | 9.05 | 0.52× |
| Darwin x86_64 | generic | 10.51 | 8.28 | 1.27× |
| Darwin arm64 | generic | 9.28 | 16.58 | 0.56× |
| Linux x86_64 | avx2 | 4.88 | 7.89 | 0.62× |
| Linux x86_64 | generic | 9.72 | 5.88 | 1.65× |
| Windows AMD64 | avx2 | 5.04 | 7.86 | 0.64× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 219.74 | 195.30 | 1.13× |
| Darwin x86_64 | avx2 | 49.91 | 45.24 | 1.10× |
| Darwin x86_64 | generic | 174.04 | 180.45 | 0.96× |
| Darwin arm64 | generic | 121.82 | 124.85 | 0.98× |
| Linux x86_64 | avx2 | 61.79 | 59.31 | 1.04× |
| Linux x86_64 | generic | 253.92 | 208.85 | 1.22× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.67 | 5.77 | 0.98× |
| Darwin x86_64 | avx2 | 1.74 | 1.63 | 1.06× |
| Darwin x86_64 | generic | 5.77 | 6.72 | 0.86× |
| Darwin arm64 | generic | 4.00 | 4.22 | 0.95× |
| Linux x86_64 | avx2 | 2.20 | 2.33 | 0.95× |
| Linux x86_64 | generic | 6.92 | 7.12 | 0.97× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 138.88 | 73.52 | 1.89× |
| Darwin x86_64 | avx2 | 51.20 | 33.07 | 1.55× |
| Darwin x86_64 | generic | 108.36 | 74.88 | 1.45× |
| Darwin arm64 | generic | 105.15 | 82.32 | 1.28× |
| Linux x86_64 | avx2 | 35.98 | 27.50 | 1.31× |
| Linux x86_64 | generic | 149.72 | 120.20 | 1.25× |
| Windows AMD64 | avx2 | 35.24 | 26.12 | 1.35× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.44 | 35.03 | 1.44× |
| Darwin x86_64 | avx2 | 24.48 | 16.58 | 1.48× |
| Darwin x86_64 | generic | 53.03 | 43.26 | 1.23× |
| Darwin arm64 | generic | 47.56 | 43.03 | 1.11× |
| Linux x86_64 | avx2 | 15.83 | 13.56 | 1.17× |
| Linux x86_64 | generic | 56.68 | 42.74 | 1.33× |
| Windows AMD64 | avx2 | 17.65 | 13.86 | 1.27× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 39.61 | 41.12 | 0.96× |
| Darwin x86_64 | avx2 | 13.26 | 12.38 | 1.07× |
| Darwin x86_64 | generic | 33.40 | 38.42 | 0.87× |
| Darwin arm64 | generic | 33.91 | 39.68 | 0.85× |
| Linux x86_64 | avx2 | 12.32 | 12.89 | 0.96× |
| Linux x86_64 | generic | 61.90 | 66.13 | 0.94× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 207.11 | 288.36 | 0.72× |
| Darwin x86_64 | avx2 | 126.46 | 70.41 | 1.80× |
| Darwin x86_64 | generic | 522.96 | 377.36 | 1.39× |
| Darwin arm64 | generic | 249.96 | 182.37 | 1.37× |
| Linux x86_64 | avx2 | 140.79 | 121.14 | 1.16× |
| Linux x86_64 | generic | 221.39 | 214.07 | 1.03× |
| Windows AMD64 | avx2 | 119.59 | 157.38 | 0.76× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 203.81 | 205.53 | 0.99× |
| Darwin x86_64 | avx2 | 126.54 | 94.73 | 1.34× |
| Darwin x86_64 | generic | 219.76 | 224.88 | 0.98× |
| Darwin arm64 | generic | 183.56 | 186.34 | 0.99× |
| Linux x86_64 | avx2 | 81.65 | 76.36 | 1.07× |
| Linux x86_64 | generic | 232.11 | 231.11 | 1.00× |
| Windows AMD64 | avx2 | 103.05 | 109.68 | 0.94× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 97.29 | 72.14 | 1.35× |
| Darwin x86_64 | avx2 | 34.14 | 29.61 | 1.15× |
| Darwin x86_64 | generic | 93.45 | 93.91 | 1.00× |
| Darwin arm64 | generic | 86.36 | 93.94 | 0.92× |
| Linux x86_64 | avx2 | 27.32 | 27.28 | 1.00× |
| Linux x86_64 | generic | 114.80 | 87.79 | 1.31× |
| Windows AMD64 | avx2 | 27.09 | 26.62 | 1.02× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.72 | 12.95 | 1.83× |
| Darwin x86_64 | avx2 | 8.93 | 7.19 | 1.24× |
| Darwin x86_64 | generic | 24.78 | 18.12 | 1.37× |
| Darwin arm64 | generic | 19.42 | 10.14 | 1.91× |
| Linux x86_64 | avx2 | 8.84 | 7.18 | 1.23× |
| Linux x86_64 | generic | 26.35 | 17.13 | 1.54× |
| Windows AMD64 | avx2 | 8.53 | 6.81 | 1.25× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 33.13 | 34.22 | 0.97× |
| Darwin x86_64 | avx2 | 12.33 | 12.15 | 1.02× |
| Darwin x86_64 | generic | 43.70 | 39.45 | 1.11× |
| Darwin arm64 | generic | 29.74 | 33.53 | 0.89× |
| Linux x86_64 | avx2 | 21.70 | 21.19 | 1.02× |
| Linux x86_64 | generic | 36.44 | 35.75 | 1.02× |
| Windows AMD64 | avx2 | 13.85 | 12.26 | 1.13× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 31.40 | 18.48 | 1.70× |
| Darwin x86_64 | avx2 | 18.75 | 9.01 | 2.08× |
| Darwin x86_64 | generic | 111.29 | 16.93 | 6.57× |
| Darwin arm64 | generic | 39.63 | 19.22 | 2.06× |
| Linux x86_64 | avx2 | 22.14 | 7.30 | 3.03× |
| Linux x86_64 | generic | 32.43 | 23.31 | 1.39× |
| Windows AMD64 | avx2 | 13.74 | 6.24 | 2.20× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.10 | 5.96 | 1.02× |
| Darwin x86_64 | avx2 | 4.21 | 3.12 | 1.35× |
| Darwin x86_64 | generic | 6.69 | 8.77 | 0.76× |
| Darwin arm64 | generic | 7.69 | 7.26 | 1.06× |
| Linux x86_64 | avx2 | 2.24 | 2.17 | 1.03× |
| Linux x86_64 | generic | 6.77 | 6.83 | 0.99× |
| Windows AMD64 | avx2 | 2.18 | 2.29 | 0.95× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 59.78 | 25.00 | 2.39× |
| Darwin x86_64 | avx2 | 44.53 | 11.66 | 3.82× |
| Darwin x86_64 | generic | 59.89 | 28.14 | 2.13× |
| Darwin arm64 | generic | 94.58 | 29.12 | 3.25× |
| Linux x86_64 | avx2 | 34.48 | 18.02 | 1.91× |
| Linux x86_64 | generic | 57.22 | 35.15 | 1.63× |
| Windows AMD64 | avx2 | 24.35 | 13.28 | 1.83× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 9.97 | 8.96 | 1.11× |
| Darwin x86_64 | avx2 | 5.17 | 4.33 | 1.19× |
| Darwin x86_64 | generic | 11.88 | 11.08 | 1.07× |
| Darwin arm64 | generic | 12.54 | 10.70 | 1.17× |
| Linux x86_64 | avx2 | 3.33 | 3.15 | 1.06× |
| Linux x86_64 | generic | 10.71 | 10.45 | 1.02× |
| Windows AMD64 | avx2 | 3.46 | 3.26 | 1.06× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 88.33 | 52.71 | 1.68× |
| Darwin x86_64 | avx2 | 36.35 | 33.19 | 1.10× |
| Darwin x86_64 | generic | 83.28 | 74.63 | 1.12× |
| Darwin arm64 | generic | 71.35 | 57.38 | 1.24× |
| Linux x86_64 | avx2 | 35.47 | 28.02 | 1.27× |
| Linux x86_64 | generic | 99.34 | 66.98 | 1.48× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 48.02 | 53.30 | 0.90× |
| Darwin x86_64 | avx2 | 19.03 | 40.72 | 0.47× |
| Darwin x86_64 | generic | 48.64 | 80.11 | 0.61× |
| Darwin arm64 | generic | 43.62 | 57.75 | 0.76× |
| Linux x86_64 | avx2 | 20.08 | 29.56 | 0.68× |
| Linux x86_64 | generic | 52.77 | 57.45 | 0.92× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 36.74 | 34.40 | 1.07× |
| Darwin x86_64 | avx2 | 6.25 | 7.30 | 0.86× |
| Darwin x86_64 | generic | 666.61 | 678.60 | 0.98× |
| Darwin arm64 | generic | 15.00 | 18.61 | 0.81× |
| Linux x86_64 | avx2 | 9.91 | 6.63 | 1.49× |
| Linux x86_64 | generic | 35.59 | 53.03 | 0.67× |
| Windows AMD64 | avx2 | 20.59 | 8.37 | 2.46× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.74 | 55.33 | 2.47× |
| Darwin x86_64 | avx2 | 41.05 | 18.77 | 2.19× |
| Darwin x86_64 | generic | 146.48 | 75.50 | 1.94× |
| Darwin arm64 | generic | 121.28 | 69.83 | 1.74× |
| Linux x86_64 | avx2 | 47.51 | 26.57 | 1.79× |
| Linux x86_64 | generic | 169.35 | 73.08 | 2.32× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 4.36 | 4.53 | 0.96× |
| Darwin x86_64 | avx2 | 1.24 | 1.09 | 1.13× |
| Darwin x86_64 | generic | 6.64 | 7.12 | 0.93× |
| Darwin arm64 | generic | 2.28 | 2.08 | 1.09× |
| Linux x86_64 | avx2 | 0.79 | 0.74 | 1.06× |
| Linux x86_64 | generic | 5.11 | 5.35 | 0.96× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 99.11 | 98.19 | 1.01× |
| Darwin x86_64 | avx2 | 26.01 | 21.22 | 1.23× |
| Darwin x86_64 | generic | 111.11 | 108.81 | 1.02× |
| Darwin arm64 | generic | 94.33 | 90.85 | 1.04× |
| Linux x86_64 | avx2 | 18.88 | 18.97 | 1.00× |
| Linux x86_64 | generic | 124.61 | 121.24 | 1.03× |
| Windows AMD64 | avx2 | 24.63 | 24.73 | 1.00× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 43.53 | 42.95 | 1.01× |
| Darwin x86_64 | avx2 | 18.45 | 15.46 | 1.19× |
| Darwin x86_64 | generic | 40.54 | 41.13 | 0.99× |
| Darwin arm64 | generic | 41.25 | 37.61 | 1.10× |
| Linux x86_64 | avx2 | 14.04 | 14.18 | 0.99× |
| Linux x86_64 | generic | 39.26 | 39.73 | 0.99× |
| Windows AMD64 | avx2 | 12.43 | 12.37 | 1.01× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 188.40 | 43.66 | 4.31× |
| Darwin x86_64 | avx2 | 23.32 | 10.11 | 2.31× |
| Darwin x86_64 | generic | 44.75 | 53.80 | 0.83× |
| Darwin arm64 | generic | 49.48 | 23.79 | 2.08× |
| Linux x86_64 | avx2 | 11.68 | 13.00 | 0.90× |
| Linux x86_64 | generic | 197.25 | 71.37 | 2.76× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 46.98 | 139.34 | 0.34× |
| Darwin x86_64 | avx2 | 24.53 | 172.51 | 0.14× |
| Darwin x86_64 | generic | 55.14 | 151.43 | 0.36× |
| Darwin arm64 | generic | 36.69 | 152.10 | 0.24× |
| Linux x86_64 | avx2 | 18.17 | 88.19 | 0.21× |
| Linux x86_64 | generic | 65.39 | 142.35 | 0.46× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.28 | 30.81 | 0.98× |
| Darwin x86_64 | avx2 | 9.36 | 11.07 | 0.85× |
| Darwin x86_64 | generic | 43.07 | 39.74 | 1.08× |
| Darwin arm64 | generic | 41.89 | 43.24 | 0.97× |
| Linux x86_64 | avx2 | 7.91 | 7.59 | 1.04× |
| Linux x86_64 | generic | 40.67 | 41.33 | 0.98× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 160.24 | 77.66 | 2.06× |
| Darwin x86_64 | avx2 | 46.69 | 28.88 | 1.62× |
| Darwin x86_64 | generic | 160.56 | 102.26 | 1.57× |
| Darwin arm64 | generic | 108.26 | 69.53 | 1.56× |
| Linux x86_64 | avx2 | 64.75 | 35.62 | 1.82× |
| Linux x86_64 | generic | 137.02 | 114.57 | 1.20× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 80.23 | 28.17 | 2.85× |
| Darwin x86_64 | avx2 | 72.13 | 24.79 | 2.91× |
| Darwin x86_64 | generic | 27.14 | 35.22 | 0.77× |
| Darwin arm64 | generic | 145.34 | 51.86 | 2.80× |
| Linux x86_64 | avx2 | 26.08 | 9.80 | 2.66× |
| Linux x86_64 | generic | 82.12 | 53.19 | 1.54× |
| Windows AMD64 | avx2 | 27.94 | 12.09 | 2.31× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 84.43 | 83.49 | 1.01× |
| Darwin x86_64 | avx2 | 50.87 | 46.29 | 1.10× |
| Darwin x86_64 | generic | 117.70 | 101.63 | 1.16× |
| Darwin arm64 | generic | 81.34 | 84.50 | 0.96× |
| Linux x86_64 | avx2 | 34.24 | 34.12 | 1.00× |
| Linux x86_64 | generic | 83.20 | 83.52 | 1.00× |
| Windows AMD64 | avx2 | 48.51 | 47.26 | 1.03× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 188.90 | 187.03 | 1.01× |
| Darwin x86_64 | avx2 | 127.30 | 103.15 | 1.23× |
| Darwin x86_64 | generic | 147.00 | 137.05 | 1.07× |
| Darwin arm64 | generic | 250.26 | 260.45 | 0.96× |
| Linux x86_64 | avx2 | 48.85 | 49.11 | 0.99× |
| Linux x86_64 | generic | 201.02 | 199.94 | 1.01× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 228.11 | 134.38 | 1.70× |
| Darwin x86_64 | avx2 | 96.66 | 38.08 | 2.54× |
| Darwin x86_64 | generic | 128.22 | 80.83 | 1.59× |
| Darwin arm64 | generic | 246.02 | 102.92 | 2.39× |
| Linux x86_64 | avx2 | 36.62 | 40.84 | 0.90× |
| Linux x86_64 | generic | 216.33 | 138.45 | 1.56× |
| Windows AMD64 | avx2 | 57.70 | 43.28 | 1.33× |


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


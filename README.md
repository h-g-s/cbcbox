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

The AVX2/Haswell build is **~2.9×** faster than the generic build on average (geometric mean across 30 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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
| Linux aarch64 | 52.94 | — | — |
| Darwin x86_64 | 74.07 | 27.93 | 2.65× |
| Darwin arm64 | 48.11 | — | — |
| Linux x86_64 | 58.68 | 16.60 | 3.53× |
| Windows AMD64 | 60.79 | 22.33 | 2.72× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 40.72 | — | — |
| Darwin x86_64 | 74.30 | 25.19 | 2.95× |
| Darwin arm64 | 38.30 | — | — |
| Linux x86_64 | 47.63 | 15.52 | 3.07× |
| Windows AMD64 | 51.58 | 20.72 | 2.49× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 8.88 | 5.85 | 1.52× |
| Darwin x86_64 | avx2 | 6.50 | 12.65 | 0.51× |
| Darwin x86_64 | generic | 9.32 | 10.22 | 0.91× |
| Darwin arm64 | generic | 10.10 | 16.24 | 0.62× |
| Linux x86_64 | avx2 | 4.49 | 6.50 | 0.69× |
| Linux x86_64 | generic | 9.91 | 8.29 | 1.20× |
| Windows AMD64 | avx2 | 5.28 | 9.01 | 0.59× |
| Windows AMD64 | generic | 12.68 | 17.21 | 0.74× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 217.95 | 194.45 | 1.12× |
| Darwin x86_64 | avx2 | 67.26 | 72.59 | 0.93× |
| Darwin x86_64 | generic | 181.47 | 237.03 | 0.77× |
| Darwin arm64 | generic | 130.41 | 122.21 | 1.07× |
| Linux x86_64 | avx2 | 58.71 | 57.96 | 1.01× |
| Linux x86_64 | generic | 240.97 | 204.89 | 1.18× |
| Windows AMD64 | avx2 | 93.58 | 90.53 | 1.03× |
| Windows AMD64 | generic | 241.25 | 194.87 | 1.24× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.59 | 5.86 | 0.95× |
| Darwin x86_64 | avx2 | 2.17 | 2.51 | 0.86× |
| Darwin x86_64 | generic | 6.29 | 8.64 | 0.73× |
| Darwin arm64 | generic | 4.31 | 4.15 | 1.04× |
| Linux x86_64 | avx2 | 2.01 | 2.08 | 0.97× |
| Linux x86_64 | generic | 6.23 | 6.41 | 0.97× |
| Windows AMD64 | avx2 | 2.94 | 3.05 | 0.97× |
| Windows AMD64 | generic | 6.04 | 6.13 | 0.99× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 138.55 | 75.98 | 1.82× |
| Darwin x86_64 | avx2 | 65.58 | 51.48 | 1.27× |
| Darwin x86_64 | generic | 118.74 | 100.26 | 1.18× |
| Darwin arm64 | generic | 109.50 | 74.95 | 1.46× |
| Linux x86_64 | avx2 | 33.88 | 25.29 | 1.34× |
| Linux x86_64 | generic | 152.96 | 92.18 | 1.66× |
| Windows AMD64 | avx2 | 44.01 | 37.80 | 1.16× |
| Windows AMD64 | generic | 156.31 | 138.86 | 1.13× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.34 | 33.75 | 1.49× |
| Darwin x86_64 | avx2 | 30.70 | 32.72 | 0.94× |
| Darwin x86_64 | generic | 65.67 | 58.04 | 1.13× |
| Darwin arm64 | generic | 48.58 | 34.17 | 1.42× |
| Linux x86_64 | avx2 | 14.84 | 12.25 | 1.21× |
| Linux x86_64 | generic | 57.12 | 42.04 | 1.36× |
| Windows AMD64 | avx2 | 22.12 | 17.05 | 1.30× |
| Windows AMD64 | generic | 57.27 | 41.13 | 1.39× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.64 | 40.71 | 1.00× |
| Darwin x86_64 | avx2 | 16.74 | 21.48 | 0.78× |
| Darwin x86_64 | generic | 38.38 | 51.06 | 0.75× |
| Darwin arm64 | generic | 35.65 | 34.71 | 1.03× |
| Linux x86_64 | avx2 | 11.57 | 11.97 | 0.97× |
| Linux x86_64 | generic | 57.59 | 55.07 | 1.05× |
| Windows AMD64 | avx2 | 14.99 | 15.32 | 0.98× |
| Windows AMD64 | generic | 64.66 | 67.35 | 0.96× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 207.99 | 177.56 | 1.17× |
| Darwin x86_64 | avx2 | 167.58 | 127.92 | 1.31× |
| Darwin x86_64 | generic | 545.52 | 575.50 | 0.95× |
| Darwin arm64 | generic | 259.75 | 161.88 | 1.60× |
| Linux x86_64 | avx2 | 133.28 | 112.88 | 1.18× |
| Linux x86_64 | generic | 220.73 | 251.60 | 0.88× |
| Windows AMD64 | avx2 | 134.05 | 233.58 | 0.57× |
| Windows AMD64 | generic | 274.88 | 357.74 | 0.77× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 207.50 | 210.05 | 0.99× |
| Darwin x86_64 | avx2 | 199.29 | 166.64 | 1.20× |
| Darwin x86_64 | generic | 228.48 | 300.20 | 0.76× |
| Darwin arm64 | generic | 180.88 | 172.14 | 1.05× |
| Linux x86_64 | avx2 | 76.88 | 72.77 | 1.06× |
| Linux x86_64 | generic | 225.57 | 221.33 | 1.02× |
| Windows AMD64 | avx2 | 114.66 | 153.92 | 0.74× |
| Windows AMD64 | generic | 230.99 | 232.33 | 0.99× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 97.72 | 73.35 | 1.33× |
| Darwin x86_64 | avx2 | 45.11 | 39.12 | 1.15× |
| Darwin x86_64 | generic | 156.37 | 129.50 | 1.21× |
| Darwin arm64 | generic | 86.57 | 92.13 | 0.94× |
| Linux x86_64 | avx2 | 25.91 | 26.05 | 0.99× |
| Linux x86_64 | generic | 109.48 | 82.26 | 1.33× |
| Windows AMD64 | avx2 | 38.14 | 37.84 | 1.01× |
| Windows AMD64 | generic | 106.73 | 78.24 | 1.36× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.75 | 13.36 | 1.78× |
| Darwin x86_64 | avx2 | 11.88 | 9.60 | 1.24× |
| Darwin x86_64 | generic | 40.52 | 22.98 | 1.76× |
| Darwin arm64 | generic | 19.43 | 9.65 | 2.01× |
| Linux x86_64 | avx2 | 8.36 | 6.82 | 1.23× |
| Linux x86_64 | generic | 26.68 | 17.70 | 1.51× |
| Windows AMD64 | avx2 | 8.74 | 6.66 | 1.31× |
| Windows AMD64 | generic | 26.37 | 17.07 | 1.54× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 33.30 | 31.82 | 1.05× |
| Darwin x86_64 | avx2 | 17.46 | 16.54 | 1.06× |
| Darwin x86_64 | generic | 66.65 | 58.42 | 1.14× |
| Darwin arm64 | generic | 29.93 | 25.38 | 1.18× |
| Linux x86_64 | avx2 | 20.79 | 20.34 | 1.02× |
| Linux x86_64 | generic | 36.16 | 38.77 | 0.93× |
| Windows AMD64 | avx2 | 16.43 | 16.90 | 0.97× |
| Windows AMD64 | generic | 34.37 | 45.00 | 0.76× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 31.36 | 17.22 | 1.82× |
| Darwin x86_64 | avx2 | 23.64 | 10.57 | 2.24× |
| Darwin x86_64 | generic | 122.10 | 24.18 | 5.05× |
| Darwin arm64 | generic | 39.69 | 15.22 | 2.61× |
| Linux x86_64 | avx2 | 20.38 | 7.78 | 2.62× |
| Linux x86_64 | generic | 33.59 | 24.93 | 1.35× |
| Windows AMD64 | avx2 | 14.48 | 29.50 | 0.49× |
| Windows AMD64 | generic | 36.41 | 21.05 | 1.73× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.98 | 5.93 | 1.01× |
| Darwin x86_64 | avx2 | 5.03 | 4.75 | 1.06× |
| Darwin x86_64 | generic | 7.37 | 11.06 | 0.67× |
| Darwin arm64 | generic | 7.60 | 7.09 | 1.07× |
| Linux x86_64 | avx2 | 2.10 | 2.03 | 1.03× |
| Linux x86_64 | generic | 6.85 | 6.80 | 1.01× |
| Windows AMD64 | avx2 | 2.33 | 2.49 | 0.93× |
| Windows AMD64 | generic | 8.00 | 6.85 | 1.17× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 58.99 | 22.59 | 2.61× |
| Darwin x86_64 | avx2 | 58.08 | 18.29 | 3.18× |
| Darwin x86_64 | generic | 62.89 | 42.03 | 1.50× |
| Darwin arm64 | generic | 88.14 | 24.06 | 3.66× |
| Linux x86_64 | avx2 | 33.31 | 15.10 | 2.21× |
| Linux x86_64 | generic | 63.38 | 32.38 | 1.96× |
| Windows AMD64 | avx2 | 25.44 | 12.23 | 2.08× |
| Windows AMD64 | generic | 79.71 | 38.76 | 2.06× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 9.93 | 9.31 | 1.07× |
| Darwin x86_64 | avx2 | 6.34 | 7.88 | 0.80× |
| Darwin x86_64 | generic | 12.14 | 13.21 | 0.92× |
| Darwin arm64 | generic | 9.40 | 8.04 | 1.17× |
| Linux x86_64 | avx2 | 3.16 | 3.07 | 1.03× |
| Linux x86_64 | generic | 10.92 | 10.46 | 1.04× |
| Windows AMD64 | avx2 | 3.72 | 3.65 | 1.02× |
| Windows AMD64 | generic | 11.02 | 12.26 | 0.90× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 87.24 | 46.53 | 1.88× |
| Darwin x86_64 | avx2 | 47.74 | 45.70 | 1.04× |
| Darwin x86_64 | generic | 90.05 | 93.14 | 0.97× |
| Darwin arm64 | generic | 66.30 | 43.61 | 1.52× |
| Linux x86_64 | avx2 | 33.16 | 29.92 | 1.11× |
| Linux x86_64 | generic | 103.95 | 71.55 | 1.45× |
| Windows AMD64 | avx2 | 37.28 | 26.43 | 1.41× |
| Windows AMD64 | generic | 97.90 | 61.02 | 1.60× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.83 | 48.74 | 0.98× |
| Darwin x86_64 | avx2 | 25.50 | 68.92 | 0.37× |
| Darwin x86_64 | generic | 65.19 | 87.83 | 0.74× |
| Darwin arm64 | generic | 42.00 | 44.55 | 0.94× |
| Linux x86_64 | avx2 | 18.93 | 28.48 | 0.66× |
| Linux x86_64 | generic | 54.49 | 68.64 | 0.79× |
| Windows AMD64 | avx2 | 25.27 | 36.63 | 0.69× |
| Windows AMD64 | generic | 47.44 | 72.03 | 0.66× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.19 | 33.34 | 1.12× |
| Darwin x86_64 | avx2 | 8.13 | 10.61 | 0.77× |
| Darwin x86_64 | generic | 862.26 | 856.57 | 1.01× |
| Darwin arm64 | generic | 15.06 | 149.69 | 0.10× |
| Linux x86_64 | avx2 | 9.54 | 8.20 | 1.16× |
| Linux x86_64 | generic | 36.29 | 33.13 | 1.10× |
| Windows AMD64 | avx2 | 22.98 | 8.67 | 2.65× |
| Windows AMD64 | generic | 89.07 | 27.99 | 3.18× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 137.15 | 56.51 | 2.43× |
| Darwin x86_64 | avx2 | 50.96 | 29.60 | 1.72× |
| Darwin x86_64 | generic | 200.74 | 108.99 | 1.84× |
| Darwin arm64 | generic | 123.21 | 56.51 | 2.18× |
| Linux x86_64 | avx2 | 46.41 | 20.86 | 2.23× |
| Linux x86_64 | generic | 165.84 | 78.94 | 2.10× |
| Windows AMD64 | avx2 | 58.72 | 23.53 | 2.50× |
| Windows AMD64 | generic | 154.38 | 68.22 | 2.26× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 4.35 | 4.55 | 0.96× |
| Darwin x86_64 | avx2 | 1.70 | 1.60 | 1.06× |
| Darwin x86_64 | generic | 8.75 | 10.16 | 0.86× |
| Darwin arm64 | generic | 2.16 | 2.04 | 1.06× |
| Linux x86_64 | avx2 | 0.74 | 0.70 | 1.06× |
| Linux x86_64 | generic | 5.08 | 5.32 | 0.95× |
| Windows AMD64 | avx2 | 2.17 | 2.32 | 0.94× |
| Windows AMD64 | generic | 3.77 | 4.03 | 0.94× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 99.00 | 98.57 | 1.00× |
| Darwin x86_64 | avx2 | 33.49 | 35.18 | 0.95× |
| Darwin x86_64 | generic | 150.24 | 151.87 | 0.99× |
| Darwin arm64 | generic | 88.71 | 82.42 | 1.08× |
| Linux x86_64 | avx2 | 18.13 | 18.26 | 0.99× |
| Linux x86_64 | generic | 112.92 | 117.05 | 0.96× |
| Windows AMD64 | avx2 | 26.78 | 27.19 | 0.99× |
| Windows AMD64 | generic | 88.12 | 88.36 | 1.00× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 42.67 | 43.53 | 0.98× |
| Darwin x86_64 | avx2 | 22.82 | 25.40 | 0.90× |
| Darwin x86_64 | generic | 59.38 | 67.76 | 0.88× |
| Darwin arm64 | generic | 41.23 | 33.60 | 1.23× |
| Linux x86_64 | avx2 | 13.50 | 13.69 | 0.99× |
| Linux x86_64 | generic | 38.88 | 38.91 | 1.00× |
| Windows AMD64 | avx2 | 12.45 | 12.68 | 0.98× |
| Windows AMD64 | generic | 45.39 | 45.77 | 0.99× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 187.15 | 48.03 | 3.90× |
| Darwin x86_64 | avx2 | 29.14 | 19.32 | 1.51× |
| Darwin x86_64 | generic | 63.96 | 134.83 | 0.47× |
| Darwin arm64 | generic | 62.40 | 18.90 | 3.30× |
| Linux x86_64 | avx2 | 10.71 | 17.38 | 0.62× |
| Linux x86_64 | generic | 202.79 | 19.27 | 10.52× |
| Windows AMD64 | avx2 | 45.54 | 18.77 | 2.43× |
| Windows AMD64 | generic | 213.78 | 61.31 | 3.49× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 46.89 | 154.19 | 0.30× |
| Darwin x86_64 | avx2 | 32.41 | 221.62 | 0.15× |
| Darwin x86_64 | generic | 80.27 | 282.64 | 0.28× |
| Darwin arm64 | generic | 47.86 | 85.44 | 0.56× |
| Linux x86_64 | avx2 | 19.75 | 99.89 | 0.20× |
| Linux x86_64 | generic | 77.04 | 167.68 | 0.46× |
| Windows AMD64 | avx2 | 20.02 | 84.34 | 0.24× |
| Windows AMD64 | generic | 54.45 | 142.71 | 0.38× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.65 | 31.98 | 0.96× |
| Darwin x86_64 | avx2 | 13.31 | 11.87 | 1.12× |
| Darwin x86_64 | generic | 59.99 | 55.76 | 1.08× |
| Darwin arm64 | generic | 52.58 | 42.01 | 1.25× |
| Linux x86_64 | avx2 | 7.58 | 7.32 | 1.04× |
| Linux x86_64 | generic | 40.02 | 39.49 | 1.01× |
| Windows AMD64 | avx2 | 12.56 | 11.77 | 1.07× |
| Windows AMD64 | generic | 29.23 | 29.66 | 0.99× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 159.11 | 77.43 | 2.05× |
| Darwin x86_64 | avx2 | 57.60 | 33.29 | 1.73× |
| Darwin x86_64 | generic | 228.35 | 160.59 | 1.42× |
| Darwin arm64 | generic | 99.33 | 74.54 | 1.33× |
| Linux x86_64 | avx2 | 62.07 | 33.98 | 1.83× |
| Linux x86_64 | generic | 137.76 | 115.50 | 1.19× |
| Windows AMD64 | avx2 | 67.26 | 44.11 | 1.52× |
| Windows AMD64 | generic | 146.09 | 118.31 | 1.23× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 78.59 | 35.74 | 2.20× |
| Darwin x86_64 | avx2 | 87.93 | 24.65 | 3.57× |
| Darwin x86_64 | generic | 37.98 | 39.56 | 0.96× |
| Darwin arm64 | generic | 134.69 | 35.04 | 3.84× |
| Linux x86_64 | avx2 | 24.56 | 14.63 | 1.68× |
| Linux x86_64 | generic | 80.37 | 51.94 | 1.55× |
| Windows AMD64 | avx2 | 32.58 | 12.50 | 2.61× |
| Windows AMD64 | generic | 128.70 | 77.75 | 1.66× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 82.48 | 84.95 | 0.97× |
| Darwin x86_64 | avx2 | 61.91 | 51.51 | 1.20× |
| Darwin x86_64 | generic | 158.22 | 168.24 | 0.94× |
| Darwin arm64 | generic | 83.31 | 85.20 | 0.98× |
| Linux x86_64 | avx2 | 31.99 | 32.24 | 0.99× |
| Linux x86_64 | generic | 83.51 | 83.50 | 1.00× |
| Windows AMD64 | avx2 | 51.68 | 51.40 | 1.01× |
| Windows AMD64 | generic | 92.08 | 91.33 | 1.01× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 187.40 | 186.91 | 1.00× |
| Darwin x86_64 | avx2 | 160.88 | 129.20 | 1.25× |
| Darwin x86_64 | generic | 199.21 | 220.65 | 0.90× |
| Darwin arm64 | generic | 263.41 | 253.99 | 1.04× |
| Linux x86_64 | avx2 | 45.87 | 46.07 | 1.00× |
| Linux x86_64 | generic | 198.66 | 197.17 | 1.01× |
| Windows AMD64 | avx2 | 63.66 | 59.07 | 1.08× |
| Windows AMD64 | generic | 134.09 | 134.78 | 0.99× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 225.86 | 130.22 | 1.73× |
| Darwin x86_64 | avx2 | 131.74 | 34.62 | 3.81× |
| Darwin x86_64 | generic | 159.99 | 121.32 | 1.32× |
| Darwin arm64 | generic | 244.76 | 91.34 | 2.68× |
| Linux x86_64 | avx2 | 34.69 | 35.07 | 0.99× |
| Linux x86_64 | generic | 206.96 | 131.85 | 1.57× |
| Windows AMD64 | avx2 | 67.93 | 51.06 | 1.33× |
| Windows AMD64 | generic | 255.88 | 217.79 | 1.17× |


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


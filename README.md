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

The AVX2/Haswell build is **~3.2×** faster than the generic build on average (geometric mean across 24 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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
| Linux aarch64 | 44.94 | — | — |
| Darwin x86_64 | 59.82 | 20.86 | 2.87× |
| Darwin arm64 | 36.79 | — | — |
| Linux x86_64 | 50.17 | 14.30 | 3.51× |
| Windows AMD64 | 52.59 | 16.05 | 3.28× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 35.49 | — | — |
| Darwin x86_64 | 55.32 | 18.88 | 2.93× |
| Darwin arm64 | 31.75 | — | — |
| Linux x86_64 | 38.74 | 13.56 | 2.86× |
| Windows AMD64 | 41.58 | 14.98 | 2.78× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 9.00 | 5.70 | 1.58× |
| Darwin x86_64 | avx2 | 5.69 | 13.46 | 0.42× |
| Darwin x86_64 | generic | 10.16 | 7.04 | 1.44× |
| Darwin arm64 | generic | 8.84 | 15.72 | 0.56× |
| Linux x86_64 | avx2 | 4.46 | 6.07 | 0.74× |
| Linux x86_64 | generic | 9.85 | 8.41 | 1.17× |
| Windows AMD64 | avx2 | 4.86 | 10.60 | 0.46× |
| Windows AMD64 | generic | 12.47 | 21.37 | 0.58× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 219.71 | 199.49 | 1.10× |
| Darwin x86_64 | avx2 | 56.36 | 52.44 | 1.07× |
| Darwin x86_64 | generic | 173.37 | 172.05 | 1.01× |
| Darwin arm64 | generic | 131.67 | 127.11 | 1.04× |
| Linux x86_64 | avx2 | 55.85 | 52.06 | 1.07× |
| Linux x86_64 | generic | 242.77 | 210.73 | 1.15× |
| Windows AMD64 | avx2 | 56.88 | 54.22 | 1.05× |
| Windows AMD64 | generic | 261.06 | 210.50 | 1.24× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.53 | 5.78 | 0.96× |
| Darwin x86_64 | avx2 | 1.83 | 1.78 | 1.03× |
| Darwin x86_64 | generic | 6.08 | 8.86 | 0.69× |
| Darwin arm64 | generic | 3.96 | 4.24 | 0.93× |
| Linux x86_64 | avx2 | 2.01 | 2.08 | 0.96× |
| Linux x86_64 | generic | 6.19 | 6.33 | 0.98× |
| Windows AMD64 | avx2 | 2.28 | 2.36 | 0.96× |
| Windows AMD64 | generic | 5.94 | 6.13 | 0.97× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 139.43 | 76.79 | 1.82× |
| Darwin x86_64 | avx2 | 57.44 | 40.55 | 1.42× |
| Darwin x86_64 | generic | 115.62 | 103.89 | 1.11× |
| Darwin arm64 | generic | 122.80 | 86.51 | 1.42× |
| Linux x86_64 | avx2 | 34.16 | 25.47 | 1.34× |
| Linux x86_64 | generic | 153.17 | 86.21 | 1.78× |
| Windows AMD64 | avx2 | 32.44 | 27.49 | 1.18× |
| Windows AMD64 | generic | 155.46 | 102.89 | 1.51× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 51.07 | 36.76 | 1.39× |
| Darwin x86_64 | avx2 | 27.53 | 19.73 | 1.40× |
| Darwin x86_64 | generic | 57.31 | 69.33 | 0.83× |
| Darwin arm64 | generic | 59.67 | 37.58 | 1.59× |
| Linux x86_64 | avx2 | 15.08 | 12.81 | 1.18× |
| Linux x86_64 | generic | 57.61 | 47.76 | 1.21× |
| Windows AMD64 | avx2 | 17.31 | 13.03 | 1.33× |
| Windows AMD64 | generic | 57.53 | 45.52 | 1.26× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 39.74 | 41.00 | 0.97× |
| Darwin x86_64 | avx2 | 15.10 | 14.75 | 1.02× |
| Darwin x86_64 | generic | 36.14 | 53.14 | 0.68× |
| Darwin arm64 | generic | 38.11 | 35.54 | 1.07× |
| Linux x86_64 | avx2 | 11.43 | 11.98 | 0.95× |
| Linux x86_64 | generic | 57.51 | 54.92 | 1.05× |
| Windows AMD64 | avx2 | 15.09 | 15.72 | 0.96× |
| Windows AMD64 | generic | 57.21 | 54.25 | 1.05× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 209.83 | 238.20 | 0.88× |
| Darwin x86_64 | avx2 | 171.06 | 93.28 | 1.83× |
| Darwin x86_64 | generic | 609.25 | 491.52 | 1.24× |
| Darwin arm64 | generic | 287.87 | 190.22 | 1.51× |
| Linux x86_64 | avx2 | 131.95 | 122.02 | 1.08× |
| Linux x86_64 | generic | 219.84 | 219.97 | 1.00× |
| Windows AMD64 | avx2 | 116.64 | 142.45 | 0.82× |
| Windows AMD64 | generic | 253.28 | 308.13 | 0.82× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 205.69 | 200.77 | 1.02× |
| Darwin x86_64 | avx2 | 160.92 | 110.56 | 1.46× |
| Darwin x86_64 | generic | 236.95 | 205.91 | 1.15× |
| Darwin arm64 | generic | 210.71 | 158.56 | 1.33× |
| Linux x86_64 | avx2 | 76.47 | 73.28 | 1.04× |
| Linux x86_64 | generic | 217.69 | 217.40 | 1.00× |
| Windows AMD64 | avx2 | 102.57 | 109.71 | 0.93× |
| Windows AMD64 | generic | 229.62 | 227.76 | 1.01× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 98.30 | 72.68 | 1.35× |
| Darwin x86_64 | avx2 | 45.40 | 34.16 | 1.33× |
| Darwin x86_64 | generic | 94.96 | 95.79 | 0.99× |
| Darwin arm64 | generic | 88.64 | 85.83 | 1.03× |
| Linux x86_64 | avx2 | 25.31 | 26.16 | 0.97× |
| Linux x86_64 | generic | 110.04 | 82.31 | 1.34× |
| Windows AMD64 | avx2 | 26.27 | 26.41 | 0.99× |
| Windows AMD64 | generic | 111.73 | 83.86 | 1.33× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.94 | 12.61 | 1.90× |
| Darwin x86_64 | avx2 | 11.47 | 9.56 | 1.20× |
| Darwin x86_64 | generic | 28.80 | 20.74 | 1.39× |
| Darwin arm64 | generic | 20.16 | 8.80 | 2.29× |
| Linux x86_64 | avx2 | 8.26 | 7.56 | 1.09× |
| Linux x86_64 | generic | 26.71 | 19.73 | 1.35× |
| Windows AMD64 | avx2 | 8.53 | 6.44 | 1.32× |
| Windows AMD64 | generic | 26.31 | 16.35 | 1.61× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 33.91 | 32.03 | 1.06× |
| Darwin x86_64 | avx2 | 13.88 | 13.96 | 0.99× |
| Darwin x86_64 | generic | 48.72 | 49.56 | 0.98× |
| Darwin arm64 | generic | 31.68 | 33.81 | 0.94× |
| Linux x86_64 | avx2 | 20.16 | 19.98 | 1.01× |
| Linux x86_64 | generic | 36.62 | 35.78 | 1.02× |
| Windows AMD64 | avx2 | 12.87 | 12.82 | 1.00× |
| Windows AMD64 | generic | 35.67 | 39.13 | 0.91× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 31.73 | 19.41 | 1.63× |
| Darwin x86_64 | avx2 | 26.56 | 9.38 | 2.83× |
| Darwin x86_64 | generic | 127.52 | 21.82 | 5.84× |
| Darwin arm64 | generic | 42.73 | 15.04 | 2.84× |
| Linux x86_64 | avx2 | 20.39 | 6.95 | 2.94× |
| Linux x86_64 | generic | 33.40 | 16.27 | 2.05× |
| Windows AMD64 | avx2 | 13.57 | 10.46 | 1.30× |
| Windows AMD64 | generic | 36.14 | 20.29 | 1.78× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.32 | 5.91 | 1.07× |
| Darwin x86_64 | avx2 | 5.88 | 4.00 | 1.47× |
| Darwin x86_64 | generic | 7.28 | 9.58 | 0.76× |
| Darwin arm64 | generic | 8.54 | 6.02 | 1.42× |
| Linux x86_64 | avx2 | 2.14 | 2.22 | 0.96× |
| Linux x86_64 | generic | 7.03 | 7.02 | 1.00× |
| Windows AMD64 | avx2 | 2.14 | 2.31 | 0.93× |
| Windows AMD64 | generic | 8.37 | 6.97 | 1.20× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 59.74 | 22.67 | 2.63× |
| Darwin x86_64 | avx2 | 61.37 | 15.21 | 4.03× |
| Darwin x86_64 | generic | 64.10 | 30.28 | 2.12× |
| Darwin arm64 | generic | 92.17 | 22.85 | 4.03× |
| Linux x86_64 | avx2 | 33.20 | 11.28 | 2.94× |
| Linux x86_64 | generic | 63.02 | 30.26 | 2.08× |
| Windows AMD64 | avx2 | 23.81 | 11.47 | 2.08× |
| Windows AMD64 | generic | 79.55 | 38.23 | 2.08× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 10.09 | 9.26 | 1.09× |
| Darwin x86_64 | avx2 | 5.51 | 5.73 | 0.96× |
| Darwin x86_64 | generic | 12.84 | 11.39 | 1.13× |
| Darwin arm64 | generic | 9.60 | 7.10 | 1.35× |
| Linux x86_64 | avx2 | 3.14 | 3.14 | 1.00× |
| Linux x86_64 | generic | 10.87 | 10.37 | 1.05× |
| Windows AMD64 | avx2 | 3.34 | 3.27 | 1.02× |
| Windows AMD64 | generic | 10.96 | 11.01 | 1.00× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 87.72 | 44.61 | 1.97× |
| Darwin x86_64 | avx2 | 47.10 | 48.77 | 0.97× |
| Darwin x86_64 | generic | 90.55 | 72.63 | 1.25× |
| Darwin arm64 | generic | 69.99 | 40.60 | 1.72× |
| Linux x86_64 | avx2 | 33.03 | 32.33 | 1.02× |
| Linux x86_64 | generic | 103.39 | 69.51 | 1.49× |
| Windows AMD64 | avx2 | 33.14 | 27.03 | 1.23× |
| Windows AMD64 | generic | 101.95 | 67.38 | 1.51× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.52 | 49.58 | 0.96× |
| Darwin x86_64 | avx2 | 25.47 | 45.27 | 0.56× |
| Darwin x86_64 | generic | 52.86 | 71.84 | 0.74× |
| Darwin arm64 | generic | 43.79 | 34.69 | 1.26× |
| Linux x86_64 | avx2 | 18.80 | 25.12 | 0.75× |
| Linux x86_64 | generic | 53.82 | 62.46 | 0.86× |
| Windows AMD64 | avx2 | 19.38 | 34.81 | 0.56× |
| Windows AMD64 | generic | 52.80 | 59.06 | 0.89× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 36.80 | 45.72 | 0.80× |
| Darwin x86_64 | avx2 | 8.50 | 8.72 | 0.98× |
| Darwin x86_64 | generic | 752.19 | 614.07 | 1.22× |
| Darwin arm64 | generic | 14.54 | 144.76 | 0.10× |
| Linux x86_64 | avx2 | 9.36 | 13.68 | 0.68× |
| Linux x86_64 | generic | 36.11 | 31.41 | 1.15× |
| Windows AMD64 | avx2 | 20.25 | 7.30 | 2.77× |
| Windows AMD64 | generic | 81.68 | 48.19 | 1.69× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.67 | 56.06 | 2.44× |
| Darwin x86_64 | avx2 | 51.30 | 24.01 | 2.14× |
| Darwin x86_64 | generic | 178.60 | 81.20 | 2.20× |
| Darwin arm64 | generic | 115.13 | 64.00 | 1.80× |
| Linux x86_64 | avx2 | 46.38 | 20.79 | 2.23× |
| Linux x86_64 | generic | 164.05 | 68.94 | 2.38× |
| Windows AMD64 | avx2 | 30.64 | 18.80 | 1.63× |
| Windows AMD64 | generic | 164.30 | 70.96 | 2.32× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 4.36 | 4.48 | 0.97× |
| Darwin x86_64 | avx2 | 1.69 | 1.42 | 1.18× |
| Darwin x86_64 | generic | 7.60 | 8.02 | 0.95× |
| Darwin arm64 | generic | 1.98 | 1.91 | 1.04× |
| Linux x86_64 | avx2 | 0.74 | 0.70 | 1.05× |
| Linux x86_64 | generic | 4.92 | 5.22 | 0.94× |
| Windows AMD64 | avx2 | 1.92 | 2.04 | 0.94× |
| Windows AMD64 | generic | 3.90 | 4.19 | 0.93× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 100.71 | 100.69 | 1.00× |
| Darwin x86_64 | avx2 | 31.43 | 25.13 | 1.25× |
| Darwin x86_64 | generic | 131.66 | 122.69 | 1.07× |
| Darwin arm64 | generic | 78.60 | 79.11 | 0.99× |
| Linux x86_64 | avx2 | 17.86 | 18.22 | 0.98× |
| Linux x86_64 | generic | 108.79 | 109.34 | 0.99× |
| Windows AMD64 | avx2 | 24.81 | 24.86 | 1.00× |
| Windows AMD64 | generic | 78.23 | 78.58 | 1.00× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 43.18 | 42.96 | 1.01× |
| Darwin x86_64 | avx2 | 17.87 | 18.19 | 0.98× |
| Darwin x86_64 | generic | 50.19 | 47.33 | 1.06× |
| Darwin arm64 | generic | 31.17 | 32.09 | 0.97× |
| Linux x86_64 | avx2 | 13.33 | 13.79 | 0.97× |
| Linux x86_64 | generic | 38.55 | 38.91 | 0.99× |
| Windows AMD64 | avx2 | 12.26 | 12.34 | 0.99× |
| Windows AMD64 | generic | 39.77 | 40.12 | 0.99× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 190.02 | 39.14 | 4.86× |
| Darwin x86_64 | avx2 | 21.39 | 27.51 | 0.78× |
| Darwin x86_64 | generic | 53.15 | 71.83 | 0.74× |
| Darwin arm64 | generic | 36.01 | 16.43 | 2.19× |
| Linux x86_64 | avx2 | 10.23 | 7.60 | 1.35× |
| Linux x86_64 | generic | 203.26 | 15.16 | 13.41× |
| Windows AMD64 | avx2 | 40.76 | 7.44 | 5.48× |
| Windows AMD64 | generic | 212.50 | 23.60 | 9.00× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.35 | 144.17 | 0.33× |
| Darwin x86_64 | avx2 | 29.62 | 223.97 | 0.13× |
| Darwin x86_64 | generic | 68.25 | 262.26 | 0.26× |
| Darwin arm64 | generic | 29.54 | 95.58 | 0.31× |
| Linux x86_64 | avx2 | 19.52 | 96.86 | 0.20× |
| Linux x86_64 | generic | 75.19 | 163.60 | 0.46× |
| Windows AMD64 | avx2 | 21.09 | 114.81 | 0.18× |
| Windows AMD64 | generic | 67.45 | 106.96 | 0.63× |


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


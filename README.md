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

The AVX2/Haswell build is **~3.1×** faster than the generic build on average (geometric mean across 30 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

<!-- PERF_SPEEDUP_END -->

<!-- PERF_PLOT_START -->

![CBC solve time — generic vs AVX2/Haswell (Linux x86_64)](https://raw.githubusercontent.com/h-g-s/cbcbox/master/docs/perf_avx2_speedup.png)

*Single-threaded solve time across benchmark instances on Linux x86_64, sorted by solve time. Speedup factor shown above each pair. Lower is better.*

See also: [Windows AMD64 + macOS x86_64 summary](https://raw.githubusercontent.com/h-g-s/cbcbox/master/docs/perf_avx2_other.png)

<!-- PERF_PLOT_END -->

## Build variants

On **x86_64 Linux, macOS, and Windows**, the wheel ships three complete sets of binaries:

| Variant | OpenBLAS kernel | Clp SIMD | Flags | Minimum CPU |
|---|---|---|---|---|
| `generic` | `DYNAMIC_ARCH=1` (runtime dispatch, Nehalem–Zen targets) | standard | `-O3` | any x86_64 |
| `avx2` | `DYNAMIC_ARCH=1` + `DYNAMIC_LIST=HASWELL SKYLAKEX` | `-march=haswell -DCOIN_AVX2=4` | `-O3 -march=haswell` | Haswell (2013+) |
| `debug` | same as `avx2` on x86_64, `generic` elsewhere | same as `avx2` on x86_64 | `-O1 -g -fno-omit-frame-pointer` | same as `avx2` |

**Non-x86_64 platforms** (Linux aarch64, macOS arm64) ship `generic` and `debug` only.

At import time `cbcbox` automatically selects `avx2` when available **and** the running CPU supports AVX2; otherwise it falls back to `generic`.

You can override the selection with the `CBCBOX_BUILD` environment variable:

```bash
# Force generic (portable) build
CBCBOX_BUILD=generic cbc mymodel.mps -solve -quit

# Force AVX2-optimised build (raises an error if not available on this platform/CPU)
CBCBOX_BUILD=avx2 cbc mymodel.mps -solve -quit

# Force debug build (full symbols, no optimisation — useful for bug reports and GDB/LLDB)
CBCBOX_BUILD=debug cbc mymodel.mps -solve -quit
```

When `CBCBOX_BUILD` is set, a short summary of the selected build is printed to
stdout on every call — useful for tagging experiment results:

```
[cbcbox] CBCBOX_BUILD=avx2
[cbcbox]   binary  : .../cbcbox/cbc_dist_avx2/bin/cbc
[cbcbox]   lib dir : .../cbcbox/cbc_dist_avx2/lib
[cbcbox]   libs    : libCbc.so.3, libClp.so.3, libopenblas.so.0
```

Set `CBCBOX_VERBOSE=1` to always print this dispatch summary regardless of whether
`CBCBOX_BUILD` is set — useful to confirm which binary is actually being invoked.

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
| Darwin x86_64 | 72.85 | 27.26 | 2.67× |
| Darwin arm64 | 54.69 | — | — |
| Linux x86_64 | 59.52 | 17.09 | 3.48× |
| Windows AMD64 | 61.59 | 19.06 | 3.23× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 40.73 | — | — |
| Darwin x86_64 | 67.40 | 22.71 | 2.97× |
| Darwin arm64 | 39.34 | — | — |
| Linux x86_64 | 47.96 | 15.86 | 3.02× |
| Windows AMD64 | 48.89 | 17.45 | 2.80× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 8.98 | 5.96 | 1.51× |
| Darwin x86_64 | avx2 | 5.33 | 12.95 | 0.41× |
| Darwin x86_64 | generic | 10.03 | 8.60 | 1.17× |
| Darwin arm64 | generic | 9.65 | 15.02 | 0.64× |
| Linux x86_64 | avx2 | 4.61 | 8.24 | 0.56× |
| Linux x86_64 | generic | 9.86 | 8.19 | 1.20× |
| Windows AMD64 | avx2 | 4.89 | 8.37 | 0.58× |
| Windows AMD64 | generic | 13.25 | 21.99 | 0.60× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 219.32 | 201.59 | 1.09× |
| Darwin x86_64 | avx2 | 54.63 | 59.66 | 0.92× |
| Darwin x86_64 | generic | 188.06 | 195.44 | 0.96× |
| Darwin arm64 | generic | 143.47 | 129.41 | 1.11× |
| Linux x86_64 | avx2 | 57.78 | 56.57 | 1.02× |
| Linux x86_64 | generic | 236.53 | 209.44 | 1.13× |
| Windows AMD64 | avx2 | 57.61 | 56.22 | 1.02× |
| Windows AMD64 | generic | 252.26 | 240.40 | 1.05× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.42 | 5.58 | 0.97× |
| Darwin x86_64 | avx2 | 1.82 | 2.09 | 0.87× |
| Darwin x86_64 | generic | 6.76 | 7.21 | 0.94× |
| Darwin arm64 | generic | 5.35 | 4.74 | 1.13× |
| Linux x86_64 | avx2 | 1.97 | 2.08 | 0.95× |
| Linux x86_64 | generic | 6.38 | 6.64 | 0.96× |
| Windows AMD64 | avx2 | 2.33 | 2.38 | 0.98× |
| Windows AMD64 | generic | 6.03 | 6.04 | 1.00× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 138.44 | 76.63 | 1.81× |
| Darwin x86_64 | avx2 | 58.68 | 45.86 | 1.28× |
| Darwin x86_64 | generic | 132.92 | 91.59 | 1.45× |
| Darwin arm64 | generic | 138.82 | 90.52 | 1.53× |
| Linux x86_64 | avx2 | 34.53 | 25.87 | 1.33× |
| Linux x86_64 | generic | 152.11 | 120.46 | 1.26× |
| Windows AMD64 | avx2 | 32.67 | 26.58 | 1.23× |
| Windows AMD64 | generic | 156.55 | 104.76 | 1.49× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.11 | 33.70 | 1.49× |
| Darwin x86_64 | avx2 | 27.44 | 21.02 | 1.31× |
| Darwin x86_64 | generic | 63.93 | 48.87 | 1.31× |
| Darwin arm64 | generic | 61.63 | 42.73 | 1.44× |
| Linux x86_64 | avx2 | 14.67 | 12.58 | 1.17× |
| Linux x86_64 | generic | 56.35 | 43.78 | 1.29× |
| Windows AMD64 | avx2 | 17.47 | 13.15 | 1.33× |
| Windows AMD64 | generic | 58.44 | 41.16 | 1.42× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 39.52 | 40.37 | 0.98× |
| Darwin x86_64 | avx2 | 14.46 | 15.96 | 0.91× |
| Darwin x86_64 | generic | 40.08 | 43.30 | 0.93× |
| Darwin arm64 | generic | 44.72 | 38.11 | 1.17× |
| Linux x86_64 | avx2 | 12.16 | 12.82 | 0.95× |
| Linux x86_64 | generic | 66.09 | 68.48 | 0.97× |
| Windows AMD64 | avx2 | 15.22 | 16.91 | 0.90× |
| Windows AMD64 | generic | 57.66 | 53.00 | 1.09× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 209.51 | 178.79 | 1.17× |
| Darwin x86_64 | avx2 | 142.69 | 107.88 | 1.32× |
| Darwin x86_64 | generic | 563.67 | 402.36 | 1.40× |
| Darwin arm64 | generic | 361.95 | 184.07 | 1.97× |
| Linux x86_64 | avx2 | 132.92 | 110.15 | 1.21× |
| Linux x86_64 | generic | 223.60 | 220.77 | 1.01× |
| Windows AMD64 | avx2 | 118.66 | 273.98 | 0.43× |
| Windows AMD64 | generic | 260.18 | 273.12 | 0.95× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 205.09 | 201.74 | 1.02× |
| Darwin x86_64 | avx2 | 144.69 | 125.00 | 1.16× |
| Darwin x86_64 | generic | 267.36 | 240.76 | 1.11× |
| Darwin arm64 | generic | 260.16 | 187.51 | 1.39× |
| Linux x86_64 | avx2 | 88.02 | 82.22 | 1.07× |
| Linux x86_64 | generic | 233.40 | 231.05 | 1.01× |
| Windows AMD64 | avx2 | 100.34 | 118.72 | 0.85× |
| Windows AMD64 | generic | 241.71 | 230.01 | 1.05× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 97.91 | 72.49 | 1.35× |
| Darwin x86_64 | avx2 | 46.73 | 38.85 | 1.20× |
| Darwin x86_64 | generic | 103.80 | 113.20 | 0.92× |
| Darwin arm64 | generic | 106.90 | 92.77 | 1.15× |
| Linux x86_64 | avx2 | 26.56 | 25.65 | 1.04× |
| Linux x86_64 | generic | 108.79 | 80.85 | 1.35× |
| Windows AMD64 | avx2 | 26.92 | 27.22 | 0.99× |
| Windows AMD64 | generic | 114.48 | 84.13 | 1.36× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.78 | 12.87 | 1.85× |
| Darwin x86_64 | avx2 | 12.84 | 9.34 | 1.38× |
| Darwin x86_64 | generic | 28.99 | 20.40 | 1.42× |
| Darwin arm64 | generic | 23.43 | 10.49 | 2.23× |
| Linux x86_64 | avx2 | 8.21 | 6.22 | 1.32× |
| Linux x86_64 | generic | 26.86 | 17.07 | 1.57× |
| Windows AMD64 | avx2 | 8.69 | 6.48 | 1.34× |
| Windows AMD64 | generic | 26.83 | 16.90 | 1.59× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 33.26 | 31.41 | 1.06× |
| Darwin x86_64 | avx2 | 21.28 | 15.24 | 1.40× |
| Darwin x86_64 | generic | 49.54 | 66.50 | 0.74× |
| Darwin arm64 | generic | 43.54 | 26.10 | 1.67× |
| Linux x86_64 | avx2 | 20.31 | 19.81 | 1.02× |
| Linux x86_64 | generic | 35.79 | 36.05 | 0.99× |
| Windows AMD64 | avx2 | 13.59 | 12.31 | 1.10× |
| Windows AMD64 | generic | 36.04 | 47.35 | 0.76× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 31.34 | 17.91 | 1.75× |
| Darwin x86_64 | avx2 | 25.75 | 8.94 | 2.88× |
| Darwin x86_64 | generic | 133.60 | 28.41 | 4.70× |
| Darwin arm64 | generic | 46.41 | 19.43 | 2.39× |
| Linux x86_64 | avx2 | 20.84 | 10.03 | 2.08× |
| Linux x86_64 | generic | 33.44 | 22.10 | 1.51× |
| Windows AMD64 | avx2 | 13.55 | 6.63 | 2.04× |
| Windows AMD64 | generic | 36.78 | 20.54 | 1.79× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.06 | 6.08 | 1.00× |
| Darwin x86_64 | avx2 | 5.82 | 4.04 | 1.44× |
| Darwin x86_64 | generic | 8.27 | 12.85 | 0.64× |
| Darwin arm64 | generic | 9.18 | 7.26 | 1.26× |
| Linux x86_64 | avx2 | 2.25 | 2.11 | 1.06× |
| Linux x86_64 | generic | 6.90 | 6.93 | 1.00× |
| Windows AMD64 | avx2 | 2.10 | 2.40 | 0.88× |
| Windows AMD64 | generic | 8.49 | 6.61 | 1.28× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 59.36 | 21.51 | 2.76× |
| Darwin x86_64 | avx2 | 62.75 | 16.70 | 3.76× |
| Darwin x86_64 | generic | 74.33 | 46.84 | 1.59× |
| Darwin arm64 | generic | 112.12 | 32.58 | 3.44× |
| Linux x86_64 | avx2 | 33.85 | 18.23 | 1.86× |
| Linux x86_64 | generic | 62.05 | 31.25 | 1.99× |
| Windows AMD64 | avx2 | 23.96 | 11.90 | 2.01× |
| Windows AMD64 | generic | 82.61 | 39.47 | 2.09× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 10.13 | 9.02 | 1.12× |
| Darwin x86_64 | avx2 | 6.87 | 5.49 | 1.25× |
| Darwin x86_64 | generic | 14.82 | 15.97 | 0.93× |
| Darwin arm64 | generic | 12.97 | 11.25 | 1.15× |
| Linux x86_64 | avx2 | 3.28 | 3.25 | 1.01× |
| Linux x86_64 | generic | 11.08 | 10.41 | 1.06× |
| Windows AMD64 | avx2 | 3.34 | 3.32 | 1.01× |
| Windows AMD64 | generic | 11.07 | 12.77 | 0.87× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 88.00 | 47.13 | 1.87× |
| Darwin x86_64 | avx2 | 48.28 | 44.10 | 1.09× |
| Darwin x86_64 | generic | 104.16 | 116.29 | 0.90× |
| Darwin arm64 | generic | 93.35 | 67.55 | 1.38× |
| Linux x86_64 | avx2 | 34.55 | 23.52 | 1.47× |
| Linux x86_64 | generic | 100.80 | 60.28 | 1.67× |
| Windows AMD64 | avx2 | 33.12 | 27.94 | 1.19× |
| Windows AMD64 | generic | 104.58 | 65.38 | 1.60× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.85 | 53.99 | 0.89× |
| Darwin x86_64 | avx2 | 30.32 | 48.81 | 0.62× |
| Darwin x86_64 | generic | 61.46 | 73.93 | 0.83× |
| Darwin arm64 | generic | 52.13 | 53.72 | 0.97× |
| Linux x86_64 | avx2 | 19.86 | 29.39 | 0.68× |
| Linux x86_64 | generic | 49.87 | 59.39 | 0.84× |
| Windows AMD64 | avx2 | 19.20 | 32.07 | 0.60× |
| Windows AMD64 | generic | 66.20 | 80.92 | 0.82× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 36.75 | 53.00 | 0.69× |
| Darwin x86_64 | avx2 | 9.23 | 9.62 | 0.96× |
| Darwin x86_64 | generic | 913.11 | 715.69 | 1.28× |
| Darwin arm64 | generic | 16.55 | 17.46 | 0.95× |
| Linux x86_64 | avx2 | 9.76 | 9.24 | 1.06× |
| Linux x86_64 | generic | 38.59 | 39.10 | 0.99× |
| Windows AMD64 | avx2 | 20.15 | 17.63 | 1.14× |
| Windows AMD64 | generic | 83.34 | 23.11 | 3.61× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 137.01 | 54.49 | 2.51× |
| Darwin x86_64 | avx2 | 55.30 | 23.23 | 2.38× |
| Darwin x86_64 | generic | 192.80 | 90.79 | 2.12× |
| Darwin arm64 | generic | 144.08 | 69.00 | 2.09× |
| Linux x86_64 | avx2 | 48.54 | 21.04 | 2.31× |
| Linux x86_64 | generic | 160.14 | 73.65 | 2.17× |
| Windows AMD64 | avx2 | 30.29 | 17.76 | 1.71× |
| Windows AMD64 | generic | 167.62 | 69.47 | 2.41× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 4.35 | 4.49 | 0.97× |
| Darwin x86_64 | avx2 | 1.72 | 1.41 | 1.22× |
| Darwin x86_64 | generic | 8.12 | 9.33 | 0.87× |
| Darwin arm64 | generic | 2.10 | 2.58 | 0.81× |
| Linux x86_64 | avx2 | 0.75 | 0.77 | 0.97× |
| Linux x86_64 | generic | 4.96 | 5.21 | 0.95× |
| Windows AMD64 | avx2 | 1.88 | 2.04 | 0.92× |
| Windows AMD64 | generic | 3.85 | 4.15 | 0.93× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 98.08 | 98.28 | 1.00× |
| Darwin x86_64 | avx2 | 34.69 | 27.83 | 1.25× |
| Darwin x86_64 | generic | 159.00 | 141.37 | 1.12× |
| Darwin arm64 | generic | 94.24 | 93.86 | 1.00× |
| Linux x86_64 | avx2 | 20.57 | 20.74 | 0.99× |
| Linux x86_64 | generic | 126.02 | 126.24 | 1.00× |
| Windows AMD64 | avx2 | 24.61 | 25.05 | 0.98× |
| Windows AMD64 | generic | 72.21 | 72.44 | 1.00× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 43.17 | 43.60 | 0.99× |
| Darwin x86_64 | avx2 | 23.75 | 20.35 | 1.17× |
| Darwin x86_64 | generic | 66.44 | 55.40 | 1.20× |
| Darwin arm64 | generic | 45.20 | 37.10 | 1.22× |
| Linux x86_64 | avx2 | 14.20 | 14.48 | 0.98× |
| Linux x86_64 | generic | 45.12 | 45.75 | 0.99× |
| Windows AMD64 | avx2 | 12.19 | 12.52 | 0.97× |
| Windows AMD64 | generic | 39.43 | 39.47 | 1.00× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 188.23 | 45.90 | 4.10× |
| Darwin x86_64 | avx2 | 31.78 | 18.57 | 1.71× |
| Darwin x86_64 | generic | 70.04 | 77.35 | 0.91× |
| Darwin arm64 | generic | 57.66 | 22.28 | 2.59× |
| Linux x86_64 | avx2 | 11.51 | 14.95 | 0.77× |
| Linux x86_64 | generic | 208.45 | 19.64 | 10.61× |
| Windows AMD64 | avx2 | 40.11 | 6.92 | 5.80× |
| Windows AMD64 | generic | 211.01 | 70.89 | 2.98× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.92 | 124.34 | 0.39× |
| Darwin x86_64 | avx2 | 35.31 | 269.92 | 0.13× |
| Darwin x86_64 | generic | 81.41 | 241.70 | 0.34× |
| Darwin arm64 | generic | 38.44 | 108.59 | 0.35× |
| Linux x86_64 | avx2 | 18.16 | 77.15 | 0.24× |
| Linux x86_64 | generic | 62.52 | 92.61 | 0.68× |
| Windows AMD64 | avx2 | 21.04 | 115.80 | 0.18× |
| Windows AMD64 | generic | 67.43 | 160.21 | 0.42× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.65 | 30.64 | 1.00× |
| Darwin x86_64 | avx2 | 14.35 | 12.26 | 1.17× |
| Darwin x86_64 | generic | 54.20 | 53.17 | 1.02× |
| Darwin arm64 | generic | 42.20 | 39.06 | 1.08× |
| Linux x86_64 | avx2 | 7.96 | 7.62 | 1.04× |
| Linux x86_64 | generic | 38.45 | 39.07 | 0.98× |
| Windows AMD64 | avx2 | 11.03 | 11.00 | 1.00× |
| Windows AMD64 | generic | 30.10 | 30.68 | 0.98× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 159.53 | 77.06 | 2.07× |
| Darwin x86_64 | avx2 | 57.51 | 33.88 | 1.70× |
| Darwin x86_64 | generic | 199.56 | 134.52 | 1.48× |
| Darwin arm64 | generic | 110.79 | 62.98 | 1.76× |
| Linux x86_64 | avx2 | 61.61 | 33.53 | 1.84× |
| Linux x86_64 | generic | 144.11 | 120.46 | 1.20× |
| Windows AMD64 | avx2 | 62.81 | 34.48 | 1.82× |
| Windows AMD64 | generic | 151.13 | 117.36 | 1.29× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 79.34 | 34.76 | 2.28× |
| Darwin x86_64 | avx2 | 82.60 | 29.06 | 2.84× |
| Darwin x86_64 | generic | 33.56 | 43.60 | 0.77× |
| Darwin arm64 | generic | 139.90 | 28.23 | 4.96× |
| Linux x86_64 | avx2 | 26.30 | 13.83 | 1.90× |
| Linux x86_64 | generic | 85.88 | 59.63 | 1.44× |
| Windows AMD64 | avx2 | 27.41 | 10.67 | 2.57× |
| Windows AMD64 | generic | 122.79 | 34.24 | 3.59× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 81.77 | 83.47 | 0.98× |
| Darwin x86_64 | avx2 | 47.12 | 51.37 | 0.92× |
| Darwin x86_64 | generic | 126.55 | 147.75 | 0.86× |
| Darwin arm64 | generic | 81.17 | 70.84 | 1.15× |
| Linux x86_64 | avx2 | 33.94 | 33.62 | 1.01× |
| Linux x86_64 | generic | 88.93 | 91.72 | 0.97× |
| Windows AMD64 | avx2 | 47.12 | 47.68 | 0.99× |
| Windows AMD64 | generic | 89.07 | 88.35 | 1.01× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 186.91 | 186.79 | 1.00× |
| Darwin x86_64 | avx2 | 125.58 | 135.01 | 0.93× |
| Darwin x86_64 | generic | 171.29 | 188.90 | 0.91× |
| Darwin arm64 | generic | 254.53 | 239.76 | 1.06× |
| Linux x86_64 | avx2 | 46.40 | 47.05 | 0.99× |
| Linux x86_64 | generic | 202.40 | 201.08 | 1.01× |
| Windows AMD64 | avx2 | 53.66 | 49.80 | 1.08× |
| Windows AMD64 | generic | 137.34 | 135.46 | 1.01× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 226.88 | 123.18 | 1.84× |
| Darwin x86_64 | avx2 | 115.72 | 49.06 | 2.36× |
| Darwin x86_64 | generic | 144.60 | 114.17 | 1.27× |
| Darwin arm64 | generic | 244.53 | 101.41 | 2.41× |
| Linux x86_64 | avx2 | 36.95 | 34.92 | 1.06× |
| Linux x86_64 | generic | 243.64 | 175.76 | 1.39× |
| Windows AMD64 | avx2 | 58.29 | 44.36 | 1.31× |
| Windows AMD64 | generic | 222.62 | 133.15 | 1.67× |


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

The released wheels include an optimised build and a **debug build** (see
[Build variants](#build-variants)).  For most debugging needs, `CBCBOX_BUILD=debug`
is all you need.  If you want to rebuild with a sanitizer or need exact parity
with the CI container, use the scripts in `scripts/`.

| Script | Platform | Environment | Output directory |
|---|---|---|---|
| `scripts/build_debug.sh` | Linux, macOS | native (host compiler) | `cbc_dist_debug_avx2/` (x86_64) or `cbc_dist_debug/` (ARM64) |
| `scripts/build_debug_manylinux.sh` | Linux | Docker — manylinux_2_28 container (exact CI parity) | same as above |
| `scripts/build_debug_windows.ps1` | Windows | MSYS2 / MinGW64 | `cbc_dist_debug_avx2\` |

### Quick start

**Linux / macOS (native build):**

```bash
# x86_64 → debug + AVX2 → cbc_dist_debug_avx2/bin/cbc
# ARM64  → debug only  → cbc_dist_debug/bin/cbc
./scripts/build_debug.sh

# With AddressSanitizer (Linux/macOS only):
./scripts/build_debug.sh --asan

# With ThreadSanitizer:
./scripts/build_debug.sh --tsan

# Force a clean rebuild from scratch (required when switching sanitizers):
./scripts/build_debug.sh --asan --clean
```

**Linux (manylinux_2_28 container — matches CI exactly):**

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

> **Note:** The debug build shipped in the wheel does **not** include a sanitizer.
> Use the local build scripts above (`--asan` / `--tsan`) on your development
> machine to enable sanitizer instrumentation.

| Sanitizer | Flag | What it catches | Runtime env var |
|---|---|---|---|
| AddressSanitizer | `--asan` | heap/stack buffer overflows, use-after-free, memory leaks | `ASAN_OPTIONS=detect_leaks=0` to suppress system-lib false positives |
| ThreadSanitizer  | `--tsan` | data races between threads | `TSAN_OPTIONS=halt_on_error=0` to log races without aborting |

ASan and TSan are mutually exclusive.  Neither is available on Windows/MinGW.
Always pass `--clean` when switching from one sanitizer to another to avoid
linking mismatched object files.

OpenBLAS is always built **without** sanitizer flags to avoid false positives
from hand-optimised BLAS assembly; only the COIN-OR stack is instrumented.

## License

CBC and all COIN-OR components are distributed under the
[Eclipse Public License 2.0](https://opensource.org/licenses/EPL-2.0).
OpenBLAS is distributed under the BSD 3-Clause licence.
SuiteSparse AMD is distributed under the BSD 3-Clause licence.
Nauty is distributed under the Apache 2.0 licence.


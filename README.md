# cbcbox

[![PyPI version](https://img.shields.io/pypi/v/cbcbox.svg?color=brightgreen)](https://pypi.org/project/cbcbox/)
[![PyPI downloads](https://img.shields.io/pypi/dm/cbcbox.svg?color=blue)](https://pypi.org/project/cbcbox/)
[![CI](https://github.com/h-g-s/cbcbox/actions/workflows/wheel.yml/badge.svg)](https://github.com/h-g-s/cbcbox/actions/workflows/wheel.yml)
[![Platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20macOS%20%7C%20Windows-informational)](https://pypi.org/project/cbcbox/)
[![License](https://img.shields.io/badge/license-EPL--2.0-blue.svg)](https://opensource.org/licenses/EPL-2.0)

**cbcbox** is a high-performance, self-contained Python distribution of the
[CBC](https://github.com/coin-or/Cbc) MILP solver (COIN-OR Branch and Cut),
built from the latest COIN-OR `next` branch.

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

The AVX2/Haswell build is **~2.7×** faster than the generic build on average (geometric mean across 30 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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
| **Cbc** | next | Branch-and-cut MIP solver |
| **Cgl** | next | Cut generation library |
| **Clp** | next | Simplex LP solver (used as the MIP node relaxation) |
| **Osi** | next | Open Solver Interface |
| **CoinUtils** | next | Utility library (shared by all COIN-OR packages) |
| **[AMD](https://github.com/DrTimothyAldenDavis/SuiteSparse)** (SuiteSparse v7.12.2) | v7.12.2 | Sparse matrix fill-reducing ordering |
| **[OpenBLAS](https://github.com/OpenMathLib/OpenBLAS)** | v0.3.31 | Optimised BLAS/LAPACK for LP basis factorisation |

On x86_64 Linux, macOS, and Windows the entire stack is compiled **twice**: once for the
`generic` variant (OpenBLAS `DYNAMIC_ARCH=1` with a broad set of x86_64 targets for
runtime dispatch) and once for the `avx2` variant (OpenBLAS `DYNAMIC_ARCH=1` restricted
to Haswell/Skylake targets via `DYNAMIC_LIST`, COIN-OR compiled with
`-march=haswell -DCOIN_AVX2=4`). Both variants use `NO_CBLAS=1` (COIN-OR only calls
the Fortran BLAS interface). AMD is built only once (it is pure
combinatorial code with no BLAS dependency) and reused by both COIN-OR variants.

The COIN-OR stack (CoinUtils, Osi, Clp, Cgl, Cbc) is always compiled with
`-ffp-contract=off`, which prevents the compiler from fusing separate
multiply/add operations into FMA instructions. FMA computes with extra
intermediate precision, which can introduce tiny (last-bit) numerical
differences that make CBC's branch-and-cut behave inconsistently across
toolchains/architectures; disabling contraction keeps results reproducible.
This flag is not applied to OpenBLAS or AMD, whose own numerics are
unaffected by this concern.

Symmetry detection via Nauty is currently disabled (`--without-nauty`) and
is not part of this build.

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
| Linux aarch64 | 48.50 | — | — |
| Darwin x86_64 | 57.56 | 20.72 | 2.78× |
| Darwin arm64 | 47.21 | — | — |
| Linux x86_64 | 53.25 | 17.78 | 3.00× |
| Windows AMD64 | 46.96 | 19.68 | 2.39× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 38.80 | — | — |
| Darwin x86_64 | 45.93 | 18.03 | 2.55× |
| Darwin arm64 | 34.76 | — | — |
| Linux x86_64 | 52.73 | 16.12 | 3.27× |
| Windows AMD64 | 36.62 | 15.47 | 2.37× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 12.62 | 9.51 | 1.33× |
| Darwin x86_64 | avx2 | 6.20 | 8.10 | 0.76× |
| Darwin x86_64 | generic | 18.61 | 18.45 | 1.01× |
| Darwin arm64 | generic | 13.11 | 10.44 | 1.26× |
| Linux x86_64 | avx2 | 4.78 | 5.48 | 0.87× |
| Linux x86_64 | generic | 14.08 | 14.03 | 1.00× |
| Windows AMD64 | avx2 | 5.24 | 5.14 | 1.02× |
| Windows AMD64 | generic | 11.98 | 9.92 | 1.21× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 97.21 | 110.62 | 0.88× |
| Darwin x86_64 | avx2 | 50.71 | 37.33 | 1.36× |
| Darwin x86_64 | generic | 146.31 | 111.03 | 1.32× |
| Darwin arm64 | generic | 147.30 | 104.44 | 1.41× |
| Linux x86_64 | avx2 | 29.67 | 34.07 | 0.87× |
| Linux x86_64 | generic | 113.69 | 131.24 | 0.87× |
| Windows AMD64 | avx2 | 33.49 | 34.68 | 0.97× |
| Windows AMD64 | generic | 181.11 | 108.74 | 1.67× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.57 | 7.19 | 0.77× |
| Darwin x86_64 | avx2 | 2.67 | 2.63 | 1.02× |
| Darwin x86_64 | generic | 7.10 | 8.09 | 0.88× |
| Darwin arm64 | generic | 5.37 | 5.86 | 0.92× |
| Linux x86_64 | avx2 | 1.90 | 2.37 | 0.80× |
| Linux x86_64 | generic | 6.47 | 8.35 | 0.77× |
| Windows AMD64 | avx2 | 1.99 | 2.36 | 0.84× |
| Windows AMD64 | generic | 5.01 | 6.51 | 0.77× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 105.75 | 104.39 | 1.01× |
| Darwin x86_64 | avx2 | 44.70 | 32.81 | 1.36× |
| Darwin x86_64 | generic | 109.65 | 74.70 | 1.47× |
| Darwin arm64 | generic | 89.82 | 58.56 | 1.53× |
| Linux x86_64 | avx2 | 40.08 | 34.11 | 1.18× |
| Linux x86_64 | generic | 118.38 | 122.26 | 0.97× |
| Windows AMD64 | avx2 | 47.49 | 41.63 | 1.14× |
| Windows AMD64 | generic | 98.74 | 92.39 | 1.07× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 75.54 | 51.27 | 1.47× |
| Darwin x86_64 | avx2 | 41.08 | 18.48 | 2.22× |
| Darwin x86_64 | generic | 99.97 | 49.12 | 2.04× |
| Darwin arm64 | generic | 92.56 | 49.26 | 1.88× |
| Linux x86_64 | avx2 | 30.38 | 18.59 | 1.63× |
| Linux x86_64 | generic | 85.93 | 45.26 | 1.90× |
| Windows AMD64 | avx2 | 36.47 | 17.13 | 2.13× |
| Windows AMD64 | generic | 73.13 | 37.20 | 1.97× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.71 | 34.18 | 0.87× |
| Darwin x86_64 | avx2 | 15.16 | 11.59 | 1.31× |
| Darwin x86_64 | generic | 49.30 | 34.81 | 1.42× |
| Darwin arm64 | generic | 40.77 | 27.37 | 1.49× |
| Linux x86_64 | avx2 | 9.66 | 11.23 | 0.86× |
| Linux x86_64 | generic | 33.60 | 34.80 | 0.97× |
| Windows AMD64 | avx2 | 12.77 | 11.19 | 1.14× |
| Windows AMD64 | generic | 26.31 | 26.60 | 0.99× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 479.71 | 471.86 | 1.02× |
| Darwin x86_64 | avx2 | 156.50 | 161.82 | 0.97× |
| Darwin x86_64 | generic | 367.48 | 368.64 | 1.00× |
| Darwin arm64 | generic | 296.66 | 300.85 | 0.99× |
| Linux x86_64 | avx2 | 186.54 | 187.11 | 1.00× |
| Linux x86_64 | generic | 501.18 | 561.34 | 0.89× |
| Windows AMD64 | avx2 | 228.05 | 176.13 | 1.29× |
| Windows AMD64 | generic | 511.50 | 353.41 | 1.45× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.39 | 3.50 | 0.97× |
| Darwin x86_64 | avx2 | 1.06 | 1.13 | 0.94× |
| Darwin x86_64 | generic | 2.23 | 3.94 | 0.56× |
| Darwin arm64 | generic | 1.66 | 2.60 | 0.64× |
| Linux x86_64 | avx2 | 1.34 | 1.30 | 1.04× |
| Linux x86_64 | generic | 3.85 | 4.04 | 0.95× |
| Windows AMD64 | avx2 | 1.46 | 1.31 | 1.12× |
| Windows AMD64 | generic | 2.58 | 3.02 | 0.86× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 106.48 | 95.14 | 1.12× |
| Darwin x86_64 | avx2 | 38.36 | 35.43 | 1.08× |
| Darwin x86_64 | generic | 102.52 | 120.54 | 0.85× |
| Darwin arm64 | generic | 93.51 | 104.15 | 0.90× |
| Linux x86_64 | avx2 | 32.62 | 28.78 | 1.13× |
| Linux x86_64 | generic | 123.19 | 110.47 | 1.12× |
| Windows AMD64 | avx2 | 36.48 | 28.46 | 1.28× |
| Windows AMD64 | generic | 94.26 | 76.56 | 1.23× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 22.45 | 12.63 | 1.78× |
| Darwin x86_64 | avx2 | 9.05 | 8.02 | 1.13× |
| Darwin x86_64 | generic | 21.85 | 15.22 | 1.44× |
| Darwin arm64 | generic | 18.40 | 11.86 | 1.55× |
| Linux x86_64 | avx2 | 8.44 | 7.33 | 1.15× |
| Linux x86_64 | generic | 24.90 | 17.82 | 1.40× |
| Windows AMD64 | avx2 | 8.50 | 5.80 | 1.46× |
| Windows AMD64 | generic | 21.14 | 12.97 | 1.63× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 35.27 | 29.91 | 1.18× |
| Darwin x86_64 | avx2 | 9.20 | 10.91 | 0.84× |
| Darwin x86_64 | generic | 23.79 | 30.68 | 0.78× |
| Darwin arm64 | generic | 24.21 | 30.40 | 0.80× |
| Linux x86_64 | avx2 | 12.53 | 12.35 | 1.01× |
| Linux x86_64 | generic | 37.79 | 35.51 | 1.06× |
| Windows AMD64 | avx2 | 12.86 | 10.38 | 1.24× |
| Windows AMD64 | generic | 30.41 | 25.84 | 1.18× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 65.86 | 20.24 | 3.25× |
| Darwin x86_64 | avx2 | 60.25 | 7.05 | 8.54× |
| Darwin x86_64 | generic | 140.71 | 40.61 | 3.46× |
| Darwin arm64 | generic | 133.53 | 29.86 | 4.47× |
| Linux x86_64 | avx2 | 26.53 | 6.11 | 4.34× |
| Linux x86_64 | generic | 70.27 | 90.46 | 0.78× |
| Windows AMD64 | avx2 | 29.71 | 4.91 | 6.05× |
| Windows AMD64 | generic | 30.68 | 18.62 | 1.65× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.73 | 6.25 | 0.92× |
| Darwin x86_64 | avx2 | 1.59 | 2.29 | 0.69× |
| Darwin x86_64 | generic | 3.50 | 5.18 | 0.68× |
| Darwin arm64 | generic | 3.03 | 5.12 | 0.59× |
| Linux x86_64 | avx2 | 2.09 | 2.14 | 0.98× |
| Linux x86_64 | generic | 6.45 | 7.13 | 0.90× |
| Windows AMD64 | avx2 | 2.30 | 2.09 | 1.10× |
| Windows AMD64 | generic | 6.03 | 5.31 | 1.13× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 342.65 | 91.13 | 3.76× |
| Darwin x86_64 | avx2 | 132.80 | 28.42 | 4.67× |
| Darwin x86_64 | generic | 324.02 | 101.74 | 3.18× |
| Darwin arm64 | generic | 293.90 | 64.14 | 4.58× |
| Linux x86_64 | avx2 | 123.89 | 36.05 | 3.44× |
| Linux x86_64 | generic | 360.32 | 117.21 | 3.07× |
| Windows AMD64 | avx2 | 135.89 | 39.90 | 3.41× |
| Windows AMD64 | generic | 282.36 | 72.81 | 3.88× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 168.76 | 13.03 | 12.95× |
| Darwin x86_64 | avx2 | 60.83 | 6.94 | 8.76× |
| Darwin x86_64 | generic | 152.50 | 19.09 | 7.99× |
| Darwin arm64 | generic | 142.22 | 9.80 | 14.51× |
| Linux x86_64 | avx2 | 62.01 | 4.87 | 12.72× |
| Linux x86_64 | generic | 180.54 | 15.77 | 11.45× |
| Windows AMD64 | avx2 | 73.17 | 5.42 | 13.51× |
| Windows AMD64 | generic | 95.83 | 10.88 | 8.81× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 72.49 | 61.75 | 1.17× |
| Darwin x86_64 | avx2 | 34.32 | 51.37 | 0.67× |
| Darwin x86_64 | generic | 84.33 | 100.10 | 0.84× |
| Darwin arm64 | generic | 68.01 | 63.72 | 1.07× |
| Linux x86_64 | avx2 | 27.58 | 41.35 | 0.67× |
| Linux x86_64 | generic | 79.79 | 90.68 | 0.88× |
| Windows AMD64 | avx2 | 26.46 | 34.36 | 0.77× |
| Windows AMD64 | generic | 71.46 | 60.31 | 1.18× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 45.97 | 34.82 | 1.32× |
| Darwin x86_64 | avx2 | 14.93 | 39.02 | 0.38× |
| Darwin x86_64 | generic | 38.30 | 68.00 | 0.56× |
| Darwin arm64 | generic | 29.94 | 39.67 | 0.75× |
| Linux x86_64 | avx2 | 19.98 | 28.53 | 0.70× |
| Linux x86_64 | generic | 51.05 | 52.78 | 0.97× |
| Windows AMD64 | avx2 | 16.10 | 24.59 | 0.65× |
| Windows AMD64 | generic | 41.02 | 43.05 | 0.95× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.04 | 32.48 | 0.89× |
| Darwin x86_64 | avx2 | 20.06 | 9.09 | 2.21× |
| Darwin x86_64 | generic | 60.46 | 22.22 | 2.72× |
| Darwin arm64 | generic | 47.50 | 15.42 | 3.08× |
| Linux x86_64 | avx2 | 8.90 | 7.86 | 1.13× |
| Linux x86_64 | generic | 28.61 | 38.64 | 0.74× |
| Windows AMD64 | avx2 | 8.99 | 8.39 | 1.07× |
| Windows AMD64 | generic | 96.46 | 43.29 | 2.23× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 119.34 | 46.03 | 2.59× |
| Darwin x86_64 | avx2 | 42.51 | 29.76 | 1.43× |
| Darwin x86_64 | generic | 158.18 | 65.14 | 2.43× |
| Darwin arm64 | generic | 155.16 | 55.81 | 2.78× |
| Linux x86_64 | avx2 | 39.51 | 17.05 | 2.32× |
| Linux x86_64 | generic | 141.81 | 68.60 | 2.07× |
| Windows AMD64 | avx2 | 43.90 | 17.41 | 2.52× |
| Windows AMD64 | generic | 104.45 | 47.67 | 2.19× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.83 | 5.84 | 1.00× |
| Darwin x86_64 | avx2 | 2.14 | 3.04 | 0.71× |
| Darwin x86_64 | generic | 6.21 | 7.55 | 0.82× |
| Darwin arm64 | generic | 5.90 | 1.95 | 3.03× |
| Linux x86_64 | avx2 | 1.83 | 1.89 | 0.97× |
| Linux x86_64 | generic | 6.55 | 6.86 | 0.96× |
| Windows AMD64 | avx2 | 2.04 | 0.69 | 2.94× |
| Windows AMD64 | generic | 4.16 | 1.74 | 2.40× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.67 | 43.25 | 0.94× |
| Darwin x86_64 | avx2 | 13.62 | 21.14 | 0.64× |
| Darwin x86_64 | generic | 33.34 | 41.14 | 0.81× |
| Darwin arm64 | generic | 26.75 | 34.02 | 0.79× |
| Linux x86_64 | avx2 | 14.33 | 13.25 | 1.08× |
| Linux x86_64 | generic | 40.33 | 46.18 | 0.87× |
| Windows AMD64 | avx2 | 16.89 | 16.02 | 1.05× |
| Windows AMD64 | generic | 35.54 | 39.55 | 0.90× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 49.99 | 139.51 | 0.36× |
| Darwin x86_64 | avx2 | — | 34.11 | — |
| Darwin x86_64 | generic | — | 61.36 | — |
| Darwin arm64 | generic | — | 53.60 | — |
| Linux x86_64 | avx2 | 19.76 | 58.53 | 0.34× |
| Linux x86_64 | generic | 51.40 | 144.47 | 0.36× |
| Windows AMD64 | avx2 | 27.89 | 65.78 | 0.42× |
| Windows AMD64 | generic | 44.57 | 112.09 | 0.40× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.28 | 26.62 | 1.40× |
| Darwin x86_64 | avx2 | 52.45 | 14.43 | 3.63× |
| Darwin x86_64 | generic | 136.17 | 23.00 | 5.92× |
| Darwin arm64 | generic | 111.97 | 14.09 | 7.95× |
| Linux x86_64 | avx2 | 13.89 | 19.33 | 0.72× |
| Linux x86_64 | generic | 39.86 | 99.62 | 0.40× |
| Windows AMD64 | avx2 | 18.53 | 21.57 | 0.86× |
| Windows AMD64 | generic | 35.21 | 22.51 | 1.56× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 63.70 | 114.58 | 0.56× |
| Darwin x86_64 | avx2 | 26.55 | 168.44 | 0.16× |
| Darwin x86_64 | generic | 69.55 | 194.43 | 0.36× |
| Darwin arm64 | generic | 32.49 | 77.66 | 0.42× |
| Linux x86_64 | avx2 | 30.40 | 147.70 | 0.21× |
| Linux x86_64 | generic | 63.60 | 248.62 | 0.26× |
| Windows AMD64 | avx2 | 17.15 | 78.49 | 0.22× |
| Windows AMD64 | generic | 41.51 | 124.43 | 0.33× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.44 | 19.84 | 0.93× |
| Darwin x86_64 | avx2 | 6.32 | 8.91 | 0.71× |
| Darwin x86_64 | generic | 26.43 | 35.24 | 0.75× |
| Darwin arm64 | generic | 18.34 | 32.79 | 0.56× |
| Linux x86_64 | avx2 | 7.94 | 7.41 | 1.07× |
| Linux x86_64 | generic | 30.63 | 28.31 | 1.08× |
| Windows AMD64 | avx2 | 9.66 | 8.88 | 1.09× |
| Windows AMD64 | generic | 21.91 | 18.60 | 1.18× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 174.36 | 134.40 | 1.30× |
| Darwin x86_64 | avx2 | 43.90 | 48.80 | 0.90× |
| Darwin x86_64 | generic | 145.57 | 129.59 | 1.12× |
| Darwin arm64 | generic | 110.85 | 122.79 | 0.90× |
| Linux x86_64 | avx2 | 59.70 | 56.78 | 1.05× |
| Linux x86_64 | generic | 172.38 | 160.10 | 1.08× |
| Windows AMD64 | avx2 | 65.84 | 59.87 | 1.10× |
| Windows AMD64 | generic | 150.07 | 130.93 | 1.15× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 158.04 | 201.53 | 0.78× |
| Darwin x86_64 | avx2 | 45.29 | 123.06 | 0.37× |
| Darwin x86_64 | generic | 136.34 | 333.40 | 0.41× |
| Darwin arm64 | generic | 107.47 | 296.76 | 0.36× |
| Linux x86_64 | avx2 | 52.00 | 99.41 | 0.52× |
| Linux x86_64 | generic | 161.06 | 326.71 | 0.49× |
| Windows AMD64 | avx2 | 54.44 | 94.62 | 0.58× |
| Windows AMD64 | generic | 246.20 | 328.50 | 0.75× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.62 | 39.45 | 0.95× |
| Darwin x86_64 | avx2 | 18.35 | 19.84 | 0.92× |
| Darwin x86_64 | generic | 106.71 | 94.63 | 1.13× |
| Darwin arm64 | generic | 71.67 | 70.67 | 1.01× |
| Linux x86_64 | avx2 | 15.68 | 15.96 | 0.98× |
| Linux x86_64 | generic | 39.44 | 42.60 | 0.93× |
| Windows AMD64 | avx2 | 19.73 | 18.63 | 1.06× |
| Windows AMD64 | generic | 71.59 | 65.91 | 1.09× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.53 | 140.52 | 0.97× |
| Darwin x86_64 | avx2 | 50.38 | 65.35 | 0.77× |
| Darwin x86_64 | generic | 133.49 | 160.16 | 0.83× |
| Darwin arm64 | generic | 115.63 | 149.35 | 0.77× |
| Linux x86_64 | avx2 | 52.74 | 55.26 | 0.95× |
| Linux x86_64 | generic | 143.71 | 148.78 | 0.97× |
| Windows AMD64 | avx2 | 62.50 | 58.24 | 1.07× |
| Windows AMD64 | generic | 112.53 | 254.46 | 0.44× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 90.94 | 36.33 | 2.50× |
| Darwin x86_64 | avx2 | 76.24 | 23.52 | 3.24× |
| Darwin x86_64 | generic | 220.68 | 53.19 | 4.15× |
| Darwin arm64 | generic | 184.90 | 113.18 | 1.63× |
| Linux x86_64 | avx2 | 31.14 | 14.88 | 2.09× |
| Linux x86_64 | generic | 96.61 | 60.70 | 1.59× |
| Windows AMD64 | avx2 | 43.74 | 19.91 | 2.20× |
| Windows AMD64 | generic | 92.76 | 38.41 | 2.41× |


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


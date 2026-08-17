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

The AVX2/Haswell build is **~2.9×** faster than the generic build on average (geometric mean across 30 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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
| Linux aarch64 | 48.67 | — | — |
| Darwin x86_64 | 74.14 | 29.32 | 2.53× |
| Darwin arm64 | 45.79 | — | — |
| Linux x86_64 | 53.50 | 17.44 | 3.07× |
| Windows AMD64 | 57.55 | 18.25 | 3.15× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 39.86 | — | — |
| Darwin x86_64 | 65.14 | 24.92 | 2.61× |
| Darwin arm64 | 32.42 | — | — |
| Linux x86_64 | 49.95 | 16.44 | 3.04× |
| Windows AMD64 | 51.55 | 16.85 | 3.06× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 12.92 | 10.42 | 1.24× |
| Darwin x86_64 | avx2 | 6.22 | 9.47 | 0.66× |
| Darwin x86_64 | generic | 18.23 | 38.63 | 0.47× |
| Darwin arm64 | generic | 10.67 | 9.18 | 1.16× |
| Linux x86_64 | avx2 | 4.71 | 5.37 | 0.88× |
| Linux x86_64 | generic | 14.08 | 14.14 | 1.00× |
| Windows AMD64 | avx2 | 4.83 | 9.37 | 0.52× |
| Windows AMD64 | generic | 13.30 | 16.16 | 0.82× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 98.06 | 110.14 | 0.89× |
| Darwin x86_64 | avx2 | 55.31 | 48.55 | 1.14× |
| Darwin x86_64 | generic | 189.57 | 178.49 | 1.06× |
| Darwin arm64 | generic | 140.33 | 98.71 | 1.42× |
| Linux x86_64 | avx2 | 29.17 | 34.32 | 0.85× |
| Linux x86_64 | generic | 113.68 | 135.51 | 0.84× |
| Windows AMD64 | avx2 | 32.48 | 42.07 | 0.77× |
| Windows AMD64 | generic | 233.33 | 140.04 | 1.67× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.64 | 7.21 | 0.78× |
| Darwin x86_64 | avx2 | 2.74 | 3.61 | 0.76× |
| Darwin x86_64 | generic | 10.49 | 11.02 | 0.95× |
| Darwin arm64 | generic | 6.82 | 5.67 | 1.20× |
| Linux x86_64 | avx2 | 1.86 | 2.41 | 0.77× |
| Linux x86_64 | generic | 6.54 | 8.33 | 0.79× |
| Windows AMD64 | avx2 | 2.02 | 2.92 | 0.69× |
| Windows AMD64 | generic | 6.73 | 8.43 | 0.80× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 106.01 | 104.40 | 1.02× |
| Darwin x86_64 | avx2 | 47.47 | 37.97 | 1.25× |
| Darwin x86_64 | generic | 139.81 | 106.02 | 1.32× |
| Darwin arm64 | generic | 95.89 | 64.80 | 1.48× |
| Linux x86_64 | avx2 | 39.55 | 34.04 | 1.16× |
| Linux x86_64 | generic | 118.22 | 109.93 | 1.08× |
| Windows AMD64 | avx2 | 45.23 | 44.92 | 1.01× |
| Windows AMD64 | generic | 121.59 | 113.91 | 1.07× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 76.62 | 54.01 | 1.42× |
| Darwin x86_64 | avx2 | 61.57 | 25.97 | 2.37× |
| Darwin x86_64 | generic | 118.38 | 68.90 | 1.72× |
| Darwin arm64 | generic | 83.48 | 40.77 | 2.05× |
| Linux x86_64 | avx2 | 29.80 | 19.00 | 1.57× |
| Linux x86_64 | generic | 85.64 | 59.99 | 1.43× |
| Windows AMD64 | avx2 | 34.56 | 23.71 | 1.46× |
| Windows AMD64 | generic | 87.25 | 45.07 | 1.94× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.20 | 34.65 | 0.87× |
| Darwin x86_64 | avx2 | 25.62 | 19.73 | 1.30× |
| Darwin x86_64 | generic | 56.95 | 44.71 | 1.27× |
| Darwin arm64 | generic | 33.01 | 23.78 | 1.39× |
| Linux x86_64 | avx2 | 9.29 | 10.07 | 0.92× |
| Linux x86_64 | generic | 33.44 | 34.93 | 0.96× |
| Windows AMD64 | avx2 | 11.47 | 13.47 | 0.85× |
| Windows AMD64 | generic | 34.19 | 35.92 | 0.95× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 482.49 | 473.77 | 1.02× |
| Darwin x86_64 | avx2 | 216.41 | 192.69 | 1.12× |
| Darwin x86_64 | generic | 381.88 | 552.71 | 0.69× |
| Darwin arm64 | generic | 278.24 | 253.10 | 1.10× |
| Linux x86_64 | avx2 | 183.27 | 183.67 | 1.00× |
| Linux x86_64 | generic | 504.97 | 517.86 | 0.98× |
| Windows AMD64 | avx2 | 199.85 | 225.42 | 0.89× |
| Windows AMD64 | generic | 627.39 | 484.88 | 1.29× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.40 | 3.50 | 0.97× |
| Darwin x86_64 | avx2 | 1.65 | 1.48 | 1.11× |
| Darwin x86_64 | generic | 2.89 | 4.17 | 0.69× |
| Darwin arm64 | generic | 1.78 | 2.34 | 0.76× |
| Linux x86_64 | avx2 | 1.29 | 1.27 | 1.02× |
| Linux x86_64 | generic | 3.85 | 4.04 | 0.95× |
| Windows AMD64 | avx2 | 1.35 | 1.46 | 0.93× |
| Windows AMD64 | generic | 3.16 | 3.91 | 0.81× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 107.17 | 95.04 | 1.13× |
| Darwin x86_64 | avx2 | 53.15 | 48.69 | 1.09× |
| Darwin x86_64 | generic | 127.70 | 137.87 | 0.93× |
| Darwin arm64 | generic | 94.79 | 93.03 | 1.02× |
| Linux x86_64 | avx2 | 32.19 | 28.62 | 1.12× |
| Linux x86_64 | generic | 122.61 | 110.70 | 1.11× |
| Windows AMD64 | avx2 | 35.17 | 32.38 | 1.09× |
| Windows AMD64 | generic | 127.27 | 112.65 | 1.13× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 22.59 | 13.17 | 1.72× |
| Darwin x86_64 | avx2 | 13.63 | 15.10 | 0.90× |
| Darwin x86_64 | generic | 27.62 | 20.81 | 1.33× |
| Darwin arm64 | generic | 17.41 | 8.45 | 2.06× |
| Linux x86_64 | avx2 | 8.43 | 7.76 | 1.09× |
| Linux x86_64 | generic | 24.93 | 17.29 | 1.44× |
| Windows AMD64 | avx2 | 8.11 | 6.65 | 1.22× |
| Windows AMD64 | generic | 25.20 | 17.25 | 1.46× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 35.37 | 30.14 | 1.17× |
| Darwin x86_64 | avx2 | 14.76 | 22.17 | 0.67× |
| Darwin x86_64 | generic | 31.31 | 41.19 | 0.76× |
| Darwin arm64 | generic | 21.11 | 25.94 | 0.81× |
| Linux x86_64 | avx2 | 12.47 | 11.54 | 1.08× |
| Linux x86_64 | generic | 37.97 | 33.98 | 1.12× |
| Windows AMD64 | avx2 | 12.63 | 12.31 | 1.03× |
| Windows AMD64 | generic | 39.01 | 35.05 | 1.11× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 66.95 | 21.81 | 3.07× |
| Darwin x86_64 | avx2 | 90.50 | 26.34 | 3.44× |
| Darwin x86_64 | generic | 196.64 | 29.70 | 6.62× |
| Darwin arm64 | generic | 132.17 | 15.81 | 8.36× |
| Linux x86_64 | avx2 | 26.04 | 5.56 | 4.68× |
| Linux x86_64 | generic | 70.49 | 22.84 | 3.09× |
| Windows AMD64 | avx2 | 26.22 | 6.45 | 4.07× |
| Windows AMD64 | generic | 46.44 | 26.30 | 1.77× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.83 | 6.43 | 0.91× |
| Darwin x86_64 | avx2 | 2.18 | 3.93 | 0.55× |
| Darwin x86_64 | generic | 4.44 | 7.18 | 0.62× |
| Darwin arm64 | generic | 3.00 | 3.72 | 0.81× |
| Linux x86_64 | avx2 | 1.97 | 2.11 | 0.93× |
| Linux x86_64 | generic | 6.62 | 7.11 | 0.93× |
| Windows AMD64 | avx2 | 2.17 | 2.31 | 0.94× |
| Windows AMD64 | generic | 7.48 | 6.78 | 1.10× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 341.48 | 95.86 | 3.56× |
| Darwin x86_64 | avx2 | 181.18 | 50.56 | 3.58× |
| Darwin x86_64 | generic | 508.58 | 130.60 | 3.89× |
| Darwin arm64 | generic | 292.38 | 66.79 | 4.38× |
| Linux x86_64 | avx2 | 123.74 | 45.73 | 2.71× |
| Linux x86_64 | generic | 365.37 | 146.21 | 2.50× |
| Windows AMD64 | avx2 | 119.45 | 38.08 | 3.14× |
| Windows AMD64 | generic | 340.88 | 98.16 | 3.47× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 167.08 | 13.68 | 12.21× |
| Darwin x86_64 | avx2 | 79.64 | 9.95 | 8.00× |
| Darwin x86_64 | generic | 263.15 | 28.72 | 9.16× |
| Darwin arm64 | generic | 124.74 | 11.23 | 11.10× |
| Linux x86_64 | avx2 | 61.20 | 5.62 | 10.89× |
| Linux x86_64 | generic | 179.95 | 15.99 | 11.25× |
| Windows AMD64 | avx2 | 65.71 | 5.57 | 11.80× |
| Windows AMD64 | generic | 108.18 | 14.88 | 7.27× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 72.30 | 63.94 | 1.13× |
| Darwin x86_64 | avx2 | 44.06 | 63.22 | 0.70× |
| Darwin x86_64 | generic | 139.35 | 130.31 | 1.07× |
| Darwin arm64 | generic | 64.07 | 59.61 | 1.07× |
| Linux x86_64 | avx2 | 27.11 | 39.48 | 0.69× |
| Linux x86_64 | generic | 79.85 | 93.65 | 0.85× |
| Windows AMD64 | avx2 | 25.90 | 36.29 | 0.71× |
| Windows AMD64 | generic | 78.07 | 83.18 | 0.94× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 45.91 | 37.22 | 1.23× |
| Darwin x86_64 | avx2 | 19.67 | 51.07 | 0.39× |
| Darwin x86_64 | generic | 64.97 | 79.74 | 0.81× |
| Darwin arm64 | generic | 33.74 | 45.35 | 0.74× |
| Linux x86_64 | avx2 | 19.61 | 29.49 | 0.66× |
| Linux x86_64 | generic | 50.98 | 56.12 | 0.91× |
| Windows AMD64 | avx2 | 16.71 | 26.89 | 0.62× |
| Windows AMD64 | generic | 47.56 | 63.11 | 0.75× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.00 | 33.39 | 0.87× |
| Darwin x86_64 | avx2 | 28.34 | 8.99 | 3.15× |
| Darwin x86_64 | generic | 85.85 | 26.97 | 3.18× |
| Darwin arm64 | generic | 58.84 | 14.08 | 4.18× |
| Linux x86_64 | avx2 | 8.66 | 11.03 | 0.79× |
| Linux x86_64 | generic | 28.45 | 26.67 | 1.07× |
| Windows AMD64 | avx2 | 8.48 | 9.99 | 0.85× |
| Windows AMD64 | generic | 112.48 | 28.55 | 3.94× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 119.30 | 46.90 | 2.54× |
| Darwin x86_64 | avx2 | 69.46 | 26.22 | 2.65× |
| Darwin x86_64 | generic | 188.93 | 100.23 | 1.88× |
| Darwin arm64 | generic | 159.92 | 63.65 | 2.51× |
| Linux x86_64 | avx2 | 39.13 | 17.51 | 2.23× |
| Linux x86_64 | generic | 142.54 | 59.52 | 2.40× |
| Windows AMD64 | avx2 | 41.56 | 18.18 | 2.29× |
| Windows AMD64 | generic | 142.54 | 59.51 | 2.40× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.79 | 6.13 | 0.95× |
| Darwin x86_64 | avx2 | 2.86 | 3.77 | 0.76× |
| Darwin x86_64 | generic | 8.01 | 10.50 | 0.76× |
| Darwin arm64 | generic | 5.67 | 2.34 | 2.42× |
| Linux x86_64 | avx2 | 1.75 | 1.79 | 0.98× |
| Linux x86_64 | generic | 6.79 | 7.67 | 0.89× |
| Windows AMD64 | avx2 | 1.96 | 0.72 | 2.74× |
| Windows AMD64 | generic | 5.04 | 5.27 | 0.96× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.32 | 43.74 | 0.92× |
| Darwin x86_64 | avx2 | 17.49 | 22.15 | 0.79× |
| Darwin x86_64 | generic | 40.74 | 56.37 | 0.72× |
| Darwin arm64 | generic | 22.89 | 31.96 | 0.72× |
| Linux x86_64 | avx2 | 14.06 | 12.76 | 1.10× |
| Linux x86_64 | generic | 41.00 | 46.19 | 0.89× |
| Windows AMD64 | avx2 | 14.85 | 14.82 | 1.00× |
| Windows AMD64 | generic | 42.82 | 55.15 | 0.78× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 48.98 | 139.04 | 0.35× |
| Darwin x86_64 | avx2 | — | 40.27 | — |
| Darwin x86_64 | generic | — | 103.89 | — |
| Darwin arm64 | generic | — | 54.06 | — |
| Linux x86_64 | avx2 | 19.28 | 57.95 | 0.33× |
| Linux x86_64 | generic | 52.58 | 145.83 | 0.36× |
| Windows AMD64 | avx2 | 20.09 | 58.74 | 0.34× |
| Windows AMD64 | generic | 52.71 | 150.43 | 0.35× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.53 | 27.21 | 1.38× |
| Darwin x86_64 | avx2 | 71.74 | 18.66 | 3.84× |
| Darwin x86_64 | generic | 193.47 | 44.87 | 4.31× |
| Darwin arm64 | generic | 102.53 | 15.70 | 6.53× |
| Linux x86_64 | avx2 | 13.69 | 24.47 | 0.56× |
| Linux x86_64 | generic | 40.15 | 79.88 | 0.50× |
| Windows AMD64 | avx2 | 14.74 | 16.01 | 0.92× |
| Windows AMD64 | generic | 40.90 | 71.46 | 0.57× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 63.39 | 121.11 | 0.52× |
| Darwin x86_64 | avx2 | 36.83 | 263.16 | 0.14× |
| Darwin x86_64 | generic | 94.77 | 326.01 | 0.29× |
| Darwin arm64 | generic | 31.57 | 127.15 | 0.25× |
| Linux x86_64 | avx2 | 30.21 | 142.93 | 0.21× |
| Linux x86_64 | generic | 65.74 | 183.27 | 0.36× |
| Windows AMD64 | avx2 | 19.46 | 91.70 | 0.21× |
| Windows AMD64 | generic | 50.69 | 138.92 | 0.36× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.40 | 19.85 | 0.93× |
| Darwin x86_64 | avx2 | 9.41 | 11.35 | 0.83× |
| Darwin x86_64 | generic | 30.34 | 52.39 | 0.58× |
| Darwin arm64 | generic | 18.73 | 28.76 | 0.65× |
| Linux x86_64 | avx2 | 7.77 | 7.28 | 1.07× |
| Linux x86_64 | generic | 30.42 | 28.34 | 1.07× |
| Windows AMD64 | avx2 | 9.41 | 8.80 | 1.07× |
| Windows AMD64 | generic | 30.56 | 28.60 | 1.07× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 174.38 | 134.74 | 1.29× |
| Darwin x86_64 | avx2 | 87.21 | 66.01 | 1.32× |
| Darwin x86_64 | generic | 162.35 | 185.51 | 0.88× |
| Darwin arm64 | generic | 112.90 | 116.10 | 0.97× |
| Linux x86_64 | avx2 | 59.76 | 55.11 | 1.08× |
| Linux x86_64 | generic | 172.86 | 162.58 | 1.06× |
| Windows AMD64 | avx2 | 60.61 | 56.24 | 1.08× |
| Windows AMD64 | generic | 176.98 | 172.63 | 1.03× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 158.97 | 252.79 | 0.63× |
| Darwin x86_64 | avx2 | 89.43 | 165.10 | 0.54× |
| Darwin x86_64 | generic | 157.47 | 725.42 | 0.22× |
| Darwin arm64 | generic | 103.62 | 279.12 | 0.37× |
| Linux x86_64 | avx2 | 51.57 | 83.96 | 0.61× |
| Linux x86_64 | generic | 160.24 | 457.43 | 0.35× |
| Windows AMD64 | avx2 | 51.58 | 87.77 | 0.59× |
| Windows AMD64 | generic | 278.01 | 532.62 | 0.52× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.48 | 39.27 | 0.95× |
| Darwin x86_64 | avx2 | 31.74 | 25.86 | 1.23× |
| Darwin x86_64 | generic | 120.86 | 126.38 | 0.96× |
| Darwin arm64 | generic | 67.55 | 69.96 | 0.97× |
| Linux x86_64 | avx2 | 15.49 | 16.01 | 0.97× |
| Linux x86_64 | generic | 39.45 | 42.17 | 0.94× |
| Windows AMD64 | avx2 | 17.96 | 18.80 | 0.96× |
| Windows AMD64 | generic | 91.93 | 95.20 | 0.97× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.47 | 140.78 | 0.97× |
| Darwin x86_64 | avx2 | 71.72 | 87.05 | 0.82× |
| Darwin x86_64 | generic | 168.09 | 235.65 | 0.71× |
| Darwin arm64 | generic | 99.90 | 137.45 | 0.73× |
| Linux x86_64 | avx2 | 51.85 | 55.19 | 0.94× |
| Linux x86_64 | generic | 143.40 | 152.60 | 0.94× |
| Windows AMD64 | avx2 | 56.54 | 58.52 | 0.97× |
| Windows AMD64 | generic | 130.23 | 171.10 | 0.76× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 92.59 | 32.59 | 2.84× |
| Darwin x86_64 | avx2 | 122.70 | 28.73 | 4.27× |
| Darwin x86_64 | generic | 252.11 | 90.54 | 2.78× |
| Darwin arm64 | generic | 171.02 | 69.84 | 2.45× |
| Linux x86_64 | avx2 | 29.93 | 18.47 | 1.62× |
| Linux x86_64 | generic | 95.06 | 55.80 | 1.70× |
| Windows AMD64 | avx2 | 36.47 | 17.72 | 2.06× |
| Windows AMD64 | generic | 103.79 | 118.22 | 0.88× |


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


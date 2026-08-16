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

The AVX2/Haswell build is **~3.1×** faster than the generic build on average (geometric mean across 30 instances, 2 x86_64 platforms: Linux x86_64, Windows AMD64).

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
| Linux aarch64 | 48.61 | — | — |
| Darwin arm64 | 48.62 | — | — |
| Linux x86_64 | 53.00 | 17.31 | 3.06× |
| Windows AMD64 | 57.17 | 18.46 | 3.10× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 39.55 | — | — |
| Darwin arm64 | 32.70 | — | — |
| Linux x86_64 | 49.98 | 17.27 | 2.89× |
| Windows AMD64 | 50.19 | 17.29 | 2.90× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 12.63 | 14.39 | 0.88× |
| Darwin arm64 | generic | 15.01 | 8.58 | 1.75× |
| Linux x86_64 | avx2 | 4.64 | 5.59 | 0.83× |
| Linux x86_64 | generic | 13.94 | 14.58 | 0.96× |
| Windows AMD64 | avx2 | 4.87 | 5.73 | 0.85× |
| Windows AMD64 | generic | 13.61 | 17.56 | 0.78× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 96.96 | 110.06 | 0.88× |
| Darwin arm64 | generic | 167.12 | 106.00 | 1.58× |
| Linux x86_64 | avx2 | 29.05 | 33.90 | 0.86× |
| Linux x86_64 | generic | 112.85 | 134.02 | 0.84× |
| Windows AMD64 | avx2 | 32.83 | 38.83 | 0.85× |
| Windows AMD64 | generic | 237.53 | 143.66 | 1.65× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.61 | 7.16 | 0.78× |
| Darwin arm64 | generic | 4.85 | 6.12 | 0.79× |
| Linux x86_64 | avx2 | 1.86 | 2.36 | 0.79× |
| Linux x86_64 | generic | 6.45 | 8.20 | 0.79× |
| Windows AMD64 | avx2 | 2.06 | 2.73 | 0.76× |
| Windows AMD64 | generic | 6.71 | 8.55 | 0.78× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 105.86 | 105.64 | 1.00× |
| Darwin arm64 | generic | 88.98 | 63.02 | 1.41× |
| Linux x86_64 | avx2 | 39.45 | 34.72 | 1.14× |
| Linux x86_64 | generic | 117.92 | 111.51 | 1.06× |
| Windows AMD64 | avx2 | 45.55 | 54.84 | 0.83× |
| Windows AMD64 | generic | 119.75 | 123.08 | 0.97× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 75.55 | 50.39 | 1.50× |
| Darwin arm64 | generic | 90.16 | 47.38 | 1.90× |
| Linux x86_64 | avx2 | 29.72 | 17.89 | 1.66× |
| Linux x86_64 | generic | 85.13 | 44.96 | 1.89× |
| Windows AMD64 | avx2 | 33.80 | 20.29 | 1.67× |
| Windows AMD64 | generic | 86.34 | 67.74 | 1.27× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.91 | 34.54 | 0.87× |
| Darwin arm64 | generic | 38.08 | 25.68 | 1.48× |
| Linux x86_64 | avx2 | 9.28 | 11.29 | 0.82× |
| Linux x86_64 | generic | 33.07 | 34.41 | 0.96× |
| Windows AMD64 | avx2 | 11.78 | 12.51 | 0.94× |
| Windows AMD64 | generic | 34.80 | 36.36 | 0.96× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 484.43 | 476.12 | 1.02× |
| Darwin arm64 | generic | 288.94 | 287.06 | 1.01× |
| Linux x86_64 | avx2 | 183.19 | 179.42 | 1.02× |
| Linux x86_64 | generic | 500.43 | 549.41 | 0.91× |
| Windows AMD64 | avx2 | 199.23 | 212.90 | 0.94× |
| Windows AMD64 | generic | 639.72 | 487.93 | 1.31× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.44 | 3.52 | 0.98× |
| Darwin arm64 | generic | 1.83 | 2.64 | 0.69× |
| Linux x86_64 | avx2 | 1.28 | 1.23 | 1.04× |
| Linux x86_64 | generic | 3.85 | 4.02 | 0.96× |
| Windows AMD64 | avx2 | 1.36 | 1.42 | 0.95× |
| Windows AMD64 | generic | 3.21 | 3.97 | 0.81× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 107.72 | 94.85 | 1.14× |
| Darwin arm64 | generic | 113.52 | 100.74 | 1.13× |
| Linux x86_64 | avx2 | 32.16 | 27.96 | 1.15× |
| Linux x86_64 | generic | 123.37 | 110.68 | 1.11× |
| Windows AMD64 | avx2 | 35.90 | 31.80 | 1.13× |
| Windows AMD64 | generic | 130.95 | 114.93 | 1.14× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 22.75 | 13.44 | 1.69× |
| Darwin arm64 | generic | 21.83 | 9.15 | 2.39× |
| Linux x86_64 | avx2 | 8.26 | 8.10 | 1.02× |
| Linux x86_64 | generic | 24.74 | 17.59 | 1.41× |
| Windows AMD64 | avx2 | 8.18 | 7.33 | 1.12× |
| Windows AMD64 | generic | 24.18 | 17.21 | 1.40× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 35.33 | 30.09 | 1.17× |
| Darwin arm64 | generic | 25.35 | 27.88 | 0.91× |
| Linux x86_64 | avx2 | 12.39 | 11.48 | 1.08× |
| Linux x86_64 | generic | 37.62 | 33.97 | 1.11× |
| Windows AMD64 | avx2 | 12.76 | 11.04 | 1.16× |
| Windows AMD64 | generic | 38.06 | 34.70 | 1.10× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 67.11 | 23.46 | 2.86× |
| Darwin arm64 | generic | 148.46 | 18.12 | 8.19× |
| Linux x86_64 | avx2 | 26.07 | 13.61 | 1.91× |
| Linux x86_64 | generic | 70.37 | 25.97 | 2.71× |
| Windows AMD64 | avx2 | 26.39 | 8.92 | 2.96× |
| Windows AMD64 | generic | 36.34 | 24.05 | 1.51× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.81 | 6.14 | 0.95× |
| Darwin arm64 | generic | 3.36 | 3.99 | 0.84× |
| Linux x86_64 | avx2 | 1.99 | 2.07 | 0.96× |
| Linux x86_64 | generic | 6.45 | 6.99 | 0.92× |
| Windows AMD64 | avx2 | 2.21 | 2.63 | 0.84× |
| Windows AMD64 | generic | 7.22 | 7.03 | 1.03× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 345.42 | 86.93 | 3.97× |
| Darwin arm64 | generic | 327.05 | 71.11 | 4.60× |
| Linux x86_64 | avx2 | 122.62 | 32.38 | 3.79× |
| Linux x86_64 | generic | 361.70 | 131.28 | 2.76× |
| Windows AMD64 | avx2 | 119.85 | 50.15 | 2.39× |
| Windows AMD64 | generic | 333.01 | 92.16 | 3.61× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 168.64 | 14.02 | 12.03× |
| Darwin arm64 | generic | 151.20 | 10.49 | 14.42× |
| Linux x86_64 | avx2 | 60.93 | 5.25 | 11.60× |
| Linux x86_64 | generic | 179.88 | 17.04 | 10.56× |
| Windows AMD64 | avx2 | 66.57 | 6.21 | 10.72× |
| Windows AMD64 | generic | 108.42 | 15.34 | 7.07× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 72.69 | 62.23 | 1.17× |
| Darwin arm64 | generic | 78.46 | 54.32 | 1.44× |
| Linux x86_64 | avx2 | 26.79 | 37.74 | 0.71× |
| Linux x86_64 | generic | 79.72 | 93.11 | 0.86× |
| Windows AMD64 | avx2 | 26.27 | 30.94 | 0.85× |
| Windows AMD64 | generic | 78.71 | 80.68 | 0.98× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 46.11 | 38.13 | 1.21× |
| Darwin arm64 | generic | 36.98 | 32.06 | 1.15× |
| Linux x86_64 | avx2 | 19.40 | 29.43 | 0.66× |
| Linux x86_64 | generic | 50.84 | 60.99 | 0.83× |
| Windows AMD64 | avx2 | 16.77 | 25.70 | 0.65× |
| Windows AMD64 | generic | 47.56 | 57.04 | 0.83× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.17 | 35.24 | 0.83× |
| Darwin arm64 | generic | 54.60 | 14.41 | 3.79× |
| Linux x86_64 | avx2 | 8.60 | 11.95 | 0.72× |
| Linux x86_64 | generic | 28.52 | 42.01 | 0.68× |
| Windows AMD64 | avx2 | 8.69 | 7.88 | 1.10× |
| Windows AMD64 | generic | 112.53 | 27.81 | 4.05× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 118.81 | 45.98 | 2.58× |
| Darwin arm64 | generic | 149.44 | 58.11 | 2.57× |
| Linux x86_64 | avx2 | 38.91 | 19.14 | 2.03× |
| Linux x86_64 | generic | 140.46 | 60.81 | 2.31× |
| Windows AMD64 | avx2 | 41.68 | 18.11 | 2.30× |
| Windows AMD64 | generic | 144.60 | 62.87 | 2.30× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.73 | 5.81 | 0.99× |
| Darwin arm64 | generic | 5.49 | 6.53 | 0.84× |
| Linux x86_64 | avx2 | 1.73 | 1.89 | 0.92× |
| Linux x86_64 | generic | 6.49 | 7.48 | 0.87× |
| Windows AMD64 | avx2 | 1.99 | 2.12 | 0.93× |
| Windows AMD64 | generic | 5.04 | 2.14 | 2.35× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.12 | 43.41 | 0.92× |
| Darwin arm64 | generic | 23.49 | 33.95 | 0.69× |
| Linux x86_64 | avx2 | 13.67 | 12.65 | 1.08× |
| Linux x86_64 | generic | 40.21 | 46.39 | 0.87× |
| Windows AMD64 | avx2 | 15.20 | 15.11 | 1.01× |
| Windows AMD64 | generic | 42.51 | 56.04 | 0.76× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 49.70 | 136.87 | 0.36× |
| Darwin arm64 | generic | — | 50.27 | — |
| Linux x86_64 | avx2 | 19.07 | 57.14 | 0.33× |
| Linux x86_64 | generic | 51.39 | 144.92 | 0.35× |
| Windows AMD64 | avx2 | 20.27 | 59.48 | 0.34× |
| Windows AMD64 | generic | 52.56 | 152.74 | 0.34× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.10 | 18.40 | 2.02× |
| Darwin arm64 | generic | 109.30 | 19.03 | 5.74× |
| Linux x86_64 | avx2 | 13.60 | 27.30 | 0.50× |
| Linux x86_64 | generic | 39.88 | 62.77 | 0.64× |
| Windows AMD64 | avx2 | 14.84 | 16.13 | 0.92× |
| Windows AMD64 | generic | 41.12 | 39.62 | 1.04× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 63.39 | 91.31 | 0.69× |
| Darwin arm64 | generic | 32.50 | 72.24 | 0.45× |
| Linux x86_64 | avx2 | 29.72 | 186.63 | 0.16× |
| Linux x86_64 | generic | 64.16 | 219.31 | 0.29× |
| Windows AMD64 | avx2 | 19.55 | 107.57 | 0.18× |
| Windows AMD64 | generic | 50.49 | 174.05 | 0.29× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.37 | 19.84 | 0.93× |
| Darwin arm64 | generic | 18.13 | 30.24 | 0.60× |
| Linux x86_64 | avx2 | 7.71 | 7.27 | 1.06× |
| Linux x86_64 | generic | 30.40 | 28.07 | 1.08× |
| Windows AMD64 | avx2 | 9.56 | 8.89 | 1.08× |
| Windows AMD64 | generic | 30.80 | 29.07 | 1.06× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 173.58 | 134.40 | 1.29× |
| Darwin arm64 | generic | 107.77 | 113.96 | 0.95× |
| Linux x86_64 | avx2 | 59.23 | 55.25 | 1.07× |
| Linux x86_64 | generic | 172.72 | 160.65 | 1.08× |
| Windows AMD64 | avx2 | 61.02 | 56.60 | 1.08× |
| Windows AMD64 | generic | 177.05 | 172.47 | 1.03× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 157.86 | 240.62 | 0.66× |
| Darwin arm64 | generic | 100.66 | 261.46 | 0.38× |
| Linux x86_64 | avx2 | 50.94 | 98.30 | 0.52× |
| Linux x86_64 | generic | 160.06 | 362.16 | 0.44× |
| Windows AMD64 | avx2 | 52.13 | 89.32 | 0.58× |
| Windows AMD64 | generic | 280.91 | 1075.46 | 0.26× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.66 | 39.28 | 0.96× |
| Darwin arm64 | generic | 63.54 | 65.63 | 0.97× |
| Linux x86_64 | avx2 | 15.38 | 16.01 | 0.96× |
| Linux x86_64 | generic | 38.98 | 42.37 | 0.92× |
| Windows AMD64 | avx2 | 18.19 | 19.00 | 0.96× |
| Windows AMD64 | generic | 89.17 | 123.61 | 0.72× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.12 | 141.34 | 0.96× |
| Darwin arm64 | generic | 110.02 | 138.76 | 0.79× |
| Linux x86_64 | avx2 | 52.04 | 54.92 | 0.95× |
| Linux x86_64 | generic | 142.40 | 151.62 | 0.94× |
| Windows AMD64 | avx2 | 57.24 | 59.13 | 0.97× |
| Windows AMD64 | generic | 135.71 | 141.03 | 0.96× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 92.09 | 43.72 | 2.11× |
| Darwin arm64 | generic | 181.88 | 33.25 | 5.47× |
| Linux x86_64 | avx2 | 29.34 | 24.46 | 1.20× |
| Linux x86_64 | generic | 93.65 | 53.26 | 1.76× |
| Windows AMD64 | avx2 | 38.12 | 14.80 | 2.58× |
| Windows AMD64 | generic | 107.30 | 52.48 | 2.04× |


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


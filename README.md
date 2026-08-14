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
| Linux aarch64 | 48.58 | — | — |
| Darwin x86_64 | 65.05 | 25.25 | 2.58× |
| Darwin arm64 | 49.71 | — | — |
| Linux x86_64 | 53.63 | 18.22 | 2.94× |
| Windows AMD64 | 58.74 | 18.60 | 3.16× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 38.95 | — | — |
| Darwin x86_64 | 51.32 | 20.81 | 2.47× |
| Darwin arm64 | 35.27 | — | — |
| Linux x86_64 | 49.93 | 16.69 | 2.99× |
| Windows AMD64 | 53.59 | 17.22 | 3.11× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 12.64 | 10.40 | 1.22× |
| Darwin x86_64 | avx2 | 5.88 | 10.92 | 0.54× |
| Darwin x86_64 | generic | 17.09 | 19.54 | 0.87× |
| Darwin arm64 | generic | 10.95 | 11.63 | 0.94× |
| Linux x86_64 | avx2 | 5.05 | 6.68 | 0.76× |
| Linux x86_64 | generic | 13.82 | 17.12 | 0.81× |
| Windows AMD64 | avx2 | 4.88 | 7.34 | 0.66× |
| Windows AMD64 | generic | 23.78 | 10.95 | 2.17× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 96.71 | 109.91 | 0.88× |
| Darwin x86_64 | avx2 | 55.59 | 44.22 | 1.26× |
| Darwin x86_64 | generic | 164.94 | 174.54 | 0.94× |
| Darwin arm64 | generic | 144.17 | 108.50 | 1.33× |
| Linux x86_64 | avx2 | 30.85 | 36.01 | 0.86× |
| Linux x86_64 | generic | 122.82 | 141.75 | 0.87× |
| Windows AMD64 | avx2 | 33.07 | 38.76 | 0.85× |
| Windows AMD64 | generic | 245.83 | 144.59 | 1.70× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.56 | 7.22 | 0.77× |
| Darwin x86_64 | avx2 | 2.60 | 3.28 | 0.79× |
| Darwin x86_64 | generic | 7.08 | 11.57 | 0.61× |
| Darwin arm64 | generic | 5.00 | 5.91 | 0.85× |
| Linux x86_64 | avx2 | 2.09 | 2.64 | 0.79× |
| Linux x86_64 | generic | 7.27 | 9.46 | 0.77× |
| Windows AMD64 | avx2 | 2.10 | 2.70 | 0.78× |
| Windows AMD64 | generic | 6.64 | 8.51 | 0.78× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 105.54 | 104.82 | 1.01× |
| Darwin x86_64 | avx2 | 46.37 | 37.76 | 1.23× |
| Darwin x86_64 | generic | 105.47 | 151.61 | 0.70× |
| Darwin arm64 | generic | 97.83 | 62.18 | 1.57× |
| Linux x86_64 | avx2 | 41.85 | 35.06 | 1.19× |
| Linux x86_64 | generic | 117.87 | 102.68 | 1.15× |
| Windows AMD64 | avx2 | 45.66 | 49.76 | 0.92× |
| Windows AMD64 | generic | 119.53 | 125.99 | 0.95× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 75.93 | 51.28 | 1.48× |
| Darwin x86_64 | avx2 | 46.89 | 22.86 | 2.05× |
| Darwin x86_64 | generic | 106.39 | 81.32 | 1.31× |
| Darwin arm64 | generic | 104.82 | 41.19 | 2.55× |
| Linux x86_64 | avx2 | 31.95 | 17.68 | 1.81× |
| Linux x86_64 | generic | 84.94 | 47.14 | 1.80× |
| Windows AMD64 | avx2 | 33.78 | 17.78 | 1.90× |
| Windows AMD64 | generic | 86.69 | 69.08 | 1.25× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.54 | 34.42 | 0.86× |
| Darwin x86_64 | avx2 | 18.31 | 13.72 | 1.33× |
| Darwin x86_64 | generic | 58.07 | 46.80 | 1.24× |
| Darwin arm64 | generic | 42.20 | 24.22 | 1.74× |
| Linux x86_64 | avx2 | 9.61 | 11.79 | 0.81× |
| Linux x86_64 | generic | 36.02 | 37.63 | 0.96× |
| Windows AMD64 | avx2 | 11.56 | 12.57 | 0.92× |
| Windows AMD64 | generic | 34.83 | 36.23 | 0.96× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 480.16 | 498.81 | 0.96× |
| Darwin x86_64 | avx2 | 163.03 | 156.34 | 1.04× |
| Darwin x86_64 | generic | 372.94 | 487.54 | 0.76× |
| Darwin arm64 | generic | 295.18 | 302.99 | 0.97× |
| Linux x86_64 | avx2 | 192.16 | 192.83 | 1.00× |
| Linux x86_64 | generic | 503.72 | 547.01 | 0.92× |
| Windows AMD64 | avx2 | 199.79 | 207.18 | 0.96× |
| Windows AMD64 | generic | 623.84 | 491.83 | 1.27× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.41 | 3.48 | 0.98× |
| Darwin x86_64 | avx2 | 1.12 | 1.36 | 0.82× |
| Darwin x86_64 | generic | 2.63 | 3.52 | 0.75× |
| Darwin arm64 | generic | 2.56 | 2.89 | 0.89× |
| Linux x86_64 | avx2 | 1.39 | 1.37 | 1.01× |
| Linux x86_64 | generic | 4.03 | 4.20 | 0.96× |
| Windows AMD64 | avx2 | 1.39 | 1.46 | 0.95× |
| Windows AMD64 | generic | 3.14 | 4.04 | 0.78× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 106.33 | 95.15 | 1.12× |
| Darwin x86_64 | avx2 | 42.64 | 41.15 | 1.04× |
| Darwin x86_64 | generic | 122.16 | 126.71 | 0.96× |
| Darwin arm64 | generic | 99.16 | 108.13 | 0.92× |
| Linux x86_64 | avx2 | 34.05 | 30.26 | 1.13× |
| Linux x86_64 | generic | 131.99 | 120.13 | 1.10× |
| Windows AMD64 | avx2 | 35.90 | 32.40 | 1.11× |
| Windows AMD64 | generic | 129.37 | 119.15 | 1.09× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 22.58 | 12.53 | 1.80× |
| Darwin x86_64 | avx2 | 10.45 | 9.70 | 1.08× |
| Darwin x86_64 | generic | 26.48 | 18.78 | 1.41× |
| Darwin arm64 | generic | 18.63 | 13.53 | 1.38× |
| Linux x86_64 | avx2 | 8.83 | 7.65 | 1.15× |
| Linux x86_64 | generic | 24.75 | 16.86 | 1.47× |
| Windows AMD64 | avx2 | 8.11 | 6.62 | 1.23× |
| Windows AMD64 | generic | 24.44 | 17.29 | 1.41× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 35.18 | 30.18 | 1.17× |
| Darwin x86_64 | avx2 | 11.33 | 13.74 | 0.82× |
| Darwin x86_64 | generic | 29.00 | 35.32 | 0.82× |
| Darwin arm64 | generic | 25.83 | 28.31 | 0.91× |
| Linux x86_64 | avx2 | 12.81 | 12.44 | 1.03× |
| Linux x86_64 | generic | 38.06 | 34.82 | 1.09× |
| Windows AMD64 | avx2 | 12.82 | 11.37 | 1.13× |
| Windows AMD64 | generic | 38.06 | 34.69 | 1.10× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 66.83 | 19.01 | 3.52× |
| Darwin x86_64 | avx2 | 75.59 | 8.16 | 9.26× |
| Darwin x86_64 | generic | 169.65 | 17.13 | 9.90× |
| Darwin arm64 | generic | 127.39 | 16.72 | 7.62× |
| Linux x86_64 | avx2 | 28.32 | 3.43 | 8.25× |
| Linux x86_64 | generic | 68.28 | 21.12 | 3.23× |
| Windows AMD64 | avx2 | 26.45 | 7.01 | 3.77× |
| Windows AMD64 | generic | 35.89 | 25.37 | 1.42× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.85 | 6.35 | 0.92× |
| Darwin x86_64 | avx2 | 1.89 | 2.79 | 0.68× |
| Darwin x86_64 | generic | 3.98 | 5.73 | 0.69× |
| Darwin arm64 | generic | 2.76 | 3.86 | 0.72× |
| Linux x86_64 | avx2 | 2.12 | 2.28 | 0.93× |
| Linux x86_64 | generic | 6.66 | 7.34 | 0.91× |
| Windows AMD64 | avx2 | 2.24 | 2.35 | 0.95× |
| Windows AMD64 | generic | 7.24 | 7.05 | 1.03× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 344.52 | 98.26 | 3.51× |
| Darwin x86_64 | avx2 | 167.98 | 40.40 | 4.16× |
| Darwin x86_64 | generic | 388.41 | 100.90 | 3.85× |
| Darwin arm64 | generic | 282.08 | 63.98 | 4.41× |
| Linux x86_64 | avx2 | 126.59 | 44.49 | 2.85× |
| Linux x86_64 | generic | 326.16 | 121.81 | 2.68× |
| Windows AMD64 | avx2 | 120.47 | 44.25 | 2.72× |
| Windows AMD64 | generic | 332.34 | 99.93 | 3.33× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 168.42 | 13.45 | 12.52× |
| Darwin x86_64 | avx2 | 77.59 | 7.55 | 10.28× |
| Darwin x86_64 | generic | 214.19 | 15.95 | 13.43× |
| Darwin arm64 | generic | 137.22 | 10.08 | 13.61× |
| Linux x86_64 | avx2 | 65.02 | 4.93 | 13.18× |
| Linux x86_64 | generic | 176.14 | 16.31 | 10.80× |
| Windows AMD64 | avx2 | 66.71 | 5.79 | 11.53× |
| Windows AMD64 | generic | 109.31 | 14.89 | 7.34× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 72.91 | 68.12 | 1.07× |
| Darwin x86_64 | avx2 | 43.93 | 54.15 | 0.81× |
| Darwin x86_64 | generic | 110.47 | 82.28 | 1.34× |
| Darwin arm64 | generic | 67.20 | 55.50 | 1.21× |
| Linux x86_64 | avx2 | 28.68 | 41.87 | 0.69× |
| Linux x86_64 | generic | 76.21 | 92.08 | 0.83× |
| Windows AMD64 | avx2 | 26.28 | 34.70 | 0.76× |
| Windows AMD64 | generic | 78.59 | 93.39 | 0.84× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 46.56 | 37.46 | 1.24× |
| Darwin x86_64 | avx2 | 18.85 | 41.41 | 0.46× |
| Darwin x86_64 | generic | 47.30 | 55.71 | 0.85× |
| Darwin arm64 | generic | 29.76 | 36.51 | 0.82× |
| Linux x86_64 | avx2 | 20.05 | 21.05 | 0.95× |
| Linux x86_64 | generic | 50.26 | 55.97 | 0.90× |
| Windows AMD64 | avx2 | 16.97 | 18.55 | 0.91× |
| Windows AMD64 | generic | 47.75 | 61.59 | 0.78× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.35 | 30.75 | 0.95× |
| Darwin x86_64 | avx2 | 25.85 | 8.03 | 3.22× |
| Darwin x86_64 | generic | 73.48 | 21.04 | 3.49× |
| Darwin arm64 | generic | 50.66 | 13.49 | 3.75× |
| Linux x86_64 | avx2 | 8.77 | 7.92 | 1.11× |
| Linux x86_64 | generic | 27.44 | 38.76 | 0.71× |
| Windows AMD64 | avx2 | 8.78 | 7.49 | 1.17× |
| Windows AMD64 | generic | 113.76 | 26.52 | 4.29× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 119.40 | 46.09 | 2.59× |
| Darwin x86_64 | avx2 | 54.59 | 22.54 | 2.42× |
| Darwin x86_64 | generic | 175.02 | 70.80 | 2.47× |
| Darwin arm64 | generic | 188.81 | 55.51 | 3.40× |
| Linux x86_64 | avx2 | 38.74 | 18.51 | 2.09× |
| Linux x86_64 | generic | 145.32 | 61.78 | 2.35× |
| Windows AMD64 | avx2 | 42.18 | 18.39 | 2.29× |
| Windows AMD64 | generic | 151.77 | 64.12 | 2.37× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.77 | 5.99 | 0.96× |
| Darwin x86_64 | avx2 | 2.86 | 3.10 | 0.92× |
| Darwin x86_64 | generic | 7.63 | 8.65 | 0.88× |
| Darwin arm64 | generic | 7.62 | 7.15 | 1.07× |
| Linux x86_64 | avx2 | 1.83 | 1.91 | 0.96× |
| Linux x86_64 | generic | 7.05 | 7.76 | 0.91× |
| Windows AMD64 | avx2 | 2.10 | 2.19 | 0.96× |
| Windows AMD64 | generic | 5.44 | 5.34 | 1.02× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.15 | 43.66 | 0.92× |
| Darwin x86_64 | avx2 | 16.78 | 20.95 | 0.80× |
| Darwin x86_64 | generic | 38.79 | 45.31 | 0.86× |
| Darwin arm64 | generic | 27.15 | 34.66 | 0.78× |
| Linux x86_64 | avx2 | 13.85 | 13.02 | 1.06× |
| Linux x86_64 | generic | 39.80 | 46.24 | 0.86× |
| Windows AMD64 | avx2 | 15.54 | 15.28 | 1.02× |
| Windows AMD64 | generic | 45.05 | 83.68 | 0.54× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 49.14 | 137.55 | 0.36× |
| Darwin x86_64 | avx2 | — | 31.95 | — |
| Darwin x86_64 | generic | — | 67.32 | — |
| Darwin arm64 | generic | — | 54.31 | — |
| Linux x86_64 | avx2 | 19.58 | 62.50 | 0.31× |
| Linux x86_64 | generic | 51.16 | 148.37 | 0.34× |
| Windows AMD64 | avx2 | 20.56 | 59.67 | 0.34× |
| Windows AMD64 | generic | 54.94 | 172.45 | 0.32× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.28 | 19.33 | 1.93× |
| Darwin x86_64 | avx2 | 69.36 | 28.52 | 2.43× |
| Darwin x86_64 | generic | 152.67 | 29.68 | 5.14× |
| Darwin arm64 | generic | 122.84 | 23.58 | 5.21× |
| Linux x86_64 | avx2 | 14.59 | 28.11 | 0.52× |
| Linux x86_64 | generic | 38.91 | 64.78 | 0.60× |
| Windows AMD64 | avx2 | 14.96 | 27.18 | 0.55× |
| Windows AMD64 | generic | 41.70 | 76.80 | 0.54× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 62.87 | 121.57 | 0.52× |
| Darwin x86_64 | avx2 | 34.44 | 245.24 | 0.14× |
| Darwin x86_64 | generic | 68.12 | 209.25 | 0.33× |
| Darwin arm64 | generic | 36.09 | 100.78 | 0.36× |
| Linux x86_64 | avx2 | 27.52 | 108.27 | 0.25× |
| Linux x86_64 | generic | 60.62 | 201.54 | 0.30× |
| Windows AMD64 | avx2 | 19.84 | 114.25 | 0.17× |
| Windows AMD64 | generic | 51.21 | 226.43 | 0.23× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.44 | 19.87 | 0.93× |
| Darwin x86_64 | avx2 | 8.67 | 13.05 | 0.66× |
| Darwin x86_64 | generic | 27.10 | 40.54 | 0.67× |
| Darwin arm64 | generic | 20.47 | 31.84 | 0.64× |
| Linux x86_64 | avx2 | 8.19 | 7.62 | 1.07× |
| Linux x86_64 | generic | 31.23 | 29.53 | 1.06× |
| Windows AMD64 | avx2 | 9.67 | 8.95 | 1.08× |
| Windows AMD64 | generic | 32.06 | 29.59 | 1.08× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 174.29 | 134.85 | 1.29× |
| Darwin x86_64 | avx2 | 58.34 | 64.11 | 0.91× |
| Darwin x86_64 | generic | 146.32 | 152.44 | 0.96× |
| Darwin arm64 | generic | 123.09 | 113.19 | 1.09× |
| Linux x86_64 | avx2 | 61.27 | 57.48 | 1.07× |
| Linux x86_64 | generic | 171.31 | 159.94 | 1.07× |
| Windows AMD64 | avx2 | 61.15 | 58.80 | 1.04× |
| Windows AMD64 | generic | 178.35 | 166.38 | 1.07× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 158.40 | 193.40 | 0.82× |
| Darwin x86_64 | avx2 | 59.62 | 144.88 | 0.41× |
| Darwin x86_64 | generic | 149.61 | 514.10 | 0.29× |
| Darwin arm64 | generic | 112.87 | 438.23 | 0.26× |
| Linux x86_64 | avx2 | 54.74 | 90.26 | 0.61× |
| Linux x86_64 | generic | 164.80 | 321.39 | 0.51× |
| Windows AMD64 | avx2 | 52.67 | 81.01 | 0.65× |
| Windows AMD64 | generic | 279.39 | 483.24 | 0.58× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 38.05 | 38.98 | 0.98× |
| Darwin x86_64 | avx2 | 23.47 | 22.32 | 1.05× |
| Darwin x86_64 | generic | 113.67 | 114.32 | 0.99× |
| Darwin arm64 | generic | 71.13 | 70.70 | 1.01× |
| Linux x86_64 | avx2 | 17.27 | 17.70 | 0.98× |
| Linux x86_64 | generic | 40.63 | 43.17 | 0.94× |
| Windows AMD64 | avx2 | 18.17 | 19.17 | 0.95× |
| Windows AMD64 | generic | 89.07 | 92.54 | 0.96× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.64 | 141.29 | 0.97× |
| Darwin x86_64 | avx2 | 65.32 | 73.21 | 0.89× |
| Darwin x86_64 | generic | 166.80 | 191.76 | 0.87× |
| Darwin arm64 | generic | 127.38 | 144.90 | 0.88× |
| Linux x86_64 | avx2 | 55.33 | 70.02 | 0.79× |
| Linux x86_64 | generic | 144.85 | 151.13 | 0.96× |
| Windows AMD64 | avx2 | 57.39 | 59.11 | 0.97× |
| Windows AMD64 | generic | 134.27 | 345.51 | 0.39× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 92.59 | 39.12 | 2.37× |
| Darwin x86_64 | avx2 | 129.75 | 19.94 | 6.51× |
| Darwin x86_64 | generic | 245.17 | 50.37 | 4.87× |
| Darwin arm64 | generic | 206.47 | 48.29 | 4.28× |
| Linux x86_64 | avx2 | 29.90 | 25.99 | 1.15× |
| Linux x86_64 | generic | 96.77 | 50.48 | 1.92× |
| Windows AMD64 | avx2 | 38.17 | 17.17 | 2.22× |
| Windows AMD64 | generic | 105.29 | 46.66 | 2.26× |


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


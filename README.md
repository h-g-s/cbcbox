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

The AVX2/Haswell build is **~2.8×** faster than the generic build on average (geometric mean across 30 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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
| Linux aarch64 | 52.41 | — | — |
| Darwin x86_64 | 71.42 | 26.71 | 2.67× |
| Darwin arm64 | 51.55 | — | — |
| Linux x86_64 | 58.43 | 19.87 | 2.94× |
| Windows AMD64 | 65.02 | 19.87 | 3.27× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 41.78 | — | — |
| Darwin x86_64 | 59.76 | 21.57 | 2.77× |
| Darwin arm64 | 39.36 | — | — |
| Linux x86_64 | 52.20 | 17.70 | 2.95× |
| Windows AMD64 | 55.10 | 17.55 | 3.14× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 12.57 | 9.93 | 1.27× |
| Darwin x86_64 | avx2 | 6.31 | 9.63 | 0.65× |
| Darwin x86_64 | generic | 18.22 | 15.01 | 1.21× |
| Darwin arm64 | generic | 10.87 | 8.54 | 1.27× |
| Linux x86_64 | avx2 | 5.14 | 5.64 | 0.91× |
| Linux x86_64 | generic | 14.06 | 20.75 | 0.68× |
| Windows AMD64 | avx2 | 4.85 | 8.42 | 0.58× |
| Windows AMD64 | generic | 13.26 | 12.90 | 1.03× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 99.45 | 101.76 | 0.98× |
| Darwin x86_64 | avx2 | 49.14 | 43.23 | 1.14× |
| Darwin x86_64 | generic | 235.01 | 128.80 | 1.82× |
| Darwin arm64 | generic | 125.91 | 111.67 | 1.13× |
| Linux x86_64 | avx2 | 32.49 | 32.62 | 1.00× |
| Linux x86_64 | generic | 126.62 | 129.06 | 0.98× |
| Windows AMD64 | avx2 | 33.79 | 49.72 | 0.68× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.58 | 7.25 | 0.77× |
| Darwin x86_64 | avx2 | 2.23 | 3.13 | 0.71× |
| Darwin x86_64 | generic | 8.48 | 9.47 | 0.90× |
| Darwin arm64 | generic | 4.72 | 6.22 | 0.76× |
| Linux x86_64 | avx2 | 2.15 | 2.61 | 0.82× |
| Linux x86_64 | generic | 7.18 | 9.22 | 0.78× |
| Windows AMD64 | avx2 | 1.98 | 3.03 | 0.65× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 126.89 | 80.93 | 1.57× |
| Darwin x86_64 | avx2 | 48.00 | 49.13 | 0.98× |
| Darwin x86_64 | generic | 174.14 | 150.12 | 1.16× |
| Darwin arm64 | generic | 96.72 | 102.90 | 0.94× |
| Linux x86_64 | avx2 | 50.86 | 32.94 | 1.54× |
| Linux x86_64 | generic | 144.56 | 103.43 | 1.40× |
| Windows AMD64 | avx2 | 55.73 | 36.37 | 1.53× |
| Windows AMD64 | generic | 144.92 | — | — |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 59.71 | 47.67 | 1.25× |
| Darwin x86_64 | avx2 | 47.22 | 20.83 | 2.27× |
| Darwin x86_64 | generic | 138.21 | 60.57 | 2.28× |
| Darwin arm64 | generic | 92.80 | 52.31 | 1.77× |
| Linux x86_64 | avx2 | 25.12 | 18.81 | 1.34× |
| Linux x86_64 | generic | 68.67 | 60.39 | 1.14× |
| Windows AMD64 | avx2 | 26.74 | 22.48 | 1.19× |
| Windows AMD64 | generic | 68.74 | 56.95 | 1.21× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.62 | 34.97 | 0.85× |
| Darwin x86_64 | avx2 | 16.11 | 13.81 | 1.17× |
| Darwin x86_64 | generic | 63.92 | 45.04 | 1.42× |
| Darwin arm64 | generic | 37.38 | 31.83 | 1.17× |
| Linux x86_64 | avx2 | 9.83 | 11.84 | 0.83× |
| Linux x86_64 | generic | 36.25 | 37.51 | 0.97× |
| Windows AMD64 | avx2 | 11.36 | 12.08 | 0.94× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 478.46 | 457.96 | 1.04× |
| Darwin x86_64 | avx2 | 144.30 | 145.74 | 0.99× |
| Darwin x86_64 | generic | 444.68 | 428.58 | 1.04× |
| Darwin arm64 | generic | 307.57 | 309.07 | 1.00× |
| Linux x86_64 | avx2 | 192.49 | 195.61 | 0.98× |
| Linux x86_64 | generic | 502.73 | 535.51 | 0.94× |
| Windows AMD64 | avx2 | 196.49 | 192.97 | 1.02× |
| Windows AMD64 | generic | 618.48 | 483.30 | 1.28× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.43 | 3.53 | 0.97× |
| Darwin x86_64 | avx2 | 0.95 | 1.32 | 0.72× |
| Darwin x86_64 | generic | 2.96 | 4.53 | 0.65× |
| Darwin arm64 | generic | 1.94 | 3.03 | 0.64× |
| Linux x86_64 | avx2 | 1.40 | 1.42 | 0.99× |
| Linux x86_64 | generic | 4.03 | 4.24 | 0.95× |
| Windows AMD64 | avx2 | 1.75 | 1.36 | 1.28× |
| Windows AMD64 | generic | 3.17 | 3.95 | 0.80× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 93.84 | 110.30 | 0.85× |
| Darwin x86_64 | avx2 | 37.85 | 48.96 | 0.77× |
| Darwin x86_64 | generic | 141.78 | 184.83 | 0.77× |
| Darwin arm64 | generic | 97.14 | 145.64 | 0.67× |
| Linux x86_64 | avx2 | 30.34 | 35.17 | 0.86× |
| Linux x86_64 | generic | 118.98 | 138.53 | 0.86× |
| Windows AMD64 | avx2 | 33.15 | 36.30 | 0.91× |
| Windows AMD64 | generic | — | 131.36 | — |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.11 | 13.18 | 1.75× |
| Darwin x86_64 | avx2 | 13.87 | 8.86 | 1.57× |
| Darwin x86_64 | generic | 28.78 | 25.27 | 1.14× |
| Darwin arm64 | generic | 17.94 | 13.24 | 1.35× |
| Linux x86_64 | avx2 | 9.00 | 7.58 | 1.19× |
| Linux x86_64 | generic | 25.45 | 17.85 | 1.43× |
| Windows AMD64 | avx2 | 8.68 | 7.39 | 1.17× |
| Windows AMD64 | generic | 25.82 | 16.72 | 1.54× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.11 | 45.93 | 1.03× |
| Darwin x86_64 | avx2 | 19.21 | 21.94 | 0.88× |
| Darwin x86_64 | generic | 38.67 | 77.07 | 0.50× |
| Darwin arm64 | generic | 25.97 | 55.12 | 0.47× |
| Linux x86_64 | avx2 | 17.45 | 14.12 | 1.24× |
| Linux x86_64 | generic | 52.03 | 51.84 | 1.00× |
| Windows AMD64 | avx2 | 17.77 | 16.38 | 1.08× |
| Windows AMD64 | generic | 57.63 | 53.15 | 1.08× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 66.47 | 14.13 | 4.70× |
| Darwin x86_64 | avx2 | 87.42 | 10.14 | 8.62× |
| Darwin x86_64 | generic | 199.16 | 32.24 | 6.18× |
| Darwin arm64 | generic | 142.04 | 15.86 | 8.96× |
| Linux x86_64 | avx2 | 28.31 | 3.61 | 7.84× |
| Linux x86_64 | generic | 68.66 | 16.05 | 4.28× |
| Windows AMD64 | avx2 | 25.94 | 12.19 | 2.13× |
| Windows AMD64 | generic | 37.01 | 35.39 | 1.05× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.84 | 6.13 | 0.95× |
| Darwin x86_64 | avx2 | 1.73 | 4.36 | 0.40× |
| Darwin x86_64 | generic | 3.07 | 11.04 | 0.28× |
| Darwin arm64 | generic | 2.33 | 6.91 | 0.34× |
| Linux x86_64 | avx2 | 2.19 | 2.39 | 0.92× |
| Linux x86_64 | generic | 6.69 | 7.25 | 0.92× |
| Windows AMD64 | avx2 | 2.13 | 2.33 | 0.92× |
| Windows AMD64 | generic | 7.26 | 6.89 | 1.05× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 344.79 | 96.09 | 3.59× |
| Darwin x86_64 | avx2 | 184.96 | 60.13 | 3.08× |
| Darwin x86_64 | generic | 506.38 | 187.97 | 2.69× |
| Darwin arm64 | generic | 310.37 | 74.50 | 4.17× |
| Linux x86_64 | avx2 | 126.82 | 45.42 | 2.79× |
| Linux x86_64 | generic | 325.92 | 139.22 | 2.34× |
| Windows AMD64 | avx2 | 118.70 | 50.01 | 2.37× |
| Windows AMD64 | generic | 348.88 | 98.13 | 3.56× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 168.73 | 13.46 | 12.54× |
| Darwin x86_64 | avx2 | 85.78 | 9.01 | 9.52× |
| Darwin x86_64 | generic | 194.77 | 19.98 | 9.75× |
| Darwin arm64 | generic | 139.40 | 20.35 | 6.85× |
| Linux x86_64 | avx2 | 65.33 | 5.93 | 11.02× |
| Linux x86_64 | generic | 176.51 | 16.12 | 10.95× |
| Windows AMD64 | avx2 | 65.30 | 4.96 | 13.17× |
| Windows AMD64 | generic | 107.96 | 14.70 | 7.35× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 73.22 | 65.01 | 1.13× |
| Darwin x86_64 | avx2 | 56.11 | 45.01 | 1.25× |
| Darwin x86_64 | generic | 97.36 | 104.83 | 0.93× |
| Darwin arm64 | generic | 73.56 | 57.10 | 1.29× |
| Linux x86_64 | avx2 | 29.09 | 37.90 | 0.77× |
| Linux x86_64 | generic | 77.52 | 88.16 | 0.88× |
| Windows AMD64 | avx2 | 26.39 | 34.26 | 0.77× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 45.58 | 43.80 | 1.04× |
| Darwin x86_64 | avx2 | 20.73 | 40.82 | 0.51× |
| Darwin x86_64 | generic | 43.37 | 70.20 | 0.62× |
| Darwin arm64 | generic | 43.35 | 44.17 | 0.98× |
| Linux x86_64 | avx2 | 20.03 | 24.61 | 0.81× |
| Linux x86_64 | generic | 50.38 | 49.48 | 1.02× |
| Windows AMD64 | avx2 | 16.66 | 24.47 | 0.68× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.10 | 29.71 | 0.98× |
| Darwin x86_64 | avx2 | 26.21 | 7.05 | 3.71× |
| Darwin x86_64 | generic | 68.29 | 23.16 | 2.95× |
| Darwin arm64 | generic | 63.31 | 14.39 | 4.40× |
| Linux x86_64 | avx2 | 8.66 | 7.96 | 1.09× |
| Linux x86_64 | generic | 27.40 | 36.32 | 0.75× |
| Windows AMD64 | avx2 | 8.44 | 6.67 | 1.27× |
| Windows AMD64 | generic | 118.64 | 29.77 | 3.99× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 133.24 | 47.82 | 2.79× |
| Darwin x86_64 | avx2 | 45.99 | 19.78 | 2.32× |
| Darwin x86_64 | generic | 145.72 | 85.25 | 1.71× |
| Darwin arm64 | generic | 133.42 | 55.51 | 2.40× |
| Linux x86_64 | avx2 | 45.55 | 22.80 | 2.00× |
| Linux x86_64 | generic | 168.47 | 61.35 | 2.75× |
| Windows AMD64 | avx2 | 48.87 | 18.46 | 2.65× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.82 | 5.91 | 0.99× |
| Darwin x86_64 | avx2 | 2.73 | 2.87 | 0.95× |
| Darwin x86_64 | generic | 7.08 | 9.75 | 0.73× |
| Darwin arm64 | generic | 6.08 | 6.43 | 0.95× |
| Linux x86_64 | avx2 | 1.88 | 1.91 | 0.98× |
| Linux x86_64 | generic | 6.97 | 7.46 | 0.93× |
| Windows AMD64 | avx2 | 2.00 | 0.69 | 2.87× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.39 | 43.81 | 0.92× |
| Darwin x86_64 | avx2 | 19.04 | 16.68 | 1.14× |
| Darwin x86_64 | generic | 36.41 | 52.24 | 0.70× |
| Darwin arm64 | generic | 27.00 | 32.29 | 0.84× |
| Linux x86_64 | avx2 | 13.99 | 13.26 | 1.06× |
| Linux x86_64 | generic | 40.08 | 46.41 | 0.86× |
| Windows AMD64 | avx2 | 14.86 | 14.62 | 1.02× |
| Windows AMD64 | generic | 42.94 | 55.18 | 0.78× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 49.50 | 141.21 | 0.35× |
| Darwin x86_64 | avx2 | — | 29.76 | — |
| Darwin x86_64 | generic | — | 77.51 | — |
| Darwin arm64 | generic | — | 50.45 | — |
| Linux x86_64 | avx2 | 19.73 | 63.13 | 0.31× |
| Linux x86_64 | generic | 51.69 | 149.16 | 0.35× |
| Windows AMD64 | avx2 | 20.08 | 58.49 | 0.34× |
| Windows AMD64 | generic | 52.82 | 150.41 | 0.35× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 36.12 | 21.78 | 1.66× |
| Darwin x86_64 | avx2 | 45.99 | 15.09 | 3.05× |
| Darwin x86_64 | generic | 100.73 | 31.35 | 3.21× |
| Darwin arm64 | generic | 87.63 | 15.39 | 5.69× |
| Linux x86_64 | avx2 | 14.13 | 36.51 | 0.39× |
| Linux x86_64 | generic | 37.76 | 67.25 | 0.56× |
| Windows AMD64 | avx2 | 14.29 | 15.03 | 0.95× |
| Windows AMD64 | generic | 39.52 | 93.31 | 0.42× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 61.30 | 117.20 | 0.52× |
| Darwin x86_64 | avx2 | 28.50 | 154.10 | 0.18× |
| Darwin x86_64 | generic | 61.84 | 286.75 | 0.22× |
| Darwin arm64 | generic | 34.40 | 121.14 | 0.28× |
| Linux x86_64 | avx2 | 27.02 | 140.35 | 0.19× |
| Linux x86_64 | generic | 61.28 | 187.45 | 0.33× |
| Windows AMD64 | avx2 | 19.52 | 131.17 | 0.15× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.46 | 19.87 | 0.93× |
| Darwin x86_64 | avx2 | 7.24 | 9.96 | 0.73× |
| Darwin x86_64 | generic | 24.77 | 45.40 | 0.55× |
| Darwin arm64 | generic | 21.39 | 30.50 | 0.70× |
| Linux x86_64 | avx2 | 8.00 | 7.77 | 1.03× |
| Linux x86_64 | generic | 31.24 | 29.79 | 1.05× |
| Windows AMD64 | avx2 | 8.96 | 8.71 | 1.03× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 172.81 | 134.57 | 1.28× |
| Darwin x86_64 | avx2 | 50.91 | 55.16 | 0.92× |
| Darwin x86_64 | generic | 135.70 | 169.91 | 0.80× |
| Darwin arm64 | generic | 125.16 | 114.18 | 1.10× |
| Linux x86_64 | avx2 | 61.48 | 59.19 | 1.04× |
| Linux x86_64 | generic | 172.41 | 156.31 | 1.10× |
| Windows AMD64 | avx2 | 60.19 | 58.35 | 1.03× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 510.72 | 439.12 | 1.16× |
| Darwin x86_64 | avx2 | 228.63 | 340.08 | 0.67× |
| Darwin x86_64 | generic | 573.57 | 594.86 | 0.96× |
| Darwin arm64 | generic | 462.42 | 501.89 | 0.92× |
| Linux x86_64 | avx2 | 180.78 | 93.21 | 1.94× |
| Linux x86_64 | generic | 527.24 | 562.78 | 0.94× |
| Windows AMD64 | avx2 | 167.79 | 92.31 | 1.82× |
| Windows AMD64 | generic | 493.57 | 1178.26 | 0.42× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 68.90 | 56.16 | 1.23× |
| Darwin x86_64 | avx2 | 44.51 | 35.31 | 1.26× |
| Darwin x86_64 | generic | 112.23 | 69.32 | 1.62× |
| Darwin arm64 | generic | 78.62 | 51.91 | 1.51× |
| Linux x86_64 | avx2 | 30.64 | 26.91 | 1.14× |
| Linux x86_64 | generic | 74.87 | 61.35 | 1.22× |
| Windows AMD64 | avx2 | 28.27 | 24.56 | 1.15× |
| Windows AMD64 | generic | 72.91 | 65.32 | 1.12× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.52 | 140.60 | 0.97× |
| Darwin x86_64 | avx2 | 57.70 | 86.38 | 0.67× |
| Darwin x86_64 | generic | 156.97 | 205.81 | 0.76× |
| Darwin arm64 | generic | 129.51 | 164.42 | 0.79× |
| Linux x86_64 | avx2 | 55.27 | 57.85 | 0.96× |
| Linux x86_64 | generic | 145.19 | 151.32 | 0.96× |
| Windows AMD64 | avx2 | 56.08 | 57.97 | 0.97× |
| Windows AMD64 | generic | 132.01 | 139.99 | 0.94× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 126.20 | 101.78 | 1.24× |
| Darwin x86_64 | avx2 | 135.59 | 26.34 | 5.15× |
| Darwin x86_64 | generic | 359.28 | 82.93 | 4.33× |
| Darwin arm64 | generic | 320.14 | 72.08 | 4.44× |
| Linux x86_64 | avx2 | 43.66 | 34.76 | 1.26× |
| Linux x86_64 | generic | 137.98 | 50.00 | 2.76× |
| Windows AMD64 | avx2 | 49.44 | 26.00 | 1.90× |
| Windows AMD64 | generic | 142.19 | 84.30 | 1.69× |


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


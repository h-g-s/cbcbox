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
| Linux aarch64 | 53.63 | — | — |
| Darwin x86_64 | 72.26 | 26.28 | 2.75× |
| Darwin arm64 | 51.15 | — | — |
| Linux x86_64 | 59.47 | 19.42 | 3.06× |
| Windows AMD64 | 75.98 | 24.77 | 3.07× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 43.20 | — | — |
| Darwin x86_64 | 61.44 | 26.92 | 2.28× |
| Darwin arm64 | 36.03 | — | — |
| Linux x86_64 | 51.04 | 17.97 | 2.84× |
| Windows AMD64 | 61.32 | 20.70 | 2.96× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 12.92 | 14.41 | 0.90× |
| Darwin x86_64 | avx2 | 5.96 | 8.06 | 0.74× |
| Darwin x86_64 | generic | 18.64 | 21.26 | 0.88× |
| Darwin arm64 | generic | 12.22 | 9.03 | 1.35× |
| Linux x86_64 | avx2 | 4.78 | 5.16 | 0.93× |
| Linux x86_64 | generic | 14.40 | 15.28 | 0.94× |
| Windows AMD64 | avx2 | 6.23 | 6.48 | 0.96× |
| Windows AMD64 | generic | 15.56 | 12.69 | 1.23× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 101.00 | 102.36 | 0.99× |
| Darwin x86_64 | avx2 | 51.33 | 52.48 | 0.98× |
| Darwin x86_64 | generic | 184.04 | 142.51 | 1.29× |
| Darwin arm64 | generic | 139.65 | 106.41 | 1.31× |
| Linux x86_64 | avx2 | 31.91 | 32.28 | 0.99× |
| Linux x86_64 | generic | 116.83 | 119.74 | 0.98× |
| Windows AMD64 | avx2 | 42.24 | 42.41 | 1.00× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.63 | 7.22 | 0.78× |
| Darwin x86_64 | avx2 | 2.38 | 3.90 | 0.61× |
| Darwin x86_64 | generic | 9.16 | 10.30 | 0.89× |
| Darwin arm64 | generic | 6.09 | 5.90 | 1.03× |
| Linux x86_64 | avx2 | 1.92 | 2.45 | 0.78× |
| Linux x86_64 | generic | 6.54 | 8.32 | 0.79× |
| Windows AMD64 | avx2 | 2.61 | 3.37 | 0.77× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 128.65 | 81.79 | 1.57× |
| Darwin x86_64 | avx2 | 50.81 | 55.58 | 0.91× |
| Darwin x86_64 | generic | 151.60 | 137.20 | 1.10× |
| Darwin arm64 | generic | 102.18 | 83.86 | 1.22× |
| Linux x86_64 | avx2 | 48.68 | 33.25 | 1.46× |
| Linux x86_64 | generic | 145.30 | 101.48 | 1.43× |
| Windows AMD64 | avx2 | 71.03 | 48.19 | 1.47× |
| Windows AMD64 | generic | 171.62 | — | — |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 60.50 | 51.27 | 1.18× |
| Darwin x86_64 | avx2 | 50.37 | 26.27 | 1.92× |
| Darwin x86_64 | generic | 139.93 | 61.44 | 2.28× |
| Darwin arm64 | generic | 94.90 | 38.20 | 2.48× |
| Linux x86_64 | avx2 | 23.76 | 18.36 | 1.29× |
| Linux x86_64 | generic | 70.06 | 75.40 | 0.93× |
| Windows AMD64 | avx2 | 34.37 | 26.79 | 1.28× |
| Windows AMD64 | generic | 82.08 | 73.10 | 1.12× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.01 | 35.10 | 0.86× |
| Darwin x86_64 | avx2 | 17.59 | 14.69 | 1.20× |
| Darwin x86_64 | generic | 64.36 | 45.07 | 1.43× |
| Darwin arm64 | generic | 37.04 | 24.35 | 1.52× |
| Linux x86_64 | avx2 | 9.39 | 10.18 | 0.92× |
| Linux x86_64 | generic | 34.13 | 35.42 | 0.96× |
| Windows AMD64 | avx2 | 14.88 | 15.76 | 0.94× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 496.24 | 473.79 | 1.05× |
| Darwin x86_64 | avx2 | 160.44 | 185.85 | 0.86× |
| Darwin x86_64 | generic | 433.92 | 435.51 | 1.00× |
| Darwin arm64 | generic | 289.18 | 274.57 | 1.05× |
| Linux x86_64 | avx2 | 191.99 | 205.12 | 0.94× |
| Linux x86_64 | generic | 524.71 | 560.43 | 0.94× |
| Windows AMD64 | avx2 | 252.98 | 238.69 | 1.06× |
| Windows AMD64 | generic | 773.02 | 582.11 | 1.33× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.46 | 3.55 | 0.97× |
| Darwin x86_64 | avx2 | 1.07 | 2.06 | 0.52× |
| Darwin x86_64 | generic | 2.61 | 3.85 | 0.68× |
| Darwin arm64 | generic | 2.10 | 2.39 | 0.88× |
| Linux x86_64 | avx2 | 1.35 | 1.32 | 1.02× |
| Linux x86_64 | generic | 3.99 | 4.14 | 0.96× |
| Windows AMD64 | avx2 | 1.75 | 1.75 | 1.00× |
| Windows AMD64 | generic | 3.70 | 4.63 | 0.80× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 94.85 | 111.61 | 0.85× |
| Darwin x86_64 | avx2 | 39.82 | 68.19 | 0.58× |
| Darwin x86_64 | generic | 113.50 | 160.34 | 0.71× |
| Darwin arm64 | generic | 96.12 | 117.44 | 0.82× |
| Linux x86_64 | avx2 | 30.12 | 35.10 | 0.86× |
| Linux x86_64 | generic | 110.18 | 127.88 | 0.86× |
| Windows AMD64 | avx2 | 39.34 | 45.28 | 0.87× |
| Windows AMD64 | generic | — | 159.94 | — |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.40 | 13.28 | 1.76× |
| Darwin x86_64 | avx2 | 9.61 | 12.41 | 0.77× |
| Darwin x86_64 | generic | 26.17 | 19.87 | 1.32× |
| Darwin arm64 | generic | 18.29 | 15.04 | 1.22× |
| Linux x86_64 | avx2 | 8.63 | 7.58 | 1.14× |
| Linux x86_64 | generic | 26.06 | 17.78 | 1.47× |
| Windows AMD64 | avx2 | 10.28 | 7.88 | 1.30× |
| Windows AMD64 | generic | 29.75 | 18.69 | 1.59× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.78 | 46.70 | 1.02× |
| Darwin x86_64 | avx2 | 13.34 | 30.89 | 0.43× |
| Darwin x86_64 | generic | 32.72 | 67.91 | 0.48× |
| Darwin arm64 | generic | 25.91 | 49.19 | 0.53× |
| Linux x86_64 | avx2 | 17.66 | 14.33 | 1.23× |
| Linux x86_64 | generic | 52.35 | 51.41 | 1.02× |
| Windows AMD64 | avx2 | 21.41 | 20.84 | 1.03× |
| Windows AMD64 | generic | 61.79 | 61.96 | 1.00× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 67.79 | 25.45 | 2.66× |
| Darwin x86_64 | avx2 | 72.17 | 15.25 | 4.73× |
| Darwin x86_64 | generic | 168.55 | 33.40 | 5.05× |
| Darwin arm64 | generic | 133.21 | 15.39 | 8.66× |
| Linux x86_64 | avx2 | 26.37 | 5.13 | 5.14× |
| Linux x86_64 | generic | 72.89 | 22.23 | 3.28× |
| Windows AMD64 | avx2 | 33.83 | 6.15 | 5.50× |
| Windows AMD64 | generic | 41.11 | 29.19 | 1.41× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.90 | 6.33 | 0.93× |
| Darwin x86_64 | avx2 | 1.31 | 6.01 | 0.22× |
| Darwin x86_64 | generic | 3.00 | 10.09 | 0.30× |
| Darwin arm64 | generic | 2.31 | 5.65 | 0.41× |
| Linux x86_64 | avx2 | 2.09 | 2.23 | 0.94× |
| Linux x86_64 | generic | 6.71 | 7.23 | 0.93× |
| Windows AMD64 | avx2 | 2.81 | 2.86 | 0.98× |
| Windows AMD64 | generic | 8.54 | 8.00 | 1.07× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 352.23 | 95.91 | 3.67× |
| Darwin x86_64 | avx2 | 163.21 | 51.63 | 3.16× |
| Darwin x86_64 | generic | 480.35 | 99.82 | 4.81× |
| Darwin arm64 | generic | 284.69 | 62.06 | 4.59× |
| Linux x86_64 | avx2 | 123.77 | 52.38 | 2.36× |
| Linux x86_64 | generic | 375.63 | 136.60 | 2.75× |
| Windows AMD64 | avx2 | 145.73 | 51.63 | 2.82× |
| Windows AMD64 | generic | 356.13 | 107.58 | 3.31× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 173.69 | 15.34 | 11.32× |
| Darwin x86_64 | avx2 | 76.24 | 9.22 | 8.27× |
| Darwin x86_64 | generic | 220.02 | 18.04 | 12.20× |
| Darwin arm64 | generic | 141.51 | 13.12 | 10.79× |
| Linux x86_64 | avx2 | 62.84 | 4.97 | 12.64× |
| Linux x86_64 | generic | 187.61 | 15.77 | 11.90× |
| Windows AMD64 | avx2 | 82.00 | 6.49 | 12.63× |
| Windows AMD64 | generic | 123.97 | 17.40 | 7.13× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 75.39 | 60.79 | 1.24× |
| Darwin x86_64 | avx2 | 42.05 | 63.80 | 0.66× |
| Darwin x86_64 | generic | 129.58 | 87.60 | 1.48× |
| Darwin arm64 | generic | 73.09 | 52.84 | 1.38× |
| Linux x86_64 | avx2 | 28.05 | 40.61 | 0.69× |
| Linux x86_64 | generic | 84.10 | 88.69 | 0.95× |
| Windows AMD64 | avx2 | 33.01 | 41.39 | 0.80× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.30 | 40.45 | 1.17× |
| Darwin x86_64 | avx2 | 18.78 | 52.28 | 0.36× |
| Darwin x86_64 | generic | 52.81 | 73.30 | 0.72× |
| Darwin arm64 | generic | 36.89 | 36.99 | 1.00× |
| Linux x86_64 | avx2 | 19.95 | 29.57 | 0.67× |
| Linux x86_64 | generic | 53.24 | 55.96 | 0.95× |
| Windows AMD64 | avx2 | 20.39 | 33.42 | 0.61× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.02 | 31.45 | 0.95× |
| Darwin x86_64 | avx2 | 25.94 | 8.05 | 3.22× |
| Darwin x86_64 | generic | 77.02 | 23.33 | 3.30× |
| Darwin arm64 | generic | 49.36 | 14.13 | 3.49× |
| Linux x86_64 | avx2 | 8.54 | 11.07 | 0.77× |
| Linux x86_64 | generic | 29.73 | 41.30 | 0.72× |
| Windows AMD64 | avx2 | 10.08 | 9.32 | 1.08× |
| Windows AMD64 | generic | 136.75 | 33.18 | 4.12× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 142.91 | 53.93 | 2.65× |
| Darwin x86_64 | avx2 | 45.75 | 24.69 | 1.85× |
| Darwin x86_64 | generic | 161.32 | 86.20 | 1.87× |
| Darwin arm64 | generic | 131.25 | 71.82 | 1.83× |
| Linux x86_64 | avx2 | 48.68 | 21.36 | 2.28× |
| Linux x86_64 | generic | 170.43 | 73.19 | 2.33× |
| Windows AMD64 | avx2 | 63.85 | 25.83 | 2.47× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.94 | 6.00 | 0.99× |
| Darwin x86_64 | avx2 | 2.70 | 3.22 | 0.84× |
| Darwin x86_64 | generic | 7.54 | 9.59 | 0.79× |
| Darwin arm64 | generic | 5.19 | 6.57 | 0.79× |
| Linux x86_64 | avx2 | 1.83 | 1.87 | 0.98× |
| Linux x86_64 | generic | 6.88 | 2.09 | 3.29× |
| Windows AMD64 | avx2 | 2.53 | 0.89 | 2.86× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 41.08 | 43.76 | 0.94× |
| Darwin x86_64 | avx2 | 17.05 | 18.79 | 0.91× |
| Darwin x86_64 | generic | 37.63 | 50.15 | 0.75× |
| Darwin arm64 | generic | 23.21 | 37.93 | 0.61× |
| Linux x86_64 | avx2 | 13.77 | 12.91 | 1.07× |
| Linux x86_64 | generic | 41.75 | 47.19 | 0.88× |
| Windows AMD64 | avx2 | 18.44 | 18.13 | 1.02× |
| Windows AMD64 | generic | 50.50 | 64.57 | 0.78× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.96 | 142.02 | 0.36× |
| Darwin x86_64 | avx2 | — | 32.73 | — |
| Darwin x86_64 | generic | — | 86.32 | — |
| Darwin arm64 | generic | — | 58.10 | — |
| Linux x86_64 | avx2 | 19.77 | 58.94 | 0.34× |
| Linux x86_64 | generic | 53.59 | 150.66 | 0.36× |
| Windows AMD64 | avx2 | 24.65 | 74.82 | 0.33× |
| Windows AMD64 | generic | 60.40 | 175.46 | 0.34× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 36.83 | 19.76 | 1.86× |
| Darwin x86_64 | avx2 | 46.19 | 19.60 | 2.36× |
| Darwin x86_64 | generic | 113.44 | 50.90 | 2.23× |
| Darwin arm64 | generic | 85.41 | 15.99 | 5.34× |
| Linux x86_64 | avx2 | 13.48 | 24.96 | 0.54× |
| Linux x86_64 | generic | 40.10 | 83.71 | 0.48× |
| Windows AMD64 | avx2 | 17.95 | 26.69 | 0.67× |
| Windows AMD64 | generic | 45.38 | 44.47 | 1.02× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 67.69 | 120.27 | 0.56× |
| Darwin x86_64 | avx2 | 31.56 | 290.84 | 0.11× |
| Darwin x86_64 | generic | 67.18 | 297.10 | 0.23× |
| Darwin arm64 | generic | 43.01 | 117.00 | 0.37× |
| Linux x86_64 | avx2 | 29.71 | 165.19 | 0.18× |
| Linux x86_64 | generic | 68.33 | 222.65 | 0.31× |
| Windows AMD64 | avx2 | 21.36 | 94.37 | 0.23× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.18 | 21.84 | 0.83× |
| Darwin x86_64 | avx2 | 8.93 | 13.84 | 0.65× |
| Darwin x86_64 | generic | 32.16 | 68.78 | 0.47× |
| Darwin arm64 | generic | 29.74 | 39.27 | 0.76× |
| Linux x86_64 | avx2 | 8.10 | 7.70 | 1.05× |
| Linux x86_64 | generic | 29.83 | 30.02 | 0.99× |
| Windows AMD64 | avx2 | 10.88 | 10.98 | 0.99× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 176.29 | 136.16 | 1.29× |
| Darwin x86_64 | avx2 | 56.12 | 70.66 | 0.79× |
| Darwin x86_64 | generic | 140.58 | 204.49 | 0.69× |
| Darwin arm64 | generic | 121.70 | 109.49 | 1.11× |
| Linux x86_64 | avx2 | 60.82 | 58.20 | 1.05× |
| Linux x86_64 | generic | 177.66 | 159.72 | 1.11× |
| Windows AMD64 | avx2 | 75.96 | 73.49 | 1.03× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 517.77 | 303.93 | 1.70× |
| Darwin x86_64 | avx2 | 257.75 | 303.44 | 0.85× |
| Darwin x86_64 | generic | 610.28 | 1005.77 | 0.61× |
| Darwin arm64 | generic | 441.62 | 418.12 | 1.06× |
| Linux x86_64 | avx2 | 174.77 | 128.70 | 1.36× |
| Linux x86_64 | generic | 531.39 | 451.72 | 1.18× |
| Windows AMD64 | avx2 | 215.06 | 127.84 | 1.68× |
| Windows AMD64 | generic | 597.11 | 1215.08 | 0.49× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 69.13 | 56.62 | 1.22× |
| Darwin x86_64 | avx2 | 51.06 | 46.71 | 1.09× |
| Darwin x86_64 | generic | 93.97 | 71.40 | 1.32× |
| Darwin arm64 | generic | 60.15 | 44.25 | 1.36× |
| Linux x86_64 | avx2 | 29.14 | 25.55 | 1.14× |
| Linux x86_64 | generic | 75.42 | 62.50 | 1.21× |
| Windows AMD64 | avx2 | 38.04 | 30.25 | 1.26× |
| Windows AMD64 | generic | 92.48 | 75.30 | 1.23× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 141.11 | 143.96 | 0.98× |
| Darwin x86_64 | avx2 | 69.74 | 100.91 | 0.69× |
| Darwin x86_64 | generic | 160.38 | 238.27 | 0.67× |
| Darwin arm64 | generic | 116.67 | 134.98 | 0.86× |
| Linux x86_64 | avx2 | 55.14 | 57.64 | 0.96× |
| Linux x86_64 | generic | 147.03 | 153.04 | 0.96× |
| Windows AMD64 | avx2 | 73.23 | 76.00 | 0.96× |
| Windows AMD64 | generic | 162.39 | 165.47 | 0.98× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 130.03 | 98.25 | 1.32× |
| Darwin x86_64 | avx2 | 152.17 | 49.30 | 3.09× |
| Darwin x86_64 | generic | 418.37 | 88.70 | 4.72× |
| Darwin arm64 | generic | 322.78 | 48.54 | 6.65× |
| Linux x86_64 | avx2 | 42.60 | 39.50 | 1.08× |
| Linux x86_64 | generic | 136.64 | 51.86 | 2.63× |
| Windows AMD64 | avx2 | 64.20 | 36.53 | 1.76× |
| Windows AMD64 | generic | 178.44 | 179.91 | 0.99× |


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


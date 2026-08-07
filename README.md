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
| Linux aarch64 | 50.80 | — | — |
| Darwin x86_64 | 76.59 | 27.32 | 2.80× |
| Darwin arm64 | 50.94 | — | — |
| Linux x86_64 | 56.64 | 18.27 | 3.10× |
| Windows AMD64 | 62.99 | 20.52 | 3.07× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 45.31 | — | — |
| Darwin x86_64 | 60.07 | 27.63 | 2.17× |
| Darwin arm64 | 41.74 | — | — |
| Linux x86_64 | 50.93 | 18.52 | 2.75× |
| Windows AMD64 | 54.53 | 19.61 | 2.78× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 13.01 | 18.69 | 0.70× |
| Darwin x86_64 | avx2 | 7.32 | 13.68 | 0.53× |
| Darwin x86_64 | generic | 15.23 | 26.52 | 0.57× |
| Darwin arm64 | generic | 11.73 | 12.94 | 0.91× |
| Linux x86_64 | avx2 | 4.78 | 5.52 | 0.87× |
| Linux x86_64 | generic | 14.67 | 14.87 | 0.99× |
| Windows AMD64 | avx2 | 5.23 | 8.40 | 0.62× |
| Windows AMD64 | generic | 13.85 | 21.26 | 0.65× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 101.34 | 102.47 | 0.99× |
| Darwin x86_64 | avx2 | 64.88 | 55.21 | 1.18× |
| Darwin x86_64 | generic | 141.24 | 142.71 | 0.99× |
| Darwin arm64 | generic | 146.09 | 108.83 | 1.34× |
| Linux x86_64 | avx2 | 31.42 | 31.82 | 0.99× |
| Linux x86_64 | generic | 118.61 | 119.36 | 0.99× |
| Windows AMD64 | avx2 | 36.33 | 36.04 | 1.01× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.64 | 7.26 | 0.78× |
| Darwin x86_64 | avx2 | 3.30 | 3.46 | 0.95× |
| Darwin x86_64 | generic | 7.29 | 9.83 | 0.74× |
| Darwin arm64 | generic | 6.41 | 6.30 | 1.02× |
| Linux x86_64 | avx2 | 1.88 | 2.39 | 0.78× |
| Linux x86_64 | generic | 6.76 | 8.43 | 0.80× |
| Windows AMD64 | avx2 | 2.20 | 2.89 | 0.76× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 128.65 | 78.57 | 1.64× |
| Darwin x86_64 | avx2 | 63.99 | 70.45 | 0.91× |
| Darwin x86_64 | generic | 125.38 | 130.31 | 0.96× |
| Darwin arm64 | generic | 128.28 | 92.46 | 1.39× |
| Linux x86_64 | avx2 | 48.43 | 31.48 | 1.54× |
| Linux x86_64 | generic | 146.70 | 101.73 | 1.44× |
| Windows AMD64 | avx2 | 59.99 | 39.13 | 1.53× |
| Windows AMD64 | generic | 147.57 | — | — |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 60.50 | 51.01 | 1.19× |
| Darwin x86_64 | avx2 | 65.15 | 31.53 | 2.07× |
| Darwin x86_64 | generic | 118.28 | 58.21 | 2.03× |
| Darwin arm64 | generic | 113.48 | 42.81 | 2.65× |
| Linux x86_64 | avx2 | 23.73 | 20.66 | 1.15× |
| Linux x86_64 | generic | 70.63 | 58.50 | 1.21× |
| Windows AMD64 | avx2 | 28.96 | 21.03 | 1.38× |
| Windows AMD64 | generic | 70.44 | 62.88 | 1.12× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.06 | 35.19 | 0.85× |
| Darwin x86_64 | avx2 | 23.35 | 17.89 | 1.31× |
| Darwin x86_64 | generic | 52.23 | 45.14 | 1.16× |
| Darwin arm64 | generic | 45.07 | 27.15 | 1.66× |
| Linux x86_64 | avx2 | 9.36 | 9.77 | 0.96× |
| Linux x86_64 | generic | 34.42 | 35.53 | 0.97× |
| Windows AMD64 | avx2 | 13.00 | 13.61 | 0.96× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 412.75 | 472.43 | 0.87× |
| Darwin x86_64 | avx2 | 151.18 | 306.52 | 0.49× |
| Darwin x86_64 | generic | 382.24 | 691.58 | 0.55× |
| Darwin arm64 | generic | 286.99 | 440.26 | 0.65× |
| Linux x86_64 | avx2 | 159.19 | 180.00 | 0.88× |
| Linux x86_64 | generic | 442.26 | 504.06 | 0.88× |
| Windows AMD64 | avx2 | 178.56 | 200.14 | 0.89× |
| Windows AMD64 | generic | 446.52 | 558.83 | 0.80× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.44 | 3.53 | 0.97× |
| Darwin x86_64 | avx2 | 1.02 | 1.77 | 0.58× |
| Darwin x86_64 | generic | 4.42 | 4.68 | 0.94× |
| Darwin arm64 | generic | 1.78 | 2.58 | 0.69× |
| Linux x86_64 | avx2 | 1.32 | 1.31 | 1.01× |
| Linux x86_64 | generic | 3.96 | 4.14 | 0.96× |
| Windows AMD64 | avx2 | 1.52 | 1.44 | 1.06× |
| Windows AMD64 | generic | 3.19 | 4.10 | 0.78× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 94.38 | 111.62 | 0.85× |
| Darwin x86_64 | avx2 | 37.93 | 74.70 | 0.51× |
| Darwin x86_64 | generic | 182.78 | 165.38 | 1.11× |
| Darwin arm64 | generic | 108.02 | 125.18 | 0.86× |
| Linux x86_64 | avx2 | 29.73 | 34.62 | 0.86× |
| Linux x86_64 | generic | 110.38 | 128.11 | 0.86× |
| Windows AMD64 | avx2 | 34.71 | 37.96 | 0.91× |
| Windows AMD64 | generic | — | 132.38 | — |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.01 | 13.25 | 1.74× |
| Darwin x86_64 | avx2 | 9.81 | 15.10 | 0.65× |
| Darwin x86_64 | generic | 39.80 | 21.37 | 1.86× |
| Darwin arm64 | generic | 20.47 | 9.22 | 2.22× |
| Linux x86_64 | avx2 | 8.49 | 7.67 | 1.11× |
| Linux x86_64 | generic | 26.41 | 18.63 | 1.42× |
| Windows AMD64 | avx2 | 9.94 | 7.34 | 1.35× |
| Windows AMD64 | generic | 26.32 | 17.31 | 1.52× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.69 | 46.95 | 1.02× |
| Darwin x86_64 | avx2 | 12.78 | 34.35 | 0.37× |
| Darwin x86_64 | generic | 40.12 | 61.66 | 0.65× |
| Darwin arm64 | generic | 29.84 | 52.76 | 0.57× |
| Linux x86_64 | avx2 | 17.42 | 14.36 | 1.21× |
| Linux x86_64 | generic | 53.01 | 52.46 | 1.01× |
| Windows AMD64 | avx2 | 19.24 | 17.28 | 1.11× |
| Windows AMD64 | generic | 53.13 | 52.86 | 1.01× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 67.58 | 25.06 | 2.70× |
| Darwin x86_64 | avx2 | 72.40 | 11.73 | 6.17× |
| Darwin x86_64 | generic | 170.34 | 27.57 | 6.18× |
| Darwin arm64 | generic | 146.88 | 18.58 | 7.91× |
| Linux x86_64 | avx2 | 26.38 | 8.36 | 3.15× |
| Linux x86_64 | generic | 73.80 | 19.95 | 3.70× |
| Windows AMD64 | avx2 | 27.71 | 8.56 | 3.24× |
| Windows AMD64 | generic | 36.98 | 22.65 | 1.63× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.85 | 6.70 | 0.87× |
| Darwin x86_64 | avx2 | 1.32 | 6.25 | 0.21× |
| Darwin x86_64 | generic | 2.91 | 8.93 | 0.33× |
| Darwin arm64 | generic | 2.43 | 5.53 | 0.44× |
| Linux x86_64 | avx2 | 2.12 | 2.26 | 0.94× |
| Linux x86_64 | generic | 6.80 | 7.27 | 0.94× |
| Windows AMD64 | avx2 | 2.38 | 2.38 | 1.00× |
| Windows AMD64 | generic | 7.43 | 7.48 | 0.99× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 353.83 | 96.23 | 3.68× |
| Darwin x86_64 | avx2 | 209.87 | 54.65 | 3.84× |
| Darwin x86_64 | generic | 394.41 | 178.16 | 2.21× |
| Darwin arm64 | generic | 312.40 | 70.50 | 4.43× |
| Linux x86_64 | avx2 | 123.35 | 35.88 | 3.44× |
| Linux x86_64 | generic | 376.93 | 147.25 | 2.56× |
| Windows AMD64 | avx2 | 143.04 | 46.91 | 3.05× |
| Windows AMD64 | generic | 345.30 | 96.59 | 3.57× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 51.18 | 13.38 | 3.82× |
| Darwin x86_64 | avx2 | 30.95 | 10.56 | 2.93× |
| Darwin x86_64 | generic | 57.96 | 19.02 | 3.05× |
| Darwin arm64 | generic | 43.79 | 12.81 | 3.42× |
| Linux x86_64 | avx2 | 18.05 | 4.37 | 4.13× |
| Linux x86_64 | generic | 56.32 | 13.76 | 4.09× |
| Windows AMD64 | avx2 | 19.44 | 6.10 | 3.19× |
| Windows AMD64 | generic | 60.02 | 15.60 | 3.85× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 75.36 | 59.92 | 1.26× |
| Darwin x86_64 | avx2 | 56.98 | 69.17 | 0.82× |
| Darwin x86_64 | generic | 147.99 | 108.08 | 1.37× |
| Darwin arm64 | generic | 74.12 | 79.86 | 0.93× |
| Linux x86_64 | avx2 | 27.84 | 37.26 | 0.75× |
| Linux x86_64 | generic | 85.12 | 90.42 | 0.94× |
| Windows AMD64 | avx2 | 28.56 | 42.34 | 0.67× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.41 | 42.80 | 1.11× |
| Darwin x86_64 | avx2 | 20.79 | 52.82 | 0.39× |
| Darwin x86_64 | generic | 64.68 | 65.37 | 0.99× |
| Darwin arm64 | generic | 34.87 | 39.53 | 0.88× |
| Linux x86_64 | avx2 | 19.83 | 28.46 | 0.70× |
| Linux x86_64 | generic | 53.30 | 49.27 | 1.08× |
| Windows AMD64 | avx2 | 18.05 | 32.88 | 0.55× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.20 | 31.82 | 0.95× |
| Darwin x86_64 | avx2 | 26.97 | 11.38 | 2.37× |
| Darwin x86_64 | generic | 99.17 | 22.64 | 4.38× |
| Darwin arm64 | generic | 53.50 | 17.77 | 3.01× |
| Linux x86_64 | avx2 | 8.52 | 12.48 | 0.68× |
| Linux x86_64 | generic | 29.82 | 43.25 | 0.69× |
| Windows AMD64 | avx2 | 8.99 | 8.03 | 1.12× |
| Windows AMD64 | generic | 126.08 | 28.34 | 4.45× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 143.53 | 59.71 | 2.40× |
| Darwin x86_64 | avx2 | 48.62 | 32.50 | 1.50× |
| Darwin x86_64 | generic | 193.99 | 86.98 | 2.23× |
| Darwin arm64 | generic | 149.34 | 83.92 | 1.78× |
| Linux x86_64 | avx2 | 48.91 | 20.58 | 2.38× |
| Linux x86_64 | generic | 172.43 | 64.18 | 2.69× |
| Windows AMD64 | avx2 | 53.01 | 20.30 | 2.61× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.89 | 6.01 | 0.98× |
| Darwin x86_64 | avx2 | 2.82 | 4.08 | 0.69× |
| Darwin x86_64 | generic | 9.48 | 9.21 | 1.03× |
| Darwin arm64 | generic | 7.02 | 7.43 | 0.94× |
| Linux x86_64 | avx2 | 1.84 | 1.90 | 0.97× |
| Linux x86_64 | generic | 6.80 | 2.11 | 3.22× |
| Windows AMD64 | avx2 | 2.18 | 2.14 | 1.02× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.77 | 44.08 | 0.92× |
| Darwin x86_64 | avx2 | 17.40 | 23.51 | 0.74× |
| Darwin x86_64 | generic | 48.50 | 48.16 | 1.01× |
| Darwin arm64 | generic | 31.23 | 37.54 | 0.83× |
| Linux x86_64 | avx2 | 13.73 | 13.08 | 1.05× |
| Linux x86_64 | generic | 41.37 | 46.83 | 0.88× |
| Windows AMD64 | avx2 | 16.52 | 15.19 | 1.09× |
| Windows AMD64 | generic | 46.20 | 56.89 | 0.81× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.83 | 142.18 | 0.36× |
| Darwin x86_64 | avx2 | — | 41.79 | — |
| Darwin x86_64 | generic | — | 72.10 | — |
| Darwin arm64 | generic | — | 64.40 | — |
| Linux x86_64 | avx2 | 19.51 | 58.54 | 0.33× |
| Linux x86_64 | generic | 53.04 | 148.82 | 0.36× |
| Windows AMD64 | avx2 | 21.76 | 60.62 | 0.36× |
| Windows AMD64 | generic | 56.24 | 155.34 | 0.36× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.76 | 19.44 | 1.94× |
| Darwin x86_64 | avx2 | 56.39 | 16.01 | 3.52× |
| Darwin x86_64 | generic | 174.56 | 21.22 | 8.22× |
| Darwin arm64 | generic | 108.00 | 27.49 | 3.93× |
| Linux x86_64 | avx2 | 13.81 | 23.55 | 0.59× |
| Linux x86_64 | generic | 40.85 | 91.69 | 0.45× |
| Windows AMD64 | avx2 | 15.46 | 17.18 | 0.90× |
| Windows AMD64 | generic | 42.79 | 63.43 | 0.67× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 65.58 | 121.94 | 0.54× |
| Darwin x86_64 | avx2 | 27.54 | 209.53 | 0.13× |
| Darwin x86_64 | generic | 88.31 | 237.84 | 0.37× |
| Darwin arm64 | generic | 37.58 | 117.25 | 0.32× |
| Linux x86_64 | avx2 | 30.46 | 194.51 | 0.16× |
| Linux x86_64 | generic | 66.79 | 256.36 | 0.26× |
| Windows AMD64 | avx2 | 21.84 | 88.84 | 0.25× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.10 | 21.92 | 0.83× |
| Darwin x86_64 | avx2 | 8.68 | 12.47 | 0.70× |
| Darwin x86_64 | generic | 45.77 | 50.20 | 0.91× |
| Darwin arm64 | generic | 28.22 | 49.46 | 0.57× |
| Linux x86_64 | avx2 | 7.97 | 7.69 | 1.04× |
| Linux x86_64 | generic | 29.72 | 30.05 | 0.99× |
| Windows AMD64 | avx2 | 9.86 | 9.17 | 1.07× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 176.08 | 136.62 | 1.29× |
| Darwin x86_64 | avx2 | 53.34 | 62.70 | 0.85× |
| Darwin x86_64 | generic | 186.42 | 152.69 | 1.22× |
| Darwin arm64 | generic | 116.93 | 143.63 | 0.81× |
| Linux x86_64 | avx2 | 60.43 | 57.67 | 1.05× |
| Linux x86_64 | generic | 177.33 | 160.43 | 1.11× |
| Windows AMD64 | avx2 | 64.01 | 57.99 | 1.10× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 522.95 | 484.30 | 1.08× |
| Darwin x86_64 | avx2 | 276.23 | 186.97 | 1.48× |
| Darwin x86_64 | generic | 831.74 | 789.35 | 1.05× |
| Darwin arm64 | generic | 438.38 | 556.36 | 0.79× |
| Linux x86_64 | avx2 | 170.89 | 163.62 | 1.04× |
| Linux x86_64 | generic | 529.70 | 457.70 | 1.16× |
| Windows AMD64 | avx2 | 181.86 | 171.44 | 1.06× |
| Windows AMD64 | generic | 528.10 | 1044.94 | 0.51× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 70.39 | 57.35 | 1.23× |
| Darwin x86_64 | avx2 | 62.62 | 35.23 | 1.78× |
| Darwin x86_64 | generic | 142.87 | 104.24 | 1.37× |
| Darwin arm64 | generic | 63.59 | 53.58 | 1.19× |
| Linux x86_64 | avx2 | 28.09 | 25.07 | 1.12× |
| Linux x86_64 | generic | 74.02 | 60.86 | 1.22× |
| Windows AMD64 | avx2 | 31.45 | 25.04 | 1.26× |
| Windows AMD64 | generic | 81.69 | 66.17 | 1.23× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 139.63 | 145.02 | 0.96× |
| Darwin x86_64 | avx2 | 72.28 | 72.55 | 1.00× |
| Darwin x86_64 | generic | 182.19 | 247.79 | 0.74× |
| Darwin arm64 | generic | 96.49 | 144.28 | 0.67× |
| Linux x86_64 | avx2 | 53.25 | 55.59 | 0.96× |
| Linux x86_64 | generic | 146.95 | 153.94 | 0.95× |
| Windows AMD64 | avx2 | 60.33 | 61.51 | 0.98× |
| Windows AMD64 | generic | 122.88 | — | — |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 106.80 | 187.97 | 0.57× |
| Darwin x86_64 | avx2 | 95.62 | 27.90 | 3.43× |
| Darwin x86_64 | generic | 266.55 | 86.98 | 3.06× |
| Darwin arm64 | generic | 165.45 | 80.81 | 2.05× |
| Linux x86_64 | avx2 | 34.76 | 81.03 | 0.43× |
| Linux x86_64 | generic | 112.78 | 75.58 | 1.49× |
| Windows AMD64 | avx2 | 52.53 | 77.94 | 0.67× |
| Windows AMD64 | generic | 126.58 | 174.88 | 0.72× |


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


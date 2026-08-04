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

The AVX2/Haswell build is **~2.7×** faster than the generic build on average (geometric mean across 30 instances, 2 x86_64 platforms: Darwin x86_64, Linux x86_64).

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
| Linux aarch64 | 55.65 | — | — |
| Darwin x86_64 | 68.66 | 28.75 | 2.39× |
| Darwin arm64 | 52.82 | — | — |
| Linux x86_64 | 62.54 | 20.33 | 3.08× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 43.54 | — | — |
| Darwin x86_64 | 58.42 | 24.06 | 2.43× |
| Darwin arm64 | 37.41 | — | — |
| Linux x86_64 | 51.81 | 17.03 | 3.04× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 16.44 | 23.33 | 0.70× |
| Darwin x86_64 | avx2 | 8.07 | 16.14 | 0.50× |
| Darwin x86_64 | generic | 17.77 | 38.04 | 0.47× |
| Darwin arm64 | generic | 15.63 | 18.27 | 0.86× |
| Linux x86_64 | avx2 | 6.27 | 9.05 | 0.69× |
| Linux x86_64 | generic | 18.94 | 29.76 | 0.64× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 94.37 | 99.94 | 0.94× |
| Darwin x86_64 | avx2 | 58.16 | 57.99 | 1.00× |
| Darwin x86_64 | generic | 153.70 | 186.65 | 0.82× |
| Darwin arm64 | generic | 165.76 | 120.13 | 1.38× |
| Linux x86_64 | avx2 | 29.42 | 33.31 | 0.88× |
| Linux x86_64 | generic | 113.69 | 116.12 | 0.98× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.60 | 7.22 | 0.78× |
| Darwin x86_64 | avx2 | 2.53 | 3.71 | 0.68× |
| Darwin x86_64 | generic | 7.36 | 11.42 | 0.64× |
| Darwin arm64 | generic | 5.35 | 6.01 | 0.89× |
| Linux x86_64 | avx2 | 1.91 | 2.61 | 0.73× |
| Linux x86_64 | generic | 6.67 | 8.39 | 0.80× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 129.57 | 85.36 | 1.52× |
| Darwin x86_64 | avx2 | 57.48 | 51.73 | 1.11× |
| Darwin x86_64 | generic | 130.15 | 165.84 | 0.78× |
| Darwin arm64 | generic | 117.26 | 86.00 | 1.36× |
| Linux x86_64 | avx2 | 48.75 | 32.74 | 1.49× |
| Linux x86_64 | generic | 147.90 | 98.40 | 1.50× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 69.82 | 50.05 | 1.40× |
| Darwin x86_64 | avx2 | 55.60 | 30.88 | 1.80× |
| Darwin x86_64 | generic | 122.19 | 70.95 | 1.72× |
| Darwin arm64 | generic | 98.81 | 39.72 | 2.49× |
| Linux x86_64 | avx2 | 27.52 | 22.29 | 1.23× |
| Linux x86_64 | generic | 81.37 | 52.15 | 1.56× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.06 | 34.94 | 0.86× |
| Darwin x86_64 | avx2 | 19.26 | 16.88 | 1.14× |
| Darwin x86_64 | generic | 55.27 | 53.81 | 1.03× |
| Darwin arm64 | generic | 44.61 | 25.03 | 1.78× |
| Linux x86_64 | avx2 | 9.38 | 10.12 | 0.93× |
| Linux x86_64 | generic | 34.49 | 35.31 | 0.98× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 408.69 | 475.39 | 0.86× |
| Darwin x86_64 | avx2 | 127.57 | 275.79 | 0.46× |
| Darwin x86_64 | generic | 275.75 | 758.18 | 0.36× |
| Darwin arm64 | generic | 247.00 | 465.19 | 0.53× |
| Linux x86_64 | avx2 | 157.85 | 184.21 | 0.86× |
| Linux x86_64 | generic | 437.64 | 510.66 | 0.86× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.31 | 3.52 | 0.94× |
| Darwin x86_64 | avx2 | 1.18 | 1.52 | 0.78× |
| Darwin x86_64 | generic | 2.42 | 4.45 | 0.54× |
| Darwin arm64 | generic | 1.76 | 3.43 | 0.51× |
| Linux x86_64 | avx2 | 1.30 | 1.38 | 0.95× |
| Linux x86_64 | generic | 3.93 | 4.18 | 0.94× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 92.50 | 105.83 | 0.87× |
| Darwin x86_64 | avx2 | 43.53 | 52.61 | 0.83× |
| Darwin x86_64 | generic | 117.03 | 148.10 | 0.79× |
| Darwin arm64 | generic | 109.14 | 123.91 | 0.88× |
| Linux x86_64 | avx2 | 29.21 | 34.95 | 0.84× |
| Linux x86_64 | generic | 110.28 | 121.81 | 0.91× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 21.80 | 13.39 | 1.63× |
| Darwin x86_64 | avx2 | 8.32 | 9.13 | 0.91× |
| Darwin x86_64 | generic | 21.50 | 15.46 | 1.39× |
| Darwin arm64 | generic | 16.91 | 10.36 | 1.63× |
| Linux x86_64 | avx2 | 7.97 | 8.11 | 0.98× |
| Linux x86_64 | generic | 24.74 | 18.15 | 1.36× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 48.20 | 46.20 | 1.04× |
| Darwin x86_64 | avx2 | 12.14 | 24.35 | 0.50× |
| Darwin x86_64 | generic | 29.06 | 53.56 | 0.54× |
| Darwin arm64 | generic | 25.52 | 47.55 | 0.54× |
| Linux x86_64 | avx2 | 17.64 | 14.07 | 1.25× |
| Linux x86_64 | generic | 53.12 | 52.31 | 1.02× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 24.99 | 21.44 | 1.17× |
| Darwin x86_64 | avx2 | 16.02 | 5.91 | 2.71× |
| Darwin x86_64 | generic | 41.86 | 13.50 | 3.10× |
| Darwin arm64 | generic | 35.63 | 14.41 | 2.47× |
| Linux x86_64 | avx2 | 9.29 | 13.72 | 0.68× |
| Linux x86_64 | generic | 27.39 | 29.26 | 0.94× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.95 | 6.74 | 0.88× |
| Darwin x86_64 | avx2 | 0.95 | 4.37 | 0.22× |
| Darwin x86_64 | generic | 1.91 | 8.20 | 0.23× |
| Darwin arm64 | generic | 1.82 | 5.92 | 0.31× |
| Linux x86_64 | avx2 | 2.17 | 2.39 | 0.91× |
| Linux x86_64 | generic | 6.85 | 8.05 | 0.85× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 256.40 | 72.62 | 3.53× |
| Darwin x86_64 | avx2 | 101.78 | 54.41 | 1.87× |
| Darwin x86_64 | generic | 245.35 | 141.54 | 1.73× |
| Darwin arm64 | generic | 212.04 | 91.47 | 2.32× |
| Linux x86_64 | avx2 | 91.48 | 34.20 | 2.67× |
| Linux x86_64 | generic | 277.39 | 105.72 | 2.62× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 151.86 | 11.62 | 13.07× |
| Darwin x86_64 | avx2 | 80.22 | 6.49 | 12.36× |
| Darwin x86_64 | generic | 182.39 | 18.25 | 10.00× |
| Darwin arm64 | generic | 147.32 | 10.90 | 13.52× |
| Linux x86_64 | avx2 | 56.37 | 4.08 | 13.83× |
| Linux x86_64 | generic | 167.10 | 13.16 | 12.69× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 130.70 | 55.84 | 2.34× |
| Darwin x86_64 | avx2 | 56.72 | 51.10 | 1.11× |
| Darwin x86_64 | generic | 123.81 | 85.88 | 1.44× |
| Darwin arm64 | generic | 102.47 | 59.41 | 1.72× |
| Linux x86_64 | avx2 | 49.89 | 35.88 | 1.39× |
| Linux x86_64 | generic | 151.55 | 83.32 | 1.82× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 56.08 | 57.16 | 0.98× |
| Darwin x86_64 | avx2 | 20.98 | 53.39 | 0.39× |
| Darwin x86_64 | generic | 53.74 | 99.35 | 0.54× |
| Darwin arm64 | generic | 47.58 | 54.60 | 0.87× |
| Linux x86_64 | avx2 | 24.93 | 33.89 | 0.74× |
| Linux x86_64 | generic | 64.74 | 85.41 | 0.76× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 63.15 | 14.57 | 4.33× |
| Darwin x86_64 | avx2 | 23.29 | 4.70 | 4.96× |
| Darwin x86_64 | generic | 62.15 | 15.52 | 4.00× |
| Darwin arm64 | generic | 51.81 | 10.40 | 4.98× |
| Linux x86_64 | avx2 | 17.91 | 4.39 | 4.08× |
| Linux x86_64 | generic | 62.45 | 14.52 | 4.30× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 143.23 | 53.05 | 2.70× |
| Darwin x86_64 | avx2 | 38.13 | 26.26 | 1.45× |
| Darwin x86_64 | generic | 135.40 | 89.02 | 1.52× |
| Darwin arm64 | generic | 130.33 | 70.42 | 1.85× |
| Linux x86_64 | avx2 | 49.55 | 21.21 | 2.34× |
| Linux x86_64 | generic | 173.11 | 74.28 | 2.33× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.93 | 6.07 | 1.14× |
| Darwin x86_64 | avx2 | 2.87 | 2.77 | 1.04× |
| Darwin x86_64 | generic | 6.87 | 9.12 | 0.75× |
| Darwin arm64 | generic | 4.97 | 6.02 | 0.83× |
| Linux x86_64 | avx2 | 2.32 | 1.97 | 1.18× |
| Linux x86_64 | generic | 8.12 | 7.19 | 1.13× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.62 | 39.93 | 0.74× |
| Darwin x86_64 | avx2 | 12.34 | 15.39 | 0.80× |
| Darwin x86_64 | generic | 32.41 | 40.76 | 0.80× |
| Darwin arm64 | generic | 19.54 | 30.46 | 0.64× |
| Linux x86_64 | avx2 | 10.18 | 11.89 | 0.86× |
| Linux x86_64 | generic | 29.60 | 43.25 | 0.68× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.95 | 141.13 | 0.36× |
| Darwin x86_64 | avx2 | 2000.83 | 32.16 | 62.21× |
| Darwin x86_64 | generic | 2001.37 | 69.23 | 28.91× |
| Darwin arm64 | generic | 2001.28 | 55.24 | 36.23× |
| Linux x86_64 | avx2 | 20.21 | 60.16 | 0.34× |
| Linux x86_64 | generic | 54.46 | 152.81 | 0.36× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 154.12 | 51.77 | 2.98× |
| Darwin x86_64 | avx2 | 55.04 | 12.10 | 4.55× |
| Darwin x86_64 | generic | 128.00 | 26.42 | 4.84× |
| Darwin arm64 | generic | 77.67 | 20.47 | 3.79× |
| Linux x86_64 | avx2 | 60.23 | 13.58 | 4.44× |
| Linux x86_64 | generic | 171.69 | 57.73 | 2.97× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 68.56 | 166.98 | 0.41× |
| Darwin x86_64 | avx2 | 26.00 | 193.00 | 0.13× |
| Darwin x86_64 | generic | 59.81 | 193.96 | 0.31× |
| Darwin arm64 | generic | 24.64 | 68.10 | 0.36× |
| Linux x86_64 | avx2 | 32.03 | 118.84 | 0.27× |
| Linux x86_64 | generic | 73.16 | 220.54 | 0.33× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.10 | 21.79 | 0.83× |
| Darwin x86_64 | avx2 | 9.88 | 14.80 | 0.67× |
| Darwin x86_64 | generic | 36.58 | 45.27 | 0.81× |
| Darwin arm64 | generic | 23.38 | 35.82 | 0.65× |
| Linux x86_64 | avx2 | 7.86 | 7.83 | 1.00× |
| Linux x86_64 | generic | 29.97 | 30.21 | 0.99× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 176.65 | 136.91 | 1.29× |
| Darwin x86_64 | avx2 | 62.40 | 57.80 | 1.08× |
| Darwin x86_64 | generic | 168.87 | 141.86 | 1.19× |
| Darwin arm64 | generic | 116.37 | 113.77 | 1.02× |
| Linux x86_64 | avx2 | 60.92 | 54.73 | 1.11× |
| Linux x86_64 | generic | 176.33 | 161.77 | 1.09× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 521.96 | 399.11 | 1.31× |
| Darwin x86_64 | avx2 | 290.93 | 322.90 | 0.90× |
| Darwin x86_64 | generic | 706.72 | 531.95 | 1.33× |
| Darwin arm64 | generic | 450.12 | 416.95 | 1.08× |
| Linux x86_64 | avx2 | 178.28 | 119.67 | 1.49× |
| Linux x86_64 | generic | 531.80 | 476.56 | 1.12× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 70.62 | 57.37 | 1.23× |
| Darwin x86_64 | avx2 | 65.31 | 41.77 | 1.56× |
| Darwin x86_64 | generic | 122.00 | 76.61 | 1.59× |
| Darwin arm64 | generic | 62.54 | 45.20 | 1.38× |
| Linux x86_64 | avx2 | 28.40 | 27.38 | 1.04× |
| Linux x86_64 | generic | 74.12 | 72.51 | 1.02× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 138.25 | 141.96 | 0.97× |
| Darwin x86_64 | avx2 | 77.51 | 125.91 | 0.62× |
| Darwin x86_64 | generic | 171.02 | 299.44 | 0.57× |
| Darwin arm64 | generic | 97.68 | 178.12 | 0.55× |
| Linux x86_64 | avx2 | 51.86 | 54.13 | 0.96× |
| Linux x86_64 | generic | 143.60 | 151.13 | 0.95× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 107.96 | 61.78 | 1.75× |
| Darwin x86_64 | avx2 | 97.85 | 41.63 | 2.35× |
| Darwin x86_64 | generic | 235.31 | 134.18 | 1.75× |
| Darwin arm64 | generic | 177.65 | 35.96 | 4.94× |
| Linux x86_64 | avx2 | 35.39 | 16.62 | 2.13× |
| Linux x86_64 | generic | 113.83 | 53.77 | 2.12× |


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


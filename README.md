# cbcbox

[![PyPI version](https://img.shields.io/pypi/v/cbcbox.svg?color=brightgreen)](https://pypi.org/project/cbcbox/)
[![PyPI downloads](https://img.shields.io/pypi/dm/cbcbox.svg?color=blue)](https://pypi.org/project/cbcbox/)
[![CI](https://github.com/h-g-s/cbcbox/actions/workflows/wheel.yml/badge.svg)](https://github.com/h-g-s/cbcbox/actions/workflows/wheel.yml)
[![Platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20macOS%20%7C%20Windows-informational)](https://pypi.org/project/cbcbox/)
[![License](https://img.shields.io/badge/license-EPL--2.0-blue.svg)](https://opensource.org/licenses/EPL-2.0)

**cbcbox** is a high-performance, self-contained Python distribution of the
[CBC](https://github.com/coin-or/Cbc) MILP solver (COIN-OR Branch and Cut),
built from the latest COIN-OR `master` branch.

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

The AVX2/Haswell build is **~3.2×** faster than the generic build on average (geometric mean across 30 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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
| Linux aarch64 | 62.60 | — | — |
| Darwin x86_64 | 71.17 | 22.72 | 3.13× |
| Darwin arm64 | 55.68 | — | — |
| Linux x86_64 | 70.32 | 21.72 | 3.24× |
| Windows AMD64 | 52.89 | 16.97 | 3.12× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 36.32 | — | — |
| Darwin x86_64 | 42.91 | 15.53 | 2.76× |
| Darwin arm64 | 36.27 | — | — |
| Linux x86_64 | 40.59 | 11.77 | 3.45× |
| Windows AMD64 | 35.13 | 9.89 | 3.55× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 68.16 | 49.53 | 1.38× |
| Darwin x86_64 | avx2 | 26.17 | 26.21 | 1.00× |
| Darwin x86_64 | generic | 65.76 | 26.85 | 2.45× |
| Darwin arm64 | generic | 56.52 | 17.89 | 3.16× |
| Linux x86_64 | avx2 | 24.55 | 7.08 | 3.47× |
| Linux x86_64 | generic | 74.79 | 22.32 | 3.35× |
| Windows AMD64 | avx2 | 20.56 | 6.30 | 3.27× |
| Windows AMD64 | generic | 43.70 | 37.73 | 1.16× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 154.84 | 152.52 | 1.02× |
| Darwin x86_64 | avx2 | 60.62 | 52.38 | 1.16× |
| Darwin x86_64 | generic | 145.97 | 152.19 | 0.96× |
| Darwin arm64 | generic | 155.97 | 137.95 | 1.13× |
| Linux x86_64 | avx2 | 49.16 | 47.82 | 1.03× |
| Linux x86_64 | generic | 174.03 | 178.12 | 0.98× |
| Windows AMD64 | avx2 | 43.10 | 43.32 | 0.99× |
| Windows AMD64 | generic | 191.92 | 131.11 | 1.46× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 45.99 | 46.50 | 0.99× |
| Darwin x86_64 | avx2 | 9.75 | 9.44 | 1.03× |
| Darwin x86_64 | generic | 50.67 | 62.93 | 0.81× |
| Darwin arm64 | generic | 42.81 | 42.99 | 1.00× |
| Linux x86_64 | avx2 | 11.45 | 11.58 | 0.99× |
| Linux x86_64 | generic | 53.90 | 54.53 | 0.99× |
| Windows AMD64 | avx2 | 6.25 | 6.45 | 0.97× |
| Windows AMD64 | generic | 60.33 | 64.42 | 0.94× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 309.91 | 151.84 | 2.04× |
| Darwin x86_64 | avx2 | 60.16 | 36.92 | 1.63× |
| Darwin x86_64 | generic | 273.80 | 169.16 | 1.62× |
| Darwin arm64 | generic | 212.36 | 131.81 | 1.61× |
| Linux x86_64 | avx2 | 84.90 | 39.82 | 2.13× |
| Linux x86_64 | generic | 361.39 | 182.72 | 1.98× |
| Windows AMD64 | avx2 | 63.19 | 29.55 | 2.14× |
| Windows AMD64 | generic | 361.68 | 182.84 | 1.98× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 129.92 | 105.37 | 1.23× |
| Darwin x86_64 | avx2 | 31.30 | 33.30 | 0.94× |
| Darwin x86_64 | generic | 138.94 | 98.01 | 1.42× |
| Darwin arm64 | generic | 98.65 | 77.54 | 1.27× |
| Linux x86_64 | avx2 | 37.29 | 33.10 | 1.13× |
| Linux x86_64 | generic | 151.67 | 124.89 | 1.21× |
| Windows AMD64 | avx2 | 28.08 | 23.27 | 1.21× |
| Windows AMD64 | generic | 151.15 | 121.60 | 1.24× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.47 | 103.64 | 0.29× |
| Darwin x86_64 | avx2 | 4.99 | 24.71 | 0.20× |
| Darwin x86_64 | generic | 30.72 | 133.51 | 0.23× |
| Darwin arm64 | generic | 20.60 | 122.88 | 0.17× |
| Linux x86_64 | avx2 | 7.14 | 25.47 | 0.28× |
| Linux x86_64 | generic | 34.67 | 121.94 | 0.28× |
| Windows AMD64 | avx2 | 4.51 | 16.72 | 0.27× |
| Windows AMD64 | generic | 37.12 | 128.28 | 0.29× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 630.90 | 266.54 | 2.37× |
| Darwin x86_64 | avx2 | 136.33 | 227.59 | 0.60× |
| Darwin x86_64 | generic | 371.80 | 489.44 | 0.76× |
| Darwin arm64 | generic | 290.00 | 502.49 | 0.58× |
| Linux x86_64 | avx2 | 247.48 | 105.79 | 2.34× |
| Linux x86_64 | generic | 664.58 | 283.02 | 2.35× |
| Windows AMD64 | avx2 | 166.49 | 85.82 | 1.94× |
| Windows AMD64 | generic | 273.19 | 298.93 | 0.91× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 1.81 | 1.73 | 1.04× |
| Darwin x86_64 | avx2 | 0.53 | 0.77 | 0.68× |
| Darwin x86_64 | generic | 1.42 | 1.61 | 0.89× |
| Darwin arm64 | generic | 1.08 | 1.34 | 0.81× |
| Linux x86_64 | avx2 | 0.69 | 0.65 | 1.05× |
| Linux x86_64 | generic | 2.09 | 1.97 | 1.06× |
| Windows AMD64 | avx2 | 0.63 | 0.58 | 1.09× |
| Windows AMD64 | generic | 1.55 | 1.51 | 1.02× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 149.23 | 109.01 | 1.37× |
| Darwin x86_64 | avx2 | 48.86 | 47.16 | 1.04× |
| Darwin x86_64 | generic | 149.73 | 120.64 | 1.24× |
| Darwin arm64 | generic | 139.49 | 130.95 | 1.07× |
| Linux x86_64 | avx2 | 44.59 | 31.50 | 1.42× |
| Linux x86_64 | generic | 169.68 | 126.46 | 1.34× |
| Windows AMD64 | avx2 | 40.24 | 28.61 | 1.41× |
| Windows AMD64 | generic | 131.34 | 109.37 | 1.20× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 28.46 | 131.51 | 0.22× |
| Darwin x86_64 | avx2 | 11.09 | 68.21 | 0.16× |
| Darwin x86_64 | generic | 28.46 | 196.17 | 0.15× |
| Darwin arm64 | generic | 22.33 | 142.78 | 0.16× |
| Linux x86_64 | avx2 | 11.12 | 43.99 | 0.25× |
| Linux x86_64 | generic | 32.26 | 168.59 | 0.19× |
| Windows AMD64 | avx2 | 8.43 | 53.42 | 0.16× |
| Windows AMD64 | generic | 23.43 | 133.54 | 0.18× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 46.13 | 38.75 | 1.19× |
| Darwin x86_64 | avx2 | 16.13 | 15.12 | 1.07× |
| Darwin x86_64 | generic | 46.03 | 37.64 | 1.22× |
| Darwin arm64 | generic | 41.00 | 37.63 | 1.09× |
| Linux x86_64 | avx2 | 16.65 | 18.21 | 0.91× |
| Linux x86_64 | generic | 50.17 | 43.95 | 1.14× |
| Windows AMD64 | avx2 | 13.16 | 11.27 | 1.17× |
| Windows AMD64 | generic | 39.04 | 33.75 | 1.16× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 42.43 | 32.68 | 1.30× |
| Darwin x86_64 | avx2 | 10.05 | 22.95 | 0.44× |
| Darwin x86_64 | generic | 29.91 | 59.40 | 0.50× |
| Darwin arm64 | generic | 23.10 | 49.00 | 0.47× |
| Linux x86_64 | avx2 | 15.83 | 11.19 | 1.41× |
| Linux x86_64 | generic | 46.37 | 40.46 | 1.15× |
| Windows AMD64 | avx2 | 13.03 | 10.23 | 1.27× |
| Windows AMD64 | generic | 15.16 | 26.21 | 0.58× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.97 | 12.51 | 0.48× |
| Darwin x86_64 | avx2 | 3.02 | 6.78 | 0.45× |
| Darwin x86_64 | generic | 7.70 | 12.41 | 0.62× |
| Darwin arm64 | generic | 6.02 | 9.48 | 0.63× |
| Linux x86_64 | avx2 | 2.10 | 3.95 | 0.53× |
| Linux x86_64 | generic | 6.94 | 15.47 | 0.45× |
| Windows AMD64 | avx2 | 1.82 | 4.03 | 0.45× |
| Windows AMD64 | generic | 5.05 | 11.82 | 0.43× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 512.35 | 105.95 | 4.84× |
| Darwin x86_64 | avx2 | 189.63 | 38.24 | 4.96× |
| Darwin x86_64 | generic | 487.74 | 83.80 | 5.82× |
| Darwin arm64 | generic | 414.27 | 83.69 | 4.95× |
| Linux x86_64 | avx2 | 190.95 | 41.29 | 4.62× |
| Linux x86_64 | generic | 548.93 | 122.53 | 4.48× |
| Windows AMD64 | avx2 | 150.39 | 33.11 | 4.54× |
| Windows AMD64 | generic | 309.29 | 86.91 | 3.56× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 79.78 | 14.92 | 5.35× |
| Darwin x86_64 | avx2 | 31.15 | 5.38 | 5.79× |
| Darwin x86_64 | generic | 82.01 | 11.34 | 7.23× |
| Darwin arm64 | generic | 70.06 | 30.95 | 2.26× |
| Linux x86_64 | avx2 | 27.36 | 5.05 | 5.42× |
| Linux x86_64 | generic | 86.48 | 17.15 | 5.04× |
| Windows AMD64 | avx2 | 23.50 | 4.46 | 5.27× |
| Windows AMD64 | generic | 49.99 | 12.28 | 4.07× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 156.05 | 6.07 | 25.71× |
| Darwin x86_64 | avx2 | 54.13 | 3.86 | 14.03× |
| Darwin x86_64 | generic | 140.16 | 6.53 | 21.47× |
| Darwin arm64 | generic | 105.12 | 6.02 | 17.46× |
| Linux x86_64 | avx2 | 57.91 | 2.76 | 20.99× |
| Linux x86_64 | generic | 168.71 | 7.88 | 21.42× |
| Windows AMD64 | avx2 | 42.33 | 2.13 | 19.83× |
| Windows AMD64 | generic | 113.83 | 5.36 | 21.22× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 112.56 | 4.14 | 27.21× |
| Darwin x86_64 | avx2 | 36.12 | 3.04 | 11.88× |
| Darwin x86_64 | generic | 96.34 | 6.82 | 14.13× |
| Darwin arm64 | generic | 63.41 | 4.58 | 13.84× |
| Linux x86_64 | avx2 | 50.58 | 1.36 | 37.24× |
| Linux x86_64 | generic | 121.20 | 5.70 | 21.27× |
| Windows AMD64 | avx2 | 27.69 | 1.19 | 23.26× |
| Windows AMD64 | generic | 67.20 | 3.91 | 17.17× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.03 | 18.24 | 0.99× |
| Darwin x86_64 | avx2 | 5.07 | 6.08 | 0.83× |
| Darwin x86_64 | generic | 18.01 | 17.50 | 1.03× |
| Darwin arm64 | generic | 12.93 | 13.54 | 0.96× |
| Linux x86_64 | avx2 | 5.62 | 5.73 | 0.98× |
| Linux x86_64 | generic | 17.75 | 17.23 | 1.03× |
| Windows AMD64 | avx2 | 4.20 | 4.27 | 0.98× |
| Windows AMD64 | generic | 13.69 | 13.96 | 0.98× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 168.39 | 309.38 | 0.54× |
| Darwin x86_64 | avx2 | 46.08 | 76.00 | 0.61× |
| Darwin x86_64 | generic | 191.89 | 301.09 | 0.64× |
| Darwin arm64 | generic | 145.65 | 209.99 | 0.69× |
| Linux x86_64 | avx2 | 52.68 | 76.64 | 0.69× |
| Linux x86_64 | generic | 183.43 | 340.38 | 0.54× |
| Windows AMD64 | avx2 | 42.42 | 79.15 | 0.54× |
| Windows AMD64 | generic | 168.62 | 281.68 | 0.60× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.99 | 5.19 | 0.77× |
| Darwin x86_64 | avx2 | 2.74 | 2.99 | 0.92× |
| Darwin x86_64 | generic | 8.46 | 6.59 | 1.28× |
| Darwin arm64 | generic | 5.19 | 5.16 | 1.01× |
| Linux x86_64 | avx2 | 1.26 | 1.66 | 0.76× |
| Linux x86_64 | generic | 4.59 | 5.90 | 0.78× |
| Windows AMD64 | avx2 | 1.17 | 1.55 | 0.76× |
| Windows AMD64 | generic | 4.55 | 4.67 | 0.97× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 39.66 | 25.10 | 1.58× |
| Darwin x86_64 | avx2 | 16.74 | 13.31 | 1.26× |
| Darwin x86_64 | generic | 48.09 | 30.18 | 1.59× |
| Darwin arm64 | generic | 29.21 | 21.95 | 1.33× |
| Linux x86_64 | avx2 | 12.42 | 9.02 | 1.38× |
| Linux x86_64 | generic | 41.42 | 28.16 | 1.47× |
| Windows AMD64 | avx2 | 11.53 | 8.05 | 1.43× |
| Windows AMD64 | generic | 33.12 | 23.70 | 1.40× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 12.52 | 8.88 | 1.41× |
| Darwin x86_64 | avx2 | — | 4.23 | — |
| Darwin x86_64 | generic | — | 11.54 | — |
| Darwin arm64 | generic | — | 7.76 | — |
| Linux x86_64 | avx2 | 4.55 | 3.40 | 1.34× |
| Linux x86_64 | generic | 12.74 | 9.78 | 1.30× |
| Windows AMD64 | avx2 | 3.90 | 2.93 | 1.33× |
| Windows AMD64 | generic | 9.63 | 7.24 | 1.33× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 20.57 | 21.18 | 0.97× |
| Darwin x86_64 | avx2 | 8.77 | 14.22 | 0.62× |
| Darwin x86_64 | generic | 19.99 | 36.52 | 0.55× |
| Darwin arm64 | generic | 14.65 | 28.87 | 0.51× |
| Linux x86_64 | avx2 | 6.99 | 8.09 | 0.86× |
| Linux x86_64 | generic | 22.40 | 26.44 | 0.85× |
| Windows AMD64 | avx2 | 6.34 | 7.28 | 0.87× |
| Windows AMD64 | generic | 17.69 | 20.58 | 0.86× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 99.07 | 2.25 | 43.95× |
| Darwin x86_64 | avx2 | 50.61 | 2.22 | 22.80× |
| Darwin x86_64 | generic | 108.91 | 4.98 | 21.88× |
| Darwin arm64 | generic | 51.98 | 2.99 | 17.37× |
| Linux x86_64 | avx2 | 66.56 | 1.36 | 49.05× |
| Linux x86_64 | generic | 144.96 | 4.48 | 32.33× |
| Windows AMD64 | avx2 | 27.94 | 1.02 | 27.42× |
| Windows AMD64 | generic | 67.40 | 2.97 | 22.71× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 69.40 | 25.51 | 2.72× |
| Darwin x86_64 | avx2 | 20.21 | 8.08 | 2.50× |
| Darwin x86_64 | generic | 122.12 | 46.33 | 2.64× |
| Darwin arm64 | generic | 98.48 | 37.60 | 2.62× |
| Linux x86_64 | avx2 | 15.84 | 6.53 | 2.43× |
| Linux x86_64 | generic | 74.68 | 28.56 | 2.62× |
| Windows AMD64 | avx2 | 11.24 | 4.43 | 2.54× |
| Windows AMD64 | generic | 74.40 | 32.20 | 2.31× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 151.78 | 197.28 | 0.77× |
| Darwin x86_64 | avx2 | 69.19 | 41.28 | 1.68× |
| Darwin x86_64 | generic | 180.91 | 100.25 | 1.80× |
| Darwin arm64 | generic | 167.34 | 98.51 | 1.70× |
| Linux x86_64 | avx2 | 102.35 | 38.29 | 2.67× |
| Linux x86_64 | generic | 281.21 | 103.13 | 2.73× |
| Windows AMD64 | avx2 | 85.21 | 30.85 | 2.76× |
| Windows AMD64 | generic | 211.50 | 77.72 | 2.72× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 135.24 | 40.12 | 3.37× |
| Darwin x86_64 | avx2 | 47.15 | 18.20 | 2.59× |
| Darwin x86_64 | generic | 162.81 | 58.01 | 2.81× |
| Darwin arm64 | generic | 152.59 | 50.51 | 3.02× |
| Linux x86_64 | avx2 | 37.55 | 11.39 | 3.30× |
| Linux x86_64 | generic | 145.40 | 49.23 | 2.95× |
| Windows AMD64 | avx2 | 29.78 | 11.30 | 2.64× |
| Windows AMD64 | generic | 129.59 | 51.57 | 2.51× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 38.92 | 30.27 | 1.29× |
| Darwin x86_64 | avx2 | 12.48 | 9.74 | 1.28× |
| Darwin x86_64 | generic | 75.54 | 69.39 | 1.09× |
| Darwin arm64 | generic | 55.37 | 54.26 | 1.02× |
| Linux x86_64 | avx2 | 15.85 | 13.33 | 1.19× |
| Linux x86_64 | generic | 39.78 | 33.41 | 1.19× |
| Windows AMD64 | avx2 | 14.55 | 12.21 | 1.19× |
| Windows AMD64 | generic | 68.06 | 67.26 | 1.01× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 208.08 | 178.89 | 1.16× |
| Darwin x86_64 | avx2 | 103.25 | 99.29 | 1.04× |
| Darwin x86_64 | generic | 235.01 | 241.81 | 0.97× |
| Darwin arm64 | generic | 210.91 | 211.93 | 1.00× |
| Linux x86_64 | avx2 | 75.10 | 65.79 | 1.14× |
| Linux x86_64 | generic | 214.96 | 189.16 | 1.14× |
| Windows AMD64 | avx2 | 66.87 | 61.53 | 1.09× |
| Windows AMD64 | generic | 159.61 | 153.34 | 1.04× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 230.03 | 76.91 | 2.99× |
| Darwin x86_64 | avx2 | 167.74 | 29.48 | 5.69× |
| Darwin x86_64 | generic | 362.74 | 76.68 | 4.73× |
| Darwin arm64 | generic | 378.14 | 63.09 | 5.99× |
| Linux x86_64 | avx2 | 80.29 | 27.44 | 2.93× |
| Linux x86_64 | generic | 242.62 | 93.14 | 2.60× |
| Windows AMD64 | avx2 | 83.24 | 25.26 | 3.30× |
| Windows AMD64 | generic | 120.49 | 65.19 | 1.85× |


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

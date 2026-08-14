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

The AVX2/Haswell build is **~2.9×** faster than the generic build on average (geometric mean across 30 instances, 2 x86_64 platforms: Darwin x86_64, Linux x86_64).

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
| Linux aarch64 | 49.24 | — | — |
| Darwin x86_64 | 57.62 | 19.93 | 2.89× |
| Darwin arm64 | 47.56 | — | — |
| Linux x86_64 | 53.58 | 18.13 | 2.96× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 41.13 | — | — |
| Darwin x86_64 | 47.29 | 18.27 | 2.59× |
| Darwin arm64 | 36.80 | — | — |
| Linux x86_64 | 47.75 | 16.41 | 2.91× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 12.99 | 13.18 | 0.99× |
| Darwin x86_64 | avx2 | 5.02 | 9.99 | 0.50× |
| Darwin x86_64 | generic | 12.19 | 17.84 | 0.68× |
| Darwin arm64 | generic | 10.76 | 7.86 | 1.37× |
| Linux x86_64 | avx2 | 5.04 | 5.10 | 0.99× |
| Linux x86_64 | generic | 13.90 | 18.82 | 0.74× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 97.97 | 112.35 | 0.87× |
| Darwin x86_64 | avx2 | 44.96 | 45.44 | 0.99× |
| Darwin x86_64 | generic | 123.54 | 124.49 | 0.99× |
| Darwin arm64 | generic | 130.36 | 106.18 | 1.23× |
| Linux x86_64 | avx2 | 30.70 | 37.33 | 0.82× |
| Linux x86_64 | generic | 122.12 | 140.84 | 0.87× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.64 | 7.29 | 0.77× |
| Darwin x86_64 | avx2 | 2.05 | 3.24 | 0.63× |
| Darwin x86_64 | generic | 6.40 | 8.43 | 0.76× |
| Darwin arm64 | generic | 5.44 | 6.08 | 0.89× |
| Linux x86_64 | avx2 | 1.94 | 2.62 | 0.74× |
| Linux x86_64 | generic | 7.34 | 9.10 | 0.81× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 106.07 | 104.66 | 1.01× |
| Darwin x86_64 | avx2 | 36.74 | 33.31 | 1.10× |
| Darwin x86_64 | generic | 92.54 | 66.58 | 1.39× |
| Darwin arm64 | generic | 91.82 | 63.77 | 1.44× |
| Linux x86_64 | avx2 | 41.80 | 38.42 | 1.09× |
| Linux x86_64 | generic | 117.56 | 103.92 | 1.13× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 76.29 | 50.73 | 1.50× |
| Darwin x86_64 | avx2 | 37.37 | 23.39 | 1.60× |
| Darwin x86_64 | generic | 87.00 | 53.89 | 1.61× |
| Darwin arm64 | generic | 85.45 | 48.27 | 1.77× |
| Linux x86_64 | avx2 | 31.97 | 18.36 | 1.74× |
| Linux x86_64 | generic | 84.55 | 60.19 | 1.40× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.48 | 35.07 | 0.87× |
| Darwin x86_64 | avx2 | 14.22 | 12.35 | 1.15× |
| Darwin x86_64 | generic | 44.58 | 35.82 | 1.24× |
| Darwin arm64 | generic | 37.22 | 25.51 | 1.46× |
| Linux x86_64 | avx2 | 9.58 | 11.74 | 0.82× |
| Linux x86_64 | generic | 35.91 | 37.00 | 0.97× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 481.60 | 478.87 | 1.01× |
| Darwin x86_64 | avx2 | 127.94 | 171.31 | 0.75× |
| Darwin x86_64 | generic | 296.33 | 359.12 | 0.83× |
| Darwin arm64 | generic | 295.43 | 320.93 | 0.92× |
| Linux x86_64 | avx2 | 191.55 | 200.44 | 0.96× |
| Linux x86_64 | generic | 502.05 | 518.40 | 0.97× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.45 | 3.59 | 0.96× |
| Darwin x86_64 | avx2 | 0.87 | 1.39 | 0.63× |
| Darwin x86_64 | generic | 2.28 | 3.59 | 0.63× |
| Darwin arm64 | generic | 1.83 | 2.82 | 0.65× |
| Linux x86_64 | avx2 | 1.39 | 1.38 | 1.01× |
| Linux x86_64 | generic | 4.01 | 4.20 | 0.95× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 107.87 | 96.19 | 1.12× |
| Darwin x86_64 | avx2 | 33.89 | 41.56 | 0.82× |
| Darwin x86_64 | generic | 101.30 | 115.66 | 0.88× |
| Darwin arm64 | generic | 104.63 | 117.11 | 0.89× |
| Linux x86_64 | avx2 | 34.13 | 30.47 | 1.12× |
| Linux x86_64 | generic | 131.39 | 119.65 | 1.10× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 22.68 | 13.12 | 1.73× |
| Darwin x86_64 | avx2 | 8.28 | 9.43 | 0.88× |
| Darwin x86_64 | generic | 22.18 | 15.78 | 1.41× |
| Darwin arm64 | generic | 19.40 | 14.55 | 1.33× |
| Linux x86_64 | avx2 | 8.81 | 7.82 | 1.13× |
| Linux x86_64 | generic | 24.78 | 16.77 | 1.48× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 35.47 | 30.31 | 1.17× |
| Darwin x86_64 | avx2 | 9.15 | 13.29 | 0.69× |
| Darwin x86_64 | generic | 23.76 | 29.56 | 0.80× |
| Darwin arm64 | generic | 23.29 | 32.90 | 0.71× |
| Linux x86_64 | avx2 | 12.82 | 12.00 | 1.07× |
| Linux x86_64 | generic | 38.11 | 33.49 | 1.14× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 67.55 | 22.38 | 3.02× |
| Darwin x86_64 | avx2 | 62.41 | 7.31 | 8.54× |
| Darwin x86_64 | generic | 188.63 | 26.59 | 7.09× |
| Darwin arm64 | generic | 138.36 | 14.18 | 9.76× |
| Linux x86_64 | avx2 | 28.36 | 4.80 | 5.91× |
| Linux x86_64 | generic | 68.41 | 20.16 | 3.39× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.97 | 6.59 | 0.90× |
| Darwin x86_64 | avx2 | 1.85 | 2.59 | 0.71× |
| Darwin x86_64 | generic | 4.86 | 8.68 | 0.56× |
| Darwin arm64 | generic | 2.98 | 5.11 | 0.58× |
| Linux x86_64 | avx2 | 2.12 | 2.33 | 0.91× |
| Linux x86_64 | generic | 6.61 | 7.42 | 0.89× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 347.89 | 100.56 | 3.46× |
| Darwin x86_64 | avx2 | 133.42 | 61.48 | 2.17× |
| Darwin x86_64 | generic | 355.68 | 81.75 | 4.35× |
| Darwin arm64 | generic | 288.92 | 116.88 | 2.47× |
| Linux x86_64 | avx2 | 126.58 | 39.97 | 3.17× |
| Linux x86_64 | generic | 324.39 | 128.23 | 2.53× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 171.29 | 14.04 | 12.20× |
| Darwin x86_64 | avx2 | 62.72 | 7.29 | 8.60× |
| Darwin x86_64 | generic | 219.15 | 18.01 | 12.17× |
| Darwin arm64 | generic | 130.51 | 15.35 | 8.50× |
| Linux x86_64 | avx2 | 65.04 | 5.30 | 12.27× |
| Linux x86_64 | generic | 176.27 | 17.13 | 10.29× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 74.39 | 67.07 | 1.11× |
| Darwin x86_64 | avx2 | 34.94 | 47.04 | 0.74× |
| Darwin x86_64 | generic | 107.06 | 97.11 | 1.10× |
| Darwin arm64 | generic | 68.92 | 74.17 | 0.93× |
| Linux x86_64 | avx2 | 28.63 | 45.26 | 0.63× |
| Linux x86_64 | generic | 76.20 | 88.34 | 0.86× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.89 | 39.73 | 1.21× |
| Darwin x86_64 | avx2 | 15.32 | 37.35 | 0.41× |
| Darwin x86_64 | generic | 48.70 | 58.95 | 0.83× |
| Darwin arm64 | generic | 32.51 | 46.11 | 0.71× |
| Linux x86_64 | avx2 | 19.51 | 24.66 | 0.79× |
| Linux x86_64 | generic | 50.38 | 57.22 | 0.88× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.70 | 30.88 | 0.96× |
| Darwin x86_64 | avx2 | 20.66 | 6.76 | 3.05× |
| Darwin x86_64 | generic | 68.72 | 20.87 | 3.29× |
| Darwin arm64 | generic | 50.16 | 16.42 | 3.05× |
| Linux x86_64 | avx2 | 8.80 | 10.07 | 0.87× |
| Linux x86_64 | generic | 27.41 | 20.65 | 1.33× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 119.83 | 49.69 | 2.41× |
| Darwin x86_64 | avx2 | 43.56 | 17.67 | 2.47× |
| Darwin x86_64 | generic | 155.50 | 66.42 | 2.34× |
| Darwin arm64 | generic | 142.62 | 71.24 | 2.00× |
| Linux x86_64 | avx2 | 38.74 | 17.29 | 2.24× |
| Linux x86_64 | generic | 144.82 | 62.30 | 2.32× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.88 | 6.00 | 0.98× |
| Darwin x86_64 | avx2 | 2.16 | 2.70 | 0.80× |
| Darwin x86_64 | generic | 7.30 | 8.19 | 0.89× |
| Darwin arm64 | generic | 5.47 | 2.30 | 2.38× |
| Linux x86_64 | avx2 | 1.83 | 1.91 | 0.96× |
| Linux x86_64 | generic | 6.98 | 2.14 | 3.27× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.58 | 44.09 | 0.92× |
| Darwin x86_64 | avx2 | 13.59 | 15.32 | 0.89× |
| Darwin x86_64 | generic | 35.98 | 43.79 | 0.82× |
| Darwin arm64 | generic | 23.69 | 37.58 | 0.63× |
| Linux x86_64 | avx2 | 13.81 | 12.97 | 1.06× |
| Linux x86_64 | generic | 39.66 | 46.17 | 0.86× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 49.86 | 140.42 | 0.36× |
| Darwin x86_64 | avx2 | — | 28.38 | — |
| Darwin x86_64 | generic | — | 67.84 | — |
| Darwin arm64 | generic | — | 58.72 | — |
| Linux x86_64 | avx2 | 19.62 | 62.41 | 0.31× |
| Linux x86_64 | generic | 51.15 | 148.69 | 0.34× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.99 | 46.44 | 0.82× |
| Darwin x86_64 | avx2 | 52.63 | 8.74 | 6.02× |
| Darwin x86_64 | generic | 134.33 | 24.89 | 5.40× |
| Darwin arm64 | generic | 124.75 | 14.46 | 8.63× |
| Linux x86_64 | avx2 | 14.59 | 10.60 | 1.38× |
| Linux x86_64 | generic | 38.74 | 71.00 | 0.55× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 63.75 | 112.04 | 0.57× |
| Darwin x86_64 | avx2 | 25.64 | 125.31 | 0.20× |
| Darwin x86_64 | generic | 63.16 | 263.10 | 0.24× |
| Darwin arm64 | generic | 39.77 | 111.62 | 0.36× |
| Linux x86_64 | avx2 | 26.90 | 151.60 | 0.18× |
| Linux x86_64 | generic | 60.76 | 187.72 | 0.32× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.68 | 19.96 | 0.94× |
| Darwin x86_64 | avx2 | 6.32 | 8.84 | 0.71× |
| Darwin x86_64 | generic | 24.24 | 37.57 | 0.65× |
| Darwin arm64 | generic | 21.15 | 36.32 | 0.58× |
| Linux x86_64 | avx2 | 8.16 | 7.57 | 1.08× |
| Linux x86_64 | generic | 31.11 | 29.49 | 1.05× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 173.64 | 134.88 | 1.29× |
| Darwin x86_64 | avx2 | 44.90 | 48.37 | 0.93× |
| Darwin x86_64 | generic | 124.46 | 140.98 | 0.88× |
| Darwin arm64 | generic | 112.35 | 143.03 | 0.79× |
| Linux x86_64 | avx2 | 61.71 | 58.72 | 1.05× |
| Linux x86_64 | generic | 172.49 | 160.08 | 1.08× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 160.37 | 235.72 | 0.68× |
| Darwin x86_64 | avx2 | 46.67 | 97.72 | 0.48× |
| Darwin x86_64 | generic | 126.31 | 437.02 | 0.29× |
| Darwin arm64 | generic | 113.29 | 366.13 | 0.31× |
| Linux x86_64 | avx2 | 54.67 | 118.90 | 0.46× |
| Linux x86_64 | generic | 164.44 | 409.01 | 0.40× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 38.37 | 39.75 | 0.97× |
| Darwin x86_64 | avx2 | 18.61 | 19.97 | 0.93× |
| Darwin x86_64 | generic | 93.96 | 107.78 | 0.87× |
| Darwin arm64 | generic | 73.52 | 77.29 | 0.95× |
| Linux x86_64 | avx2 | 17.25 | 17.71 | 0.97× |
| Linux x86_64 | generic | 41.23 | 43.36 | 0.95× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 138.60 | 141.95 | 0.98× |
| Darwin x86_64 | avx2 | 51.24 | 67.63 | 0.76× |
| Darwin x86_64 | generic | 142.77 | 182.54 | 0.78× |
| Darwin arm64 | generic | 125.86 | 167.73 | 0.75× |
| Linux x86_64 | avx2 | 55.22 | 57.06 | 0.97× |
| Linux x86_64 | generic | 144.80 | 154.15 | 0.94× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 94.75 | 34.05 | 2.78× |
| Darwin x86_64 | avx2 | 80.40 | 31.28 | 2.57× |
| Darwin x86_64 | generic | 201.74 | 53.46 | 3.77× |
| Darwin arm64 | generic | 191.52 | 44.69 | 4.29× |
| Linux x86_64 | avx2 | 29.77 | 14.22 | 2.09× |
| Linux x86_64 | generic | 96.53 | 53.06 | 1.82× |


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


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
| Linux aarch64 | 51.04 | — | — |
| Darwin x86_64 | 60.64 | 23.56 | 2.57× |
| Darwin arm64 | 50.58 | — | — |
| Linux x86_64 | 56.04 | 18.26 | 3.07× |
| Windows AMD64 | 57.78 | 19.38 | 2.98× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 44.71 | — | — |
| Darwin x86_64 | 49.60 | 20.43 | 2.43× |
| Darwin arm64 | 39.04 | — | — |
| Linux x86_64 | 50.13 | 18.61 | 2.69× |
| Windows AMD64 | 58.03 | 19.15 | 3.03× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 13.05 | 15.59 | 0.84× |
| Darwin x86_64 | avx2 | 4.91 | 8.46 | 0.58× |
| Darwin x86_64 | generic | 12.66 | 18.71 | 0.68× |
| Darwin arm64 | generic | 9.84 | 10.59 | 0.93× |
| Linux x86_64 | avx2 | 4.77 | 5.26 | 0.91× |
| Linux x86_64 | generic | 14.36 | 15.61 | 0.92× |
| Windows AMD64 | avx2 | 5.05 | 5.77 | 0.88× |
| Windows AMD64 | generic | 14.49 | 10.41 | 1.39× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 101.44 | 102.92 | 0.99× |
| Darwin x86_64 | avx2 | 43.50 | 45.49 | 0.96× |
| Darwin x86_64 | generic | 121.09 | 121.83 | 0.99× |
| Darwin arm64 | generic | 111.91 | 115.79 | 0.97× |
| Linux x86_64 | avx2 | 31.44 | 31.97 | 0.98× |
| Linux x86_64 | generic | 116.64 | 119.10 | 0.98× |
| Windows AMD64 | avx2 | 34.95 | 35.56 | 0.98× |
| Windows AMD64 | generic | 127.56 | 119.60 | 1.07× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.60 | 7.24 | 0.77× |
| Darwin x86_64 | avx2 | 2.08 | 2.91 | 0.71× |
| Darwin x86_64 | generic | 6.16 | 8.69 | 0.71× |
| Darwin arm64 | generic | 4.28 | 6.62 | 0.65× |
| Linux x86_64 | avx2 | 1.89 | 2.42 | 0.78× |
| Linux x86_64 | generic | 6.48 | 8.38 | 0.77× |
| Windows AMD64 | avx2 | 2.14 | 2.82 | 0.76× |
| Windows AMD64 | generic | 6.76 | 8.65 | 0.78× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 128.23 | 82.18 | 1.56× |
| Darwin x86_64 | avx2 | 42.09 | 46.83 | 0.90× |
| Darwin x86_64 | generic | 103.04 | 104.93 | 0.98× |
| Darwin arm64 | generic | 87.52 | 92.77 | 0.94× |
| Linux x86_64 | avx2 | 48.52 | 33.84 | 1.43× |
| Linux x86_64 | generic | 145.94 | 103.40 | 1.41× |
| Windows AMD64 | avx2 | 57.67 | 37.75 | 1.53× |
| Windows AMD64 | generic | 147.68 | 140.83 | 1.05× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 60.67 | 49.79 | 1.22× |
| Darwin x86_64 | avx2 | 42.09 | 20.25 | 2.08× |
| Darwin x86_64 | generic | 97.59 | 47.61 | 2.05× |
| Darwin arm64 | generic | 81.54 | 48.44 | 1.68× |
| Linux x86_64 | avx2 | 23.75 | 24.18 | 0.98× |
| Linux x86_64 | generic | 70.04 | 58.13 | 1.20× |
| Windows AMD64 | avx2 | 27.59 | 23.01 | 1.20× |
| Windows AMD64 | generic | 71.07 | 68.34 | 1.04× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.09 | 35.15 | 0.86× |
| Darwin x86_64 | avx2 | 14.92 | 12.22 | 1.22× |
| Darwin x86_64 | generic | 45.21 | 35.08 | 1.29× |
| Darwin arm64 | generic | 32.72 | 25.93 | 1.26× |
| Linux x86_64 | avx2 | 9.37 | 11.33 | 0.83× |
| Linux x86_64 | generic | 34.09 | 35.35 | 0.96× |
| Windows AMD64 | avx2 | 12.13 | 12.97 | 0.94× |
| Windows AMD64 | generic | 36.12 | 36.88 | 0.98× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 417.46 | 479.55 | 0.87× |
| Darwin x86_64 | avx2 | 114.64 | 199.25 | 0.58× |
| Darwin x86_64 | generic | 267.21 | 574.46 | 0.47× |
| Darwin arm64 | generic | 227.87 | 416.60 | 0.55× |
| Linux x86_64 | avx2 | 159.50 | 181.57 | 0.88× |
| Linux x86_64 | generic | 437.54 | 508.92 | 0.86× |
| Windows AMD64 | avx2 | 173.12 | 200.90 | 0.86× |
| Windows AMD64 | generic | 471.73 | 583.11 | 0.81× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.47 | 3.60 | 0.96× |
| Darwin x86_64 | avx2 | 0.91 | 1.46 | 0.62× |
| Darwin x86_64 | generic | 2.31 | 3.60 | 0.64× |
| Darwin arm64 | generic | 1.74 | 2.54 | 0.68× |
| Linux x86_64 | avx2 | 1.32 | 1.30 | 1.02× |
| Linux x86_64 | generic | 3.94 | 4.13 | 0.95× |
| Windows AMD64 | avx2 | 1.43 | 1.47 | 0.97× |
| Windows AMD64 | generic | 3.33 | 4.00 | 0.83× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 95.14 | 111.92 | 0.85× |
| Darwin x86_64 | avx2 | 33.32 | 55.83 | 0.60× |
| Darwin x86_64 | generic | 97.48 | 143.57 | 0.68× |
| Darwin arm64 | generic | 90.63 | 121.03 | 0.75× |
| Linux x86_64 | avx2 | 29.80 | 34.75 | 0.86× |
| Linux x86_64 | generic | 110.64 | 127.91 | 0.87× |
| Windows AMD64 | avx2 | 32.50 | 37.48 | 0.87× |
| Windows AMD64 | generic | 117.25 | 132.51 | 0.88× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.26 | 12.89 | 1.80× |
| Darwin x86_64 | avx2 | 7.92 | 9.89 | 0.80× |
| Darwin x86_64 | generic | 21.43 | 18.48 | 1.16× |
| Darwin arm64 | generic | 17.25 | 11.01 | 1.57× |
| Linux x86_64 | avx2 | 8.47 | 7.52 | 1.13× |
| Linux x86_64 | generic | 25.75 | 19.03 | 1.35× |
| Windows AMD64 | avx2 | 8.38 | 7.13 | 1.18× |
| Windows AMD64 | generic | 26.90 | 18.52 | 1.45× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 48.19 | 47.37 | 1.02× |
| Darwin x86_64 | avx2 | 10.75 | 20.21 | 0.53× |
| Darwin x86_64 | generic | 27.87 | 52.78 | 0.53× |
| Darwin arm64 | generic | 24.78 | 46.96 | 0.53× |
| Linux x86_64 | avx2 | 17.55 | 14.13 | 1.24× |
| Linux x86_64 | generic | 52.31 | 52.46 | 1.00× |
| Windows AMD64 | avx2 | 17.82 | 17.51 | 1.02× |
| Windows AMD64 | generic | 55.05 | 53.31 | 1.03× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 68.01 | 22.15 | 3.07× |
| Darwin x86_64 | avx2 | 60.17 | 9.72 | 6.19× |
| Darwin x86_64 | generic | 142.54 | 27.90 | 5.11× |
| Darwin arm64 | generic | 133.26 | 18.60 | 7.16× |
| Linux x86_64 | avx2 | 26.48 | 14.72 | 1.80× |
| Linux x86_64 | generic | 72.31 | 27.06 | 2.67× |
| Windows AMD64 | avx2 | 27.03 | 7.79 | 3.47× |
| Windows AMD64 | generic | 36.62 | 35.43 | 1.03× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.93 | 6.20 | 0.96× |
| Darwin x86_64 | avx2 | 1.12 | 4.38 | 0.26× |
| Darwin x86_64 | generic | 2.49 | 8.40 | 0.30× |
| Darwin arm64 | generic | 2.16 | 5.42 | 0.40× |
| Linux x86_64 | avx2 | 2.11 | 2.24 | 0.94× |
| Linux x86_64 | generic | 6.62 | 7.24 | 0.91× |
| Windows AMD64 | avx2 | 2.30 | 2.40 | 0.96× |
| Windows AMD64 | generic | 7.41 | 6.90 | 1.07× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 354.37 | 94.10 | 3.77× |
| Darwin x86_64 | avx2 | 133.55 | 45.57 | 2.93× |
| Darwin x86_64 | generic | 372.90 | 73.55 | 5.07× |
| Darwin arm64 | generic | 299.70 | 67.98 | 4.41× |
| Linux x86_64 | avx2 | 123.36 | 37.74 | 3.27× |
| Linux x86_64 | generic | 372.34 | 133.03 | 2.80× |
| Windows AMD64 | avx2 | 122.80 | 40.24 | 3.05× |
| Windows AMD64 | generic | 343.30 | 97.43 | 3.52× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.72 | 15.08 | 3.36× |
| Darwin x86_64 | avx2 | 19.26 | 7.50 | 2.57× |
| Darwin x86_64 | generic | 56.41 | 14.42 | 3.91× |
| Darwin arm64 | generic | 44.16 | 13.50 | 3.27× |
| Linux x86_64 | avx2 | 18.12 | 7.60 | 2.38× |
| Linux x86_64 | generic | 54.72 | 13.52 | 4.05× |
| Windows AMD64 | avx2 | 19.46 | 5.59 | 3.48× |
| Windows AMD64 | generic | 60.24 | 16.46 | 3.66× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 75.96 | 64.32 | 1.18× |
| Darwin x86_64 | avx2 | 35.02 | 56.74 | 0.62× |
| Darwin x86_64 | generic | 94.19 | 95.03 | 0.99× |
| Darwin arm64 | generic | 74.03 | 66.29 | 1.12× |
| Linux x86_64 | avx2 | 27.74 | 38.57 | 0.72× |
| Linux x86_64 | generic | 82.81 | 88.05 | 0.94× |
| Windows AMD64 | avx2 | 27.31 | 38.89 | 0.70× |
| Windows AMD64 | generic | 81.88 | 83.46 | 0.98× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.45 | 48.99 | 0.97× |
| Darwin x86_64 | avx2 | 15.49 | 33.15 | 0.47× |
| Darwin x86_64 | generic | 40.57 | 83.40 | 0.49× |
| Darwin arm64 | generic | 34.56 | 46.17 | 0.75× |
| Linux x86_64 | avx2 | 19.61 | 28.52 | 0.69× |
| Linux x86_64 | generic | 52.96 | 48.49 | 1.09× |
| Windows AMD64 | avx2 | 17.39 | 30.15 | 0.58× |
| Windows AMD64 | generic | 49.15 | 59.12 | 0.83× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.23 | 31.87 | 0.95× |
| Darwin x86_64 | avx2 | 21.53 | 6.55 | 3.29× |
| Darwin x86_64 | generic | 72.22 | 22.54 | 3.20× |
| Darwin arm64 | generic | 52.57 | 16.32 | 3.22× |
| Linux x86_64 | avx2 | 8.48 | 7.84 | 1.08× |
| Linux x86_64 | generic | 29.43 | 18.95 | 1.55× |
| Windows AMD64 | avx2 | 8.59 | 9.48 | 0.91× |
| Windows AMD64 | generic | 123.96 | 62.93 | 1.97× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 143.42 | 54.29 | 2.64× |
| Darwin x86_64 | avx2 | 37.01 | 19.97 | 1.85× |
| Darwin x86_64 | generic | 146.54 | 89.87 | 1.63× |
| Darwin arm64 | generic | 133.36 | 76.79 | 1.74× |
| Linux x86_64 | avx2 | 48.70 | 21.20 | 2.30× |
| Linux x86_64 | generic | 171.25 | 62.05 | 2.76× |
| Windows AMD64 | avx2 | 51.74 | 19.51 | 2.65× |
| Windows AMD64 | generic | 177.05 | 65.50 | 2.70× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.87 | 6.00 | 0.98× |
| Darwin x86_64 | avx2 | 2.24 | 2.59 | 0.87× |
| Darwin x86_64 | generic | 6.76 | 3.03 | 2.23× |
| Darwin arm64 | generic | 5.71 | 6.33 | 0.90× |
| Linux x86_64 | avx2 | 1.83 | 1.83 | 1.00× |
| Linux x86_64 | generic | 6.75 | 7.10 | 0.95× |
| Windows AMD64 | avx2 | 2.11 | 2.23 | 0.94× |
| Windows AMD64 | generic | 5.24 | 5.76 | 0.91× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.90 | 44.00 | 0.93× |
| Darwin x86_64 | avx2 | 14.24 | 14.89 | 0.96× |
| Darwin x86_64 | generic | 34.74 | 44.57 | 0.78× |
| Darwin arm64 | generic | 25.86 | 34.31 | 0.75× |
| Linux x86_64 | avx2 | 13.60 | 12.82 | 1.06× |
| Linux x86_64 | generic | 40.93 | 47.67 | 0.86× |
| Windows AMD64 | avx2 | 15.42 | 15.28 | 1.01× |
| Windows AMD64 | generic | 44.51 | 56.62 | 0.79× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.93 | 140.10 | 0.36× |
| Darwin x86_64 | avx2 | 2000.56 | 29.19 | 68.52× |
| Darwin x86_64 | generic | 2001.19 | 64.69 | 30.93× |
| Darwin arm64 | generic | 2000.93 | 55.44 | 36.09× |
| Linux x86_64 | avx2 | 19.54 | 58.89 | 0.33× |
| Linux x86_64 | generic | 52.60 | 148.58 | 0.35× |
| Windows AMD64 | avx2 | 20.61 | 60.56 | 0.34× |
| Windows AMD64 | generic | 54.75 | 155.05 | 0.35× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 38.00 | 43.50 | 0.87× |
| Darwin x86_64 | avx2 | 45.13 | 7.61 | 5.93× |
| Darwin x86_64 | generic | 107.93 | 22.72 | 4.75× |
| Darwin arm64 | generic | 98.64 | 16.19 | 6.09× |
| Linux x86_64 | avx2 | 13.81 | 36.35 | 0.38× |
| Linux x86_64 | generic | 42.56 | 61.46 | 0.69× |
| Windows AMD64 | avx2 | 14.89 | 24.18 | 0.62× |
| Windows AMD64 | generic | 41.73 | 66.74 | 0.63× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 67.31 | 112.70 | 0.60× |
| Darwin x86_64 | avx2 | 22.80 | 154.58 | 0.15× |
| Darwin x86_64 | generic | 50.57 | 231.60 | 0.22× |
| Darwin arm64 | generic | 32.59 | 88.05 | 0.37× |
| Linux x86_64 | avx2 | 30.63 | 144.70 | 0.21× |
| Linux x86_64 | generic | 67.86 | 174.23 | 0.39× |
| Windows AMD64 | avx2 | 20.58 | 100.12 | 0.21× |
| Windows AMD64 | generic | 53.19 | 197.82 | 0.27× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.11 | 21.82 | 0.83× |
| Darwin x86_64 | avx2 | 7.18 | 9.91 | 0.72× |
| Darwin x86_64 | generic | 27.44 | 42.86 | 0.64× |
| Darwin arm64 | generic | 24.51 | 35.68 | 0.69× |
| Linux x86_64 | avx2 | 7.97 | 7.62 | 1.05× |
| Linux x86_64 | generic | 29.75 | 29.89 | 1.00× |
| Windows AMD64 | avx2 | 9.27 | 9.27 | 1.00× |
| Windows AMD64 | generic | 30.39 | 30.77 | 0.99× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 176.64 | 136.23 | 1.30× |
| Darwin x86_64 | avx2 | 44.89 | 47.35 | 0.95× |
| Darwin x86_64 | generic | 120.11 | 145.45 | 0.83× |
| Darwin arm64 | generic | 110.22 | 109.76 | 1.00× |
| Linux x86_64 | avx2 | 60.54 | 56.18 | 1.08× |
| Linux x86_64 | generic | 175.83 | 158.65 | 1.11× |
| Windows AMD64 | avx2 | 62.35 | 58.10 | 1.07× |
| Windows AMD64 | generic | 215.04 | 190.19 | 1.13× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 524.76 | 429.37 | 1.22× |
| Darwin x86_64 | avx2 | 208.88 | 167.53 | 1.25× |
| Darwin x86_64 | generic | 505.98 | 613.87 | 0.82× |
| Darwin arm64 | generic | 431.28 | 650.34 | 0.66× |
| Linux x86_64 | avx2 | 171.24 | 123.51 | 1.39× |
| Linux x86_64 | generic | 528.33 | 465.01 | 1.14× |
| Windows AMD64 | avx2 | 175.82 | 162.18 | 1.08× |
| Windows AMD64 | generic | 512.56 | 1243.25 | 0.41× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 71.50 | 55.94 | 1.28× |
| Darwin x86_64 | avx2 | 36.41 | 37.68 | 0.97× |
| Darwin x86_64 | generic | 80.30 | 71.89 | 1.12× |
| Darwin arm64 | generic | 67.71 | 56.08 | 1.21× |
| Linux x86_64 | avx2 | 28.11 | 24.86 | 1.13× |
| Linux x86_64 | generic | 72.02 | 63.04 | 1.14× |
| Windows AMD64 | avx2 | 29.66 | 25.17 | 1.18× |
| Windows AMD64 | generic | 79.43 | 67.20 | 1.18× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 139.97 | 144.52 | 0.97× |
| Darwin x86_64 | avx2 | 46.56 | 77.18 | 0.60× |
| Darwin x86_64 | generic | 109.39 | 158.63 | 0.69× |
| Darwin arm64 | generic | 94.32 | 136.62 | 0.69× |
| Linux x86_64 | avx2 | 53.32 | 55.40 | 0.96× |
| Linux x86_64 | generic | 145.78 | 153.33 | 0.95× |
| Windows AMD64 | avx2 | 59.21 | 61.27 | 0.97× |
| Windows AMD64 | generic | 119.36 | 123.10 | 0.97× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 107.94 | 82.91 | 1.30× |
| Darwin x86_64 | avx2 | 74.69 | 44.14 | 1.69× |
| Darwin x86_64 | generic | 173.64 | 91.11 | 1.91× |
| Darwin arm64 | generic | 161.72 | 74.42 | 2.17× |
| Linux x86_64 | avx2 | 34.50 | 40.81 | 0.85× |
| Linux x86_64 | generic | 111.74 | 55.69 | 2.01× |
| Windows AMD64 | avx2 | 41.18 | 53.10 | 0.78× |
| Windows AMD64 | generic | 123.48 | 216.97 | 0.57× |


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


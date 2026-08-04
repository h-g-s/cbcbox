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
| Linux aarch64 | 55.60 | — | — |
| Darwin x86_64 | 70.10 | 27.56 | 2.54× |
| Darwin arm64 | 58.26 | — | — |
| Linux x86_64 | 61.62 | 20.96 | 2.94× |
| Windows AMD64 | 61.14 | 21.15 | 2.89× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 42.52 | — | — |
| Darwin x86_64 | 51.61 | 20.33 | 2.54× |
| Darwin arm64 | 42.49 | — | — |
| Linux x86_64 | 51.77 | 18.00 | 2.88× |
| Windows AMD64 | 52.62 | 18.71 | 2.81× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 16.47 | 20.10 | 0.82× |
| Darwin x86_64 | avx2 | 6.58 | 12.23 | 0.54× |
| Darwin x86_64 | generic | 27.84 | 19.96 | 1.39× |
| Darwin arm64 | generic | 17.10 | 27.63 | 0.62× |
| Linux x86_64 | avx2 | 6.76 | 9.70 | 0.70× |
| Linux x86_64 | generic | 17.85 | 35.34 | 0.50× |
| Windows AMD64 | avx2 | 6.43 | 17.09 | 0.38× |
| Windows AMD64 | generic | 20.10 | 39.25 | 0.51× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 94.59 | 99.63 | 0.95× |
| Darwin x86_64 | avx2 | 43.22 | 49.56 | 0.87× |
| Darwin x86_64 | generic | 186.98 | 134.31 | 1.39× |
| Darwin arm64 | generic | 165.01 | 125.61 | 1.31× |
| Linux x86_64 | avx2 | 31.22 | 33.15 | 0.94× |
| Linux x86_64 | generic | 118.52 | 125.65 | 0.94× |
| Windows AMD64 | avx2 | 39.75 | 34.96 | 1.14× |
| Windows AMD64 | generic | 115.83 | 118.73 | 0.98× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.69 | 7.21 | 0.79× |
| Darwin x86_64 | avx2 | 2.08 | 3.03 | 0.69× |
| Darwin x86_64 | generic | 7.88 | 8.39 | 0.94× |
| Darwin arm64 | generic | 6.73 | 6.52 | 1.03× |
| Linux x86_64 | avx2 | 2.06 | 2.68 | 0.77× |
| Linux x86_64 | generic | 7.40 | 9.41 | 0.79× |
| Windows AMD64 | avx2 | 2.91 | 2.74 | 1.06× |
| Windows AMD64 | generic | 6.73 | 8.56 | 0.79× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 129.63 | 81.95 | 1.58× |
| Darwin x86_64 | avx2 | 47.34 | 50.23 | 0.94× |
| Darwin x86_64 | generic | 154.87 | 100.56 | 1.54× |
| Darwin arm64 | generic | 143.90 | 91.47 | 1.57× |
| Linux x86_64 | avx2 | 51.45 | 35.64 | 1.44× |
| Linux x86_64 | generic | 146.52 | 104.02 | 1.41× |
| Windows AMD64 | avx2 | 60.06 | 43.41 | 1.38× |
| Windows AMD64 | generic | 148.00 | 136.66 | 1.08× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 70.20 | 59.56 | 1.18× |
| Darwin x86_64 | avx2 | 56.69 | 24.80 | 2.29× |
| Darwin x86_64 | generic | 125.99 | 53.52 | 2.35× |
| Darwin arm64 | generic | 123.85 | 55.08 | 2.25× |
| Linux x86_64 | avx2 | 29.39 | 19.19 | 1.53× |
| Linux x86_64 | generic | 80.20 | 52.21 | 1.54× |
| Windows AMD64 | avx2 | 32.10 | 21.29 | 1.51× |
| Windows AMD64 | generic | 80.31 | 55.12 | 1.46× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.27 | 34.74 | 0.87× |
| Darwin x86_64 | avx2 | 20.79 | 17.14 | 1.21× |
| Darwin x86_64 | generic | 55.93 | 35.91 | 1.56× |
| Darwin arm64 | generic | 48.35 | 31.80 | 1.52× |
| Linux x86_64 | avx2 | 9.95 | 10.61 | 0.94× |
| Linux x86_64 | generic | 36.55 | 37.63 | 0.97× |
| Windows AMD64 | avx2 | 12.27 | 12.68 | 0.97× |
| Windows AMD64 | generic | 35.49 | 36.88 | 0.96× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 406.56 | 477.44 | 0.85× |
| Darwin x86_64 | avx2 | 143.76 | 296.24 | 0.49× |
| Darwin x86_64 | generic | 309.58 | 540.05 | 0.57× |
| Darwin arm64 | generic | 301.06 | 477.40 | 0.63× |
| Linux x86_64 | avx2 | 167.31 | 194.63 | 0.86× |
| Linux x86_64 | generic | 431.86 | 507.84 | 0.85× |
| Windows AMD64 | avx2 | 168.57 | 195.50 | 0.86× |
| Windows AMD64 | generic | 437.84 | 542.49 | 0.81× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 3.31 | 3.59 | 0.92× |
| Darwin x86_64 | avx2 | 1.05 | 1.76 | 0.60× |
| Darwin x86_64 | generic | 2.97 | 3.64 | 0.82× |
| Darwin arm64 | generic | 2.20 | 3.00 | 0.73× |
| Linux x86_64 | avx2 | 1.36 | 1.42 | 0.96× |
| Linux x86_64 | generic | 3.91 | 4.29 | 0.91× |
| Windows AMD64 | avx2 | 1.32 | 1.40 | 0.94× |
| Windows AMD64 | generic | 3.42 | 4.00 | 0.85× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 92.63 | 105.95 | 0.87× |
| Darwin x86_64 | avx2 | 52.24 | 65.93 | 0.79× |
| Darwin x86_64 | generic | 155.65 | 133.43 | 1.17× |
| Darwin arm64 | generic | 119.35 | 137.98 | 0.87× |
| Linux x86_64 | avx2 | 30.57 | 37.63 | 0.81× |
| Linux x86_64 | generic | 115.79 | 130.99 | 0.88× |
| Windows AMD64 | avx2 | 30.78 | 35.52 | 0.87× |
| Windows AMD64 | generic | 114.61 | 131.58 | 0.87× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 21.72 | 12.93 | 1.68× |
| Darwin x86_64 | avx2 | 9.61 | 9.22 | 1.04× |
| Darwin x86_64 | generic | 24.62 | 15.61 | 1.58× |
| Darwin arm64 | generic | 19.25 | 16.10 | 1.20× |
| Linux x86_64 | avx2 | 8.25 | 7.49 | 1.10× |
| Linux x86_64 | generic | 23.87 | 17.02 | 1.40× |
| Windows AMD64 | avx2 | 7.58 | 6.67 | 1.14× |
| Windows AMD64 | generic | 24.96 | 17.00 | 1.47× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 48.18 | 46.31 | 1.04× |
| Darwin x86_64 | avx2 | 12.72 | 22.51 | 0.57× |
| Darwin x86_64 | generic | 31.13 | 53.42 | 0.58× |
| Darwin arm64 | generic | 30.32 | 52.23 | 0.58× |
| Linux x86_64 | avx2 | 18.40 | 11.40 | 1.61× |
| Linux x86_64 | generic | 53.27 | 52.03 | 1.02× |
| Windows AMD64 | avx2 | 17.61 | 17.60 | 1.00× |
| Windows AMD64 | generic | 53.33 | 54.01 | 0.99× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 25.21 | 17.72 | 1.42× |
| Darwin x86_64 | avx2 | 17.62 | 8.02 | 2.20× |
| Darwin x86_64 | generic | 40.91 | 21.77 | 1.88× |
| Darwin arm64 | generic | 36.75 | 30.12 | 1.22× |
| Linux x86_64 | avx2 | 9.86 | 15.18 | 0.65× |
| Linux x86_64 | generic | 26.06 | 22.82 | 1.14× |
| Windows AMD64 | avx2 | 9.27 | 16.30 | 0.57× |
| Windows AMD64 | generic | 34.22 | 18.05 | 1.90× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.12 | 6.78 | 0.90× |
| Darwin x86_64 | avx2 | 1.20 | 3.98 | 0.30× |
| Darwin x86_64 | generic | 2.11 | 8.24 | 0.26× |
| Darwin arm64 | generic | 1.92 | 7.95 | 0.24× |
| Linux x86_64 | avx2 | 2.22 | 2.69 | 0.83× |
| Linux x86_64 | generic | 6.74 | 8.03 | 0.84× |
| Windows AMD64 | avx2 | 2.19 | 2.58 | 0.85× |
| Windows AMD64 | generic | 6.58 | 8.08 | 0.81× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 256.87 | 69.25 | 3.71× |
| Darwin x86_64 | avx2 | 116.61 | 55.71 | 2.09× |
| Darwin x86_64 | generic | 242.03 | 125.61 | 1.93× |
| Darwin arm64 | generic | 231.28 | 111.14 | 2.08× |
| Linux x86_64 | avx2 | 92.81 | 33.95 | 2.73× |
| Linux x86_64 | generic | 243.96 | 100.94 | 2.42× |
| Windows AMD64 | avx2 | 88.86 | 35.88 | 2.48× |
| Windows AMD64 | generic | 271.31 | 141.19 | 1.92× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 152.94 | 12.01 | 12.74× |
| Darwin x86_64 | avx2 | 92.34 | 4.90 | 18.83× |
| Darwin x86_64 | generic | 205.97 | 13.81 | 14.91× |
| Darwin arm64 | generic | 176.53 | 11.60 | 15.22× |
| Linux x86_64 | avx2 | 57.42 | 4.48 | 12.81× |
| Linux x86_64 | generic | 159.25 | 15.45 | 10.31× |
| Windows AMD64 | avx2 | 57.33 | 3.96 | 14.49× |
| Windows AMD64 | generic | 136.72 | 9.07 | 15.07× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 128.80 | 53.34 | 2.41× |
| Darwin x86_64 | avx2 | 63.02 | 36.30 | 1.74× |
| Darwin x86_64 | generic | 192.67 | 70.26 | 2.74× |
| Darwin arm64 | generic | 108.05 | 51.43 | 2.10× |
| Linux x86_64 | avx2 | 51.46 | 38.61 | 1.33× |
| Linux x86_64 | generic | 136.13 | 72.03 | 1.89× |
| Windows AMD64 | avx2 | 46.69 | 32.52 | 1.44× |
| Windows AMD64 | generic | 143.34 | 65.62 | 2.18× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 55.56 | 57.73 | 0.96× |
| Darwin x86_64 | avx2 | 24.89 | 35.55 | 0.70× |
| Darwin x86_64 | generic | 63.77 | 89.65 | 0.71× |
| Darwin arm64 | generic | 51.04 | 42.27 | 1.21× |
| Linux x86_64 | avx2 | 24.70 | 40.91 | 0.60× |
| Linux x86_64 | generic | 60.21 | 66.67 | 0.90× |
| Windows AMD64 | avx2 | 20.98 | 34.41 | 0.61× |
| Windows AMD64 | generic | 58.08 | 74.02 | 0.78× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 63.20 | 14.60 | 4.33× |
| Darwin x86_64 | avx2 | 25.80 | 4.03 | 6.41× |
| Darwin x86_64 | generic | 72.94 | 14.62 | 4.99× |
| Darwin arm64 | generic | 53.59 | 10.44 | 5.13× |
| Linux x86_64 | avx2 | 18.14 | 4.47 | 4.06× |
| Linux x86_64 | generic | 58.11 | 14.33 | 4.06× |
| Windows AMD64 | avx2 | 16.80 | 4.04 | 4.16× |
| Windows AMD64 | generic | 28.49 | 13.97 | 2.04× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 142.76 | 53.94 | 2.65× |
| Darwin x86_64 | avx2 | 42.66 | 18.33 | 2.33× |
| Darwin x86_64 | generic | 153.31 | 95.32 | 1.61× |
| Darwin arm64 | generic | 139.60 | 73.86 | 1.89× |
| Linux x86_64 | avx2 | 47.59 | 18.77 | 2.54× |
| Linux x86_64 | generic | 179.26 | 71.22 | 2.52× |
| Windows AMD64 | avx2 | 51.46 | 21.65 | 2.38× |
| Windows AMD64 | generic | 187.62 | 67.80 | 2.77× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.95 | 6.09 | 1.14× |
| Darwin x86_64 | avx2 | 3.10 | 2.58 | 1.20× |
| Darwin x86_64 | generic | 8.05 | 7.71 | 1.04× |
| Darwin arm64 | generic | 5.90 | 4.42 | 1.33× |
| Linux x86_64 | avx2 | 2.33 | 1.98 | 1.18× |
| Linux x86_64 | generic | 8.17 | 8.17 | 1.00× |
| Windows AMD64 | avx2 | 2.47 | 2.13 | 1.16× |
| Windows AMD64 | generic | 6.99 | 6.20 | 1.13× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 29.29 | 39.93 | 0.73× |
| Darwin x86_64 | avx2 | 14.58 | 13.07 | 1.12× |
| Darwin x86_64 | generic | 33.70 | 36.89 | 0.91× |
| Darwin arm64 | generic | 24.51 | 32.91 | 0.74× |
| Linux x86_64 | avx2 | 9.82 | 11.77 | 0.83× |
| Linux x86_64 | generic | 28.88 | 42.75 | 0.68× |
| Windows AMD64 | avx2 | 10.20 | 13.29 | 0.77× |
| Windows AMD64 | generic | 31.08 | 41.77 | 0.74× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.12 | 139.91 | 0.36× |
| Darwin x86_64 | avx2 | 2023.84 | 26.69 | 75.82× |
| Darwin x86_64 | generic | 2001.30 | 63.28 | 31.62× |
| Darwin arm64 | generic | 2001.47 | 59.50 | 33.64× |
| Linux x86_64 | avx2 | 19.98 | 63.57 | 0.31× |
| Linux x86_64 | generic | 52.45 | 151.93 | 0.35× |
| Windows AMD64 | avx2 | 20.32 | 59.76 | 0.34× |
| Windows AMD64 | generic | 56.78 | 153.67 | 0.37× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 155.20 | 49.85 | 3.11× |
| Darwin x86_64 | avx2 | 49.68 | 9.52 | 5.22× |
| Darwin x86_64 | generic | 95.51 | 25.19 | 3.79× |
| Darwin arm64 | generic | 87.15 | 22.48 | 3.88× |
| Linux x86_64 | avx2 | 63.56 | 24.73 | 2.57× |
| Linux x86_64 | generic | 163.43 | 65.56 | 2.49× |
| Windows AMD64 | avx2 | 60.75 | 28.64 | 2.12× |
| Windows AMD64 | generic | 179.16 | 89.27 | 2.01× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 64.19 | 110.85 | 0.58× |
| Darwin x86_64 | avx2 | 21.94 | 152.99 | 0.14× |
| Darwin x86_64 | generic | 42.05 | 216.42 | 0.19× |
| Darwin arm64 | generic | 27.30 | 118.55 | 0.23× |
| Linux x86_64 | avx2 | 29.12 | 118.00 | 0.25× |
| Linux x86_64 | generic | 66.01 | 182.21 | 0.36× |
| Windows AMD64 | avx2 | 20.87 | 92.02 | 0.23× |
| Windows AMD64 | generic | 63.99 | 148.51 | 0.43× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 18.15 | 21.85 | 0.83× |
| Darwin x86_64 | avx2 | 7.78 | 10.01 | 0.78× |
| Darwin x86_64 | generic | 27.89 | 56.04 | 0.50× |
| Darwin arm64 | generic | 26.23 | 36.60 | 0.72× |
| Linux x86_64 | avx2 | 8.12 | 8.06 | 1.01× |
| Linux x86_64 | generic | 30.93 | 32.29 | 0.96× |
| Windows AMD64 | avx2 | 9.04 | 9.24 | 0.98× |
| Windows AMD64 | generic | 32.61 | 31.58 | 1.03× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 176.53 | 136.20 | 1.30× |
| Darwin x86_64 | avx2 | 55.32 | 50.69 | 1.09× |
| Darwin x86_64 | generic | 125.93 | 173.39 | 0.73× |
| Darwin arm64 | generic | 108.83 | 118.96 | 0.91× |
| Linux x86_64 | avx2 | 63.20 | 56.53 | 1.12× |
| Linux x86_64 | generic | 174.12 | 160.69 | 1.08× |
| Windows AMD64 | avx2 | 61.91 | 57.85 | 1.07× |
| Windows AMD64 | generic | 225.79 | 180.25 | 1.25× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 520.70 | 360.06 | 1.45× |
| Darwin x86_64 | avx2 | 252.66 | 193.90 | 1.30× |
| Darwin x86_64 | generic | 574.86 | 627.37 | 0.92× |
| Darwin arm64 | generic | 441.13 | 422.43 | 1.04× |
| Linux x86_64 | avx2 | 184.25 | 124.81 | 1.48× |
| Linux x86_64 | generic | 541.00 | 461.68 | 1.17× |
| Windows AMD64 | avx2 | 172.22 | 137.77 | 1.25× |
| Windows AMD64 | generic | 543.57 | 766.75 | 0.71× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 71.73 | 56.48 | 1.27× |
| Darwin x86_64 | avx2 | 38.34 | 27.29 | 1.40× |
| Darwin x86_64 | generic | 85.11 | 72.09 | 1.18× |
| Darwin arm64 | generic | 65.52 | 50.73 | 1.29× |
| Linux x86_64 | avx2 | 30.70 | 26.82 | 1.14× |
| Linux x86_64 | generic | 76.03 | 66.46 | 1.14× |
| Windows AMD64 | avx2 | 28.48 | 24.42 | 1.17× |
| Windows AMD64 | generic | 78.25 | 66.11 | 1.18× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.85 | 141.16 | 0.97× |
| Darwin x86_64 | avx2 | 46.29 | 95.39 | 0.49× |
| Darwin x86_64 | generic | 120.16 | 233.55 | 0.51× |
| Darwin arm64 | generic | 106.05 | 179.42 | 0.59× |
| Linux x86_64 | avx2 | 55.01 | 56.44 | 0.97× |
| Linux x86_64 | generic | 145.78 | 152.86 | 0.95× |
| Windows AMD64 | avx2 | 56.72 | 58.59 | 0.97× |
| Windows AMD64 | generic | 124.53 | 127.65 | 0.98× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 108.30 | 69.44 | 1.56× |
| Darwin x86_64 | avx2 | 66.81 | 22.43 | 2.98× |
| Darwin x86_64 | generic | 179.68 | 92.22 | 1.95× |
| Darwin arm64 | generic | 168.77 | 58.76 | 2.87× |
| Linux x86_64 | avx2 | 36.61 | 26.54 | 1.38× |
| Linux x86_64 | generic | 117.31 | 56.56 | 2.07× |
| Windows AMD64 | avx2 | 40.54 | 24.27 | 1.67× |
| Windows AMD64 | generic | 125.66 | 88.84 | 1.41× |


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


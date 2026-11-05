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
| Linux aarch64 | 62.06 | — | — |
| Darwin x86_64 | 68.78 | 21.71 | 3.17× |
| Darwin arm64 | 61.41 | — | — |
| Linux x86_64 | 54.56 | 17.57 | 3.11× |
| Windows AMD64 | 53.62 | 21.77 | 2.46× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 36.22 | — | — |
| Darwin x86_64 | 43.67 | 14.25 | 3.06× |
| Darwin arm64 | 35.08 | — | — |
| Linux x86_64 | 35.00 | 9.80 | 3.57× |
| Windows AMD64 | 35.91 | 14.87 | 2.41× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 68.04 | 19.17 | 3.55× |
| Darwin x86_64 | avx2 | 30.45 | 7.96 | 3.82× |
| Darwin x86_64 | generic | 84.76 | 57.07 | 1.49× |
| Darwin arm64 | generic | 74.35 | 16.39 | 4.54× |
| Linux x86_64 | avx2 | 19.92 | 5.74 | 3.47× |
| Linux x86_64 | generic | 57.05 | 51.80 | 1.10× |
| Windows AMD64 | avx2 | 26.11 | 21.04 | 1.24× |
| Windows AMD64 | generic | 51.45 | 42.33 | 1.22× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 154.99 | 151.54 | 1.02× |
| Darwin x86_64 | avx2 | 60.02 | 51.56 | 1.16× |
| Darwin x86_64 | generic | 181.28 | 144.14 | 1.26× |
| Darwin arm64 | generic | 177.25 | 138.78 | 1.28× |
| Linux x86_64 | avx2 | 39.67 | 38.58 | 1.03× |
| Linux x86_64 | generic | 145.06 | 149.72 | 0.97× |
| Windows AMD64 | avx2 | 54.00 | 53.23 | 1.01× |
| Windows AMD64 | generic | 178.67 | 122.89 | 1.45× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 46.11 | 46.46 | 0.99× |
| Darwin x86_64 | avx2 | 9.45 | 9.31 | 1.02× |
| Darwin x86_64 | generic | 61.08 | 51.91 | 1.18× |
| Darwin arm64 | generic | 52.06 | 42.56 | 1.22× |
| Linux x86_64 | avx2 | 9.65 | 9.70 | 0.99× |
| Linux x86_64 | generic | 47.09 | 47.68 | 0.99× |
| Windows AMD64 | avx2 | 8.85 | 8.98 | 0.98× |
| Windows AMD64 | generic | 58.29 | 56.23 | 1.04× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 335.22 | 151.44 | 2.21× |
| Darwin x86_64 | avx2 | 61.57 | 37.88 | 1.63× |
| Darwin x86_64 | generic | 299.42 | 154.04 | 1.94× |
| Darwin arm64 | generic | 257.08 | 124.41 | 2.07× |
| Linux x86_64 | avx2 | 78.45 | 32.79 | 2.39× |
| Linux x86_64 | generic | 328.06 | 157.60 | 2.08× |
| Windows AMD64 | avx2 | 100.19 | 40.28 | 2.49× |
| Windows AMD64 | generic | 359.95 | 165.69 | 2.17× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 129.83 | 105.48 | 1.23× |
| Darwin x86_64 | avx2 | 34.47 | 34.48 | 1.00× |
| Darwin x86_64 | generic | 136.76 | 88.61 | 1.54× |
| Darwin arm64 | generic | 110.77 | 71.18 | 1.56× |
| Linux x86_64 | avx2 | 31.38 | 26.41 | 1.19× |
| Linux x86_64 | generic | 128.36 | 105.48 | 1.22× |
| Windows AMD64 | avx2 | 38.94 | 31.34 | 1.24× |
| Windows AMD64 | generic | 140.41 | 117.13 | 1.20× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 30.39 | 103.62 | 0.29× |
| Darwin x86_64 | avx2 | 5.30 | 24.75 | 0.21× |
| Darwin x86_64 | generic | 28.52 | 163.25 | 0.17× |
| Darwin arm64 | generic | 22.58 | 125.42 | 0.18× |
| Linux x86_64 | avx2 | 6.11 | 20.98 | 0.29× |
| Linux x86_64 | generic | 30.50 | 105.70 | 0.29× |
| Windows AMD64 | avx2 | 5.94 | 22.82 | 0.26× |
| Windows AMD64 | generic | 32.22 | 113.64 | 0.28× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 629.99 | 264.97 | 2.38× |
| Darwin x86_64 | avx2 | 157.69 | 220.06 | 0.72× |
| Darwin x86_64 | generic | 409.46 | 534.55 | 0.77× |
| Darwin arm64 | generic | 346.30 | 478.51 | 0.72× |
| Linux x86_64 | avx2 | 199.69 | 81.48 | 2.45× |
| Linux x86_64 | generic | 517.96 | 217.62 | 2.38× |
| Windows AMD64 | avx2 | 216.22 | 119.91 | 1.80× |
| Windows AMD64 | generic | 301.84 | 323.43 | 0.93× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 1.84 | 1.72 | 1.07× |
| Darwin x86_64 | avx2 | 0.64 | 0.65 | 0.99× |
| Darwin x86_64 | generic | 1.68 | 1.63 | 1.03× |
| Darwin arm64 | generic | 1.17 | 1.23 | 0.95× |
| Linux x86_64 | avx2 | 0.62 | 0.54 | 1.16× |
| Linux x86_64 | generic | 1.74 | 1.62 | 1.07× |
| Windows AMD64 | avx2 | 0.77 | 0.86 | 0.90× |
| Windows AMD64 | generic | 1.72 | 1.62 | 1.06× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 150.33 | 110.22 | 1.36× |
| Darwin x86_64 | avx2 | 58.76 | 42.49 | 1.38× |
| Darwin x86_64 | generic | 168.88 | 122.42 | 1.38× |
| Darwin arm64 | generic | 174.35 | 113.90 | 1.53× |
| Linux x86_64 | avx2 | 37.09 | 25.81 | 1.44× |
| Linux x86_64 | generic | 143.70 | 107.61 | 1.34× |
| Windows AMD64 | avx2 | 49.38 | 47.11 | 1.05× |
| Windows AMD64 | generic | 121.89 | 100.61 | 1.21× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 28.97 | 132.94 | 0.22× |
| Darwin x86_64 | avx2 | 12.13 | 62.32 | 0.19× |
| Darwin x86_64 | generic | 29.25 | 209.21 | 0.14× |
| Darwin arm64 | generic | 30.00 | 140.54 | 0.21× |
| Linux x86_64 | avx2 | 9.20 | 37.49 | 0.25× |
| Linux x86_64 | generic | 24.79 | 145.84 | 0.17× |
| Windows AMD64 | avx2 | 10.77 | 58.18 | 0.19× |
| Windows AMD64 | generic | 27.64 | 128.32 | 0.22× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 46.95 | 38.73 | 1.21× |
| Darwin x86_64 | avx2 | 17.17 | 13.91 | 1.23× |
| Darwin x86_64 | generic | 47.55 | 38.82 | 1.22× |
| Darwin arm64 | generic | 51.84 | 35.08 | 1.48× |
| Linux x86_64 | avx2 | 12.83 | 13.81 | 0.93× |
| Linux x86_64 | generic | 39.56 | 34.76 | 1.14× |
| Windows AMD64 | avx2 | 16.11 | 17.99 | 0.90× |
| Windows AMD64 | generic | 40.19 | 34.74 | 1.16× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 42.72 | 32.57 | 1.31× |
| Darwin x86_64 | avx2 | 10.26 | 18.98 | 0.54× |
| Darwin x86_64 | generic | 27.32 | 60.25 | 0.45× |
| Darwin arm64 | generic | 29.85 | 45.45 | 0.66× |
| Linux x86_64 | avx2 | 13.41 | 9.40 | 1.43× |
| Linux x86_64 | generic | 35.61 | 32.23 | 1.11× |
| Windows AMD64 | avx2 | 16.84 | 12.74 | 1.32× |
| Windows AMD64 | generic | 17.19 | 27.50 | 0.62× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.09 | 12.64 | 0.48× |
| Darwin x86_64 | avx2 | 3.18 | 4.99 | 0.64× |
| Darwin x86_64 | generic | 8.01 | 12.47 | 0.64× |
| Darwin arm64 | generic | 7.65 | 8.88 | 0.86× |
| Linux x86_64 | avx2 | 1.77 | 3.46 | 0.51× |
| Linux x86_64 | generic | 5.45 | 13.34 | 0.41× |
| Windows AMD64 | avx2 | 2.36 | 4.82 | 0.49× |
| Windows AMD64 | generic | 5.55 | 11.83 | 0.47× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 478.45 | 88.84 | 5.39× |
| Darwin x86_64 | avx2 | 179.49 | 39.37 | 4.56× |
| Darwin x86_64 | generic | 470.10 | 98.52 | 4.77× |
| Darwin arm64 | generic | 501.66 | 83.34 | 6.02× |
| Linux x86_64 | avx2 | 142.45 | 27.46 | 5.19× |
| Linux x86_64 | generic | 358.71 | 74.78 | 4.80× |
| Windows AMD64 | avx2 | 190.12 | 37.46 | 5.08× |
| Windows AMD64 | generic | 378.73 | 86.80 | 4.36× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 51.42 | 15.10 | 3.41× |
| Darwin x86_64 | avx2 | 16.78 | 4.18 | 4.01× |
| Darwin x86_64 | generic | 46.42 | 11.43 | 4.06× |
| Darwin arm64 | generic | 52.63 | 9.70 | 5.43× |
| Linux x86_64 | avx2 | 15.21 | 4.09 | 3.71× |
| Linux x86_64 | generic | 42.06 | 13.92 | 3.02× |
| Windows AMD64 | avx2 | 21.38 | 5.69 | 3.75× |
| Windows AMD64 | generic | 36.13 | 13.89 | 2.60× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 159.54 | 6.08 | 26.26× |
| Darwin x86_64 | avx2 | 54.33 | 2.95 | 18.44× |
| Darwin x86_64 | generic | 144.93 | 6.18 | 23.44× |
| Darwin arm64 | generic | 144.50 | 5.03 | 28.73× |
| Linux x86_64 | avx2 | 49.80 | 2.15 | 23.20× |
| Linux x86_64 | generic | 123.54 | 5.84 | 21.17× |
| Windows AMD64 | avx2 | 54.15 | 2.74 | 19.75× |
| Windows AMD64 | generic | 142.51 | 6.73 | 21.17× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 114.65 | 4.13 | 27.79× |
| Darwin x86_64 | avx2 | 36.18 | 2.68 | 13.52× |
| Darwin x86_64 | generic | 90.84 | 6.28 | 14.47× |
| Darwin arm64 | generic | 79.83 | 4.75 | 16.81× |
| Linux x86_64 | avx2 | 39.75 | 1.00 | 39.64× |
| Linux x86_64 | generic | 87.15 | 4.58 | 19.03× |
| Windows AMD64 | avx2 | 33.01 | 11.46 | 2.88× |
| Windows AMD64 | generic | 82.83 | 3.79 | 21.87× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 17.81 | 17.95 | 0.99× |
| Darwin x86_64 | avx2 | 5.09 | 5.57 | 0.91× |
| Darwin x86_64 | generic | 15.70 | 16.04 | 0.98× |
| Darwin arm64 | generic | 15.54 | 14.67 | 1.06× |
| Linux x86_64 | avx2 | 4.37 | 4.42 | 0.99× |
| Linux x86_64 | generic | 13.41 | 13.81 | 0.97× |
| Windows AMD64 | avx2 | 5.41 | 5.56 | 0.97× |
| Windows AMD64 | generic | 15.12 | 15.32 | 0.99× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 198.85 | 193.66 | 1.03× |
| Darwin x86_64 | avx2 | 41.63 | 45.23 | 0.92× |
| Darwin x86_64 | generic | 163.39 | 154.96 | 1.05× |
| Darwin arm64 | generic | 162.38 | 155.56 | 1.04× |
| Linux x86_64 | avx2 | 46.81 | 48.91 | 0.96× |
| Linux x86_64 | generic | 176.99 | 203.09 | 0.87× |
| Windows AMD64 | avx2 | 61.41 | 67.78 | 0.91× |
| Windows AMD64 | generic | 187.67 | 192.25 | 0.98× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 4.04 | 5.24 | 0.77× |
| Darwin x86_64 | avx2 | 2.73 | 2.95 | 0.93× |
| Darwin x86_64 | generic | 7.17 | 6.68 | 1.07× |
| Darwin arm64 | generic | 5.93 | 5.48 | 1.08× |
| Linux x86_64 | avx2 | 1.03 | 1.36 | 0.76× |
| Linux x86_64 | generic | 3.73 | 4.79 | 0.78× |
| Windows AMD64 | avx2 | 1.45 | 1.97 | 0.74× |
| Windows AMD64 | generic | 4.78 | 4.71 | 1.02× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 39.75 | 25.50 | 1.56× |
| Darwin x86_64 | avx2 | 15.67 | 12.04 | 1.30× |
| Darwin x86_64 | generic | 46.11 | 28.94 | 1.59× |
| Darwin arm64 | generic | 35.84 | 24.93 | 1.44× |
| Linux x86_64 | avx2 | 9.95 | 6.96 | 1.43× |
| Linux x86_64 | generic | 33.03 | 21.70 | 1.52× |
| Windows AMD64 | avx2 | 14.88 | 10.85 | 1.37× |
| Windows AMD64 | generic | 33.53 | 25.75 | 1.30× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 12.41 | 8.93 | 1.39× |
| Darwin x86_64 | avx2 | — | 4.33 | — |
| Darwin x86_64 | generic | — | 9.85 | — |
| Darwin arm64 | generic | — | 8.32 | — |
| Linux x86_64 | avx2 | 3.74 | 2.70 | 1.39× |
| Linux x86_64 | generic | 9.80 | 7.70 | 1.27× |
| Windows AMD64 | avx2 | 5.26 | 3.97 | 1.33× |
| Windows AMD64 | generic | 10.87 | 8.18 | 1.33× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 26.30 | 21.41 | 1.23× |
| Darwin x86_64 | avx2 | 10.61 | 14.06 | 0.75× |
| Darwin x86_64 | generic | 29.34 | 31.43 | 0.93× |
| Darwin arm64 | generic | 26.20 | 26.14 | 1.00× |
| Linux x86_64 | avx2 | 7.82 | 6.77 | 1.16× |
| Linux x86_64 | generic | 21.64 | 19.37 | 1.12× |
| Windows AMD64 | avx2 | 11.25 | 10.15 | 1.11× |
| Windows AMD64 | generic | 23.22 | 22.12 | 1.05× |

### `markshare_4_0`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 102.61 | 2.29 | 44.86× |
| Darwin x86_64 | avx2 | 43.19 | 2.13 | 20.24× |
| Darwin x86_64 | generic | 103.42 | 4.35 | 23.75× |
| Darwin arm64 | generic | 58.36 | 2.52 | 23.15× |
| Linux x86_64 | avx2 | 43.38 | 0.96 | 45.36× |
| Linux x86_64 | generic | 99.72 | 3.72 | 26.81× |
| Windows AMD64 | avx2 | 32.79 | 1.23 | 26.59× |
| Windows AMD64 | generic | 81.27 | 3.04 | 26.75× |

### `irp`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 69.44 | 25.53 | 2.72× |
| Darwin x86_64 | avx2 | 19.25 | 8.14 | 2.37× |
| Darwin x86_64 | generic | 122.66 | 42.59 | 2.88× |
| Darwin arm64 | generic | 109.73 | 38.23 | 2.87× |
| Linux x86_64 | avx2 | 13.17 | 5.35 | 2.46× |
| Linux x86_64 | generic | 63.69 | 24.72 | 2.58× |
| Windows AMD64 | avx2 | 16.96 | 6.06 | 2.80× |
| Windows AMD64 | generic | 67.00 | 29.09 | 2.30× |

### `qap10`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 152.15 | 197.12 | 0.77× |
| Darwin x86_64 | avx2 | 63.80 | 39.70 | 1.61× |
| Darwin x86_64 | generic | 177.83 | 101.88 | 1.75× |
| Darwin arm64 | generic | 159.66 | 110.19 | 1.45× |
| Linux x86_64 | avx2 | 82.33 | 30.37 | 2.71× |
| Linux x86_64 | generic | 213.97 | 80.05 | 2.67× |
| Windows AMD64 | avx2 | 111.16 | 41.33 | 2.69× |
| Windows AMD64 | generic | 236.59 | 88.69 | 2.67× |

### `swath1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.77 | 93.74 | 0.51× |
| Darwin x86_64 | avx2 | 15.81 | 35.75 | 0.44× |
| Darwin x86_64 | generic | 52.76 | 106.23 | 0.50× |
| Darwin arm64 | generic | 43.52 | 93.35 | 0.47× |
| Linux x86_64 | avx2 | 11.89 | 24.08 | 0.49× |
| Linux x86_64 | generic | 40.38 | 89.11 | 0.45× |
| Windows AMD64 | avx2 | 14.72 | 32.74 | 0.45× |
| Windows AMD64 | generic | 43.26 | 81.67 | 0.53× |

### `physiciansched6-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 39.00 | 31.24 | 1.25× |
| Darwin x86_64 | avx2 | 11.03 | 9.53 | 1.16× |
| Darwin x86_64 | generic | 75.02 | 81.80 | 0.92× |
| Darwin arm64 | generic | 49.06 | 52.83 | 0.93× |
| Linux x86_64 | avx2 | 13.86 | 11.26 | 1.23× |
| Linux x86_64 | generic | 31.52 | 26.07 | 1.21× |
| Windows AMD64 | avx2 | 19.33 | 16.33 | 1.18× |
| Windows AMD64 | generic | 63.62 | 62.92 | 1.01× |

### `mzzv42z`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 207.50 | 185.20 | 1.12× |
| Darwin x86_64 | avx2 | 87.93 | 98.75 | 0.89× |
| Darwin x86_64 | generic | 207.77 | 237.50 | 0.87× |
| Darwin arm64 | generic | 199.72 | 223.27 | 0.89× |
| Linux x86_64 | avx2 | 62.22 | 52.80 | 1.18× |
| Linux x86_64 | generic | 167.79 | 147.51 | 1.14× |
| Windows AMD64 | avx2 | 86.57 | 80.14 | 1.08× |
| Windows AMD64 | generic | 175.74 | 169.49 | 1.04× |

### `neos-860300`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 438.23 | 132.62 | 3.30× |
| Darwin x86_64 | avx2 | 157.81 | 40.77 | 3.87× |
| Darwin x86_64 | generic | 377.11 | 102.18 | 3.69× |
| Darwin arm64 | generic | 350.62 | 102.96 | 3.41× |
| Linux x86_64 | avx2 | 115.68 | 36.23 | 3.19× |
| Linux x86_64 | generic | 354.87 | 128.11 | 2.77× |
| Windows AMD64 | avx2 | 177.59 | 56.60 | 3.14× |
| Windows AMD64 | generic | 112.19 | 67.65 | 1.66× |


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

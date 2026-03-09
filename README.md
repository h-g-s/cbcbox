# cbcbox

[![PyPI version](https://img.shields.io/pypi/v/cbcbox.svg?color=brightgreen)](https://pypi.org/project/cbcbox/)
[![PyPI downloads](https://img.shields.io/pypi/dm/cbcbox.svg?color=blue)](https://pypi.org/project/cbcbox/)
[![CI](https://github.com/h-g-s/cbcbox/actions/workflows/wheel.yml/badge.svg)](https://github.com/h-g-s/cbcbox/actions/workflows/wheel.yml)
[![Platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20macOS%20%7C%20Windows-informational)](https://pypi.org/project/cbcbox/)
[![License](https://img.shields.io/badge/license-EPL--2.0-blue.svg)](https://opensource.org/licenses/EPL-2.0)

**cbcbox** is a high-performance, self-contained Python distribution of the
[CBC](https://github.com/coin-or/Cbc) MILP solver (COIN-OR Branch and Cut),
built from the latest COIN-OR master branch.

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

The AVX2/Haswell build is **~3.4×** faster than the generic build on average (geometric mean across 23 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

<!-- PERF_SPEEDUP_END -->

<!-- PERF_PLOT_START -->

![CBC solve time — generic vs AVX2/Haswell (Linux x86_64)](https://raw.githubusercontent.com/h-g-s/cbcbox/master/docs/perf_avx2_speedup.png)

*Single-threaded solve time across benchmark instances on Linux x86_64, sorted by solve time. Speedup factor shown above each pair. Lower is better.*

See also: [Windows AMD64 + macOS x86_64 summary](https://raw.githubusercontent.com/h-g-s/cbcbox/master/docs/perf_avx2_other.png)

<!-- PERF_PLOT_END -->

## Build variants

On **x86_64 Linux, macOS, and Windows**, the wheel ships two complete sets of binaries:

| Variant | OpenBLAS kernel | Clp SIMD | Minimum CPU |
|---|---|---|---|
| `generic` | `DYNAMIC_ARCH=1` (runtime dispatch, Nehalem–Zen targets) | standard | any x86_64 |
| `avx2` | `DYNAMIC_ARCH=1` + `DYNAMIC_LIST=HASWELL SKYLAKEX` | `-march=haswell -DCOIN_AVX2=4` | Haswell (2013+) |

At import time `cbcbox` automatically selects `avx2` when it is available **and**
the running CPU supports AVX2; otherwise it falls back to `generic`.

You can override this selection with the `CBCBOX_BUILD` environment variable:

```bash
# Force generic (portable) build
CBCBOX_BUILD=generic cbc mymodel.mps -solve -quit

# Force AVX2-optimised build (raises an error if not available)
CBCBOX_BUILD=avx2 cbc mymodel.mps -solve -quit
```

When `CBCBOX_BUILD` is set, a short summary of the selected build is printed to
stdout on every call — useful for tagging experiment results:

```
[cbcbox] CBCBOX_BUILD=avx2
[cbcbox]   binary  : .../cbcbox/cbc_dist_avx2/bin/cbc
[cbcbox]   lib dir : .../cbcbox/cbc_dist_avx2/lib
[cbcbox]   libs    : libCbc.so.3, libClp.so.3, libopenblas.so.0
```

> **Non-x86_64 platforms** (Linux aarch64, macOS arm64) ship the `generic`
> build only.  `CBCBOX_BUILD=avx2` will raise a `RuntimeError` on those
> platforms.

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
| **[Nauty](https://pallini.di.uniroma1.it/)** | 2.8.9 | Symmetry detection for MIP presolve |
| **[AMD](https://github.com/DrTimothyAldenDavis/SuiteSparse)** (SuiteSparse v7.12.2) | v7.12.2 | Sparse matrix fill-reducing ordering |
| **[OpenBLAS](https://github.com/OpenMathLib/OpenBLAS)** | v0.3.31 | Optimised BLAS/LAPACK for LP basis factorisation |

On x86_64 Linux, macOS, and Windows the entire stack is compiled **twice**: once for the
`generic` variant (OpenBLAS `DYNAMIC_ARCH=1` with a broad set of x86_64 targets for
runtime dispatch) and once for the `avx2` variant (OpenBLAS `DYNAMIC_ARCH=1` restricted
to Haswell/Skylake targets via `DYNAMIC_LIST`, COIN-OR compiled with
`-march=haswell -DCOIN_AVX2=4`). Both variants use `NO_CBLAS=1` (COIN-OR only calls
the Fortran BLAS interface). AMD and Nauty are built only once (they are pure
combinatorial code with no BLAS dependency) and reused by both COIN-OR variants.

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
    ├── nauty/     # Nauty headers
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

The test suite (`pytest`) solves 23 MIP instances and checks the optimal
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
| Linux aarch64 | 44.95 | — | — |
| Darwin x86_64 | 67.58 | 19.61 | 3.45× |
| Darwin arm64 | 38.70 | — | — |
| Linux x86_64 | 49.14 | 14.23 | 3.45× |
| Windows AMD64 | 52.84 | 16.03 | 3.30× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 32.14 | — | — |
| Darwin x86_64 | 48.50 | 18.39 | 2.64× |
| Darwin arm64 | 34.75 | — | — |
| Linux x86_64 | 40.14 | 12.27 | 3.27× |
| Windows AMD64 | 40.00 | 14.96 | 2.67× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 8.88 | 5.69 | 1.56× |
| Darwin x86_64 | avx2 | 5.46 | 12.87 | 0.42× |
| Darwin x86_64 | generic | 9.48 | 8.49 | 1.12× |
| Darwin arm64 | generic | 9.49 | 17.26 | 0.55× |
| Linux x86_64 | avx2 | 4.50 | 8.64 | 0.52× |
| Linux x86_64 | generic | 9.84 | 8.37 | 1.17× |
| Windows AMD64 | avx2 | 4.87 | 8.71 | 0.56× |
| Windows AMD64 | generic | 14.37 | 23.81 | 0.60× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 218.40 | 195.49 | 1.12× |
| Darwin x86_64 | avx2 | 67.19 | 61.68 | 1.09× |
| Darwin x86_64 | generic | 199.32 | 181.98 | 1.10× |
| Darwin arm64 | generic | 131.76 | 115.38 | 1.14× |
| Linux x86_64 | avx2 | 56.03 | 51.97 | 1.08× |
| Linux x86_64 | generic | 241.19 | 211.55 | 1.14× |
| Windows AMD64 | avx2 | 56.96 | 57.06 | 1.00× |
| Windows AMD64 | generic | 248.30 | 213.89 | 1.16× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.55 | 5.66 | 0.98× |
| Darwin x86_64 | avx2 | 1.98 | 2.09 | 0.95× |
| Darwin x86_64 | generic | 6.57 | 6.78 | 0.97× |
| Darwin arm64 | generic | 5.22 | 3.91 | 1.33× |
| Linux x86_64 | avx2 | 2.03 | 2.07 | 0.98× |
| Linux x86_64 | generic | 6.18 | 6.40 | 0.97× |
| Windows AMD64 | avx2 | 2.27 | 2.46 | 0.92× |
| Windows AMD64 | generic | 5.94 | 6.14 | 0.97× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 138.87 | 78.75 | 1.76× |
| Darwin x86_64 | avx2 | 62.29 | 40.66 | 1.53× |
| Darwin x86_64 | generic | 127.04 | 82.25 | 1.54× |
| Darwin arm64 | generic | 136.37 | 89.53 | 1.52× |
| Linux x86_64 | avx2 | 34.05 | 24.91 | 1.37× |
| Linux x86_64 | generic | 152.67 | 90.55 | 1.69× |
| Windows AMD64 | avx2 | 32.44 | 27.49 | 1.18× |
| Windows AMD64 | generic | 154.08 | 116.35 | 1.32× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 50.83 | 33.98 | 1.50× |
| Darwin x86_64 | avx2 | 29.29 | 25.02 | 1.17× |
| Darwin x86_64 | generic | 65.29 | 45.03 | 1.45× |
| Darwin arm64 | generic | 65.48 | 33.64 | 1.95× |
| Linux x86_64 | avx2 | 15.09 | 12.64 | 1.19× |
| Linux x86_64 | generic | 57.41 | 42.01 | 1.37× |
| Windows AMD64 | avx2 | 17.49 | 14.36 | 1.22× |
| Windows AMD64 | generic | 57.45 | 40.82 | 1.41× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 39.78 | 40.94 | 0.97× |
| Darwin x86_64 | avx2 | 16.61 | 16.04 | 1.04× |
| Darwin x86_64 | generic | 42.25 | 37.94 | 1.11× |
| Darwin arm64 | generic | 37.57 | 37.48 | 1.00× |
| Linux x86_64 | avx2 | 11.45 | 11.90 | 0.96× |
| Linux x86_64 | generic | 57.36 | 55.54 | 1.03× |
| Windows AMD64 | avx2 | 15.34 | 16.20 | 0.95× |
| Windows AMD64 | generic | 57.91 | 55.79 | 1.04× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 208.54 | 180.52 | 1.16× |
| Darwin x86_64 | avx2 | 159.01 | 97.62 | 1.63× |
| Darwin x86_64 | generic | 614.40 | 437.75 | 1.40× |
| Darwin arm64 | generic | 293.99 | 160.05 | 1.84× |
| Linux x86_64 | avx2 | 131.93 | 121.62 | 1.08× |
| Linux x86_64 | generic | 221.06 | 222.27 | 0.99× |
| Windows AMD64 | avx2 | 119.31 | 175.96 | 0.68× |
| Windows AMD64 | generic | 256.81 | 281.98 | 0.91× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 204.74 | 202.93 | 1.01× |
| Darwin x86_64 | avx2 | 121.04 | 119.91 | 1.01× |
| Darwin x86_64 | generic | 289.13 | 245.05 | 1.18× |
| Darwin arm64 | generic | 235.55 | 175.69 | 1.34× |
| Linux x86_64 | avx2 | 78.80 | 73.22 | 1.08× |
| Linux x86_64 | generic | 217.72 | 216.28 | 1.01× |
| Windows AMD64 | avx2 | 102.81 | 120.95 | 0.85× |
| Windows AMD64 | generic | 235.45 | 228.21 | 1.03× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 99.41 | 72.18 | 1.38× |
| Darwin x86_64 | avx2 | 39.39 | 36.30 | 1.09× |
| Darwin x86_64 | generic | 107.63 | 104.84 | 1.03× |
| Darwin arm64 | generic | 98.68 | 102.31 | 0.96× |
| Linux x86_64 | avx2 | 25.41 | 25.60 | 0.99× |
| Linux x86_64 | generic | 109.29 | 82.66 | 1.32× |
| Windows AMD64 | avx2 | 26.53 | 26.17 | 1.01× |
| Windows AMD64 | generic | 111.88 | 84.25 | 1.33× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 24.08 | 12.35 | 1.95× |
| Darwin x86_64 | avx2 | 10.99 | 8.18 | 1.34× |
| Darwin x86_64 | generic | 29.56 | 21.81 | 1.36× |
| Darwin arm64 | generic | 20.47 | 17.06 | 1.20× |
| Linux x86_64 | avx2 | 8.33 | 6.77 | 1.23× |
| Linux x86_64 | generic | 26.42 | 17.33 | 1.52× |
| Windows AMD64 | avx2 | 8.38 | 6.70 | 1.25× |
| Windows AMD64 | generic | 26.30 | 17.63 | 1.49× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 33.71 | 31.85 | 1.06× |
| Darwin x86_64 | avx2 | 16.38 | 14.87 | 1.10× |
| Darwin x86_64 | generic | 51.33 | 43.31 | 1.19× |
| Darwin arm64 | generic | 44.53 | 34.54 | 1.29× |
| Linux x86_64 | avx2 | 20.41 | 20.00 | 1.02× |
| Linux x86_64 | generic | 36.17 | 36.54 | 0.99× |
| Windows AMD64 | avx2 | 12.99 | 12.78 | 1.02× |
| Windows AMD64 | generic | 35.66 | 37.35 | 0.95× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 31.46 | 15.74 | 2.00× |
| Darwin x86_64 | avx2 | 22.60 | 10.15 | 2.23× |
| Darwin x86_64 | generic | 138.10 | 14.79 | 9.34× |
| Darwin arm64 | generic | 43.05 | 22.18 | 1.94× |
| Linux x86_64 | avx2 | 20.46 | 7.33 | 2.79× |
| Linux x86_64 | generic | 33.31 | 17.16 | 1.94× |
| Windows AMD64 | avx2 | 13.67 | 16.53 | 0.83× |
| Windows AMD64 | generic | 36.04 | 16.89 | 2.13× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.30 | 6.04 | 1.04× |
| Darwin x86_64 | avx2 | 4.93 | 4.76 | 1.03× |
| Darwin x86_64 | generic | 8.70 | 7.52 | 1.16× |
| Darwin arm64 | generic | 9.55 | 8.64 | 1.11× |
| Linux x86_64 | avx2 | 2.19 | 2.10 | 1.05× |
| Linux x86_64 | generic | 6.90 | 7.01 | 0.98× |
| Windows AMD64 | avx2 | 2.16 | 2.23 | 0.97× |
| Windows AMD64 | generic | 8.35 | 7.12 | 1.17× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 59.71 | 24.64 | 2.42× |
| Darwin x86_64 | avx2 | 52.81 | 17.85 | 2.96× |
| Darwin x86_64 | generic | 75.63 | 24.88 | 3.04× |
| Darwin arm64 | generic | 87.49 | 32.92 | 2.66× |
| Linux x86_64 | avx2 | 33.34 | 11.34 | 2.94× |
| Linux x86_64 | generic | 63.07 | 36.23 | 1.74× |
| Windows AMD64 | avx2 | 24.02 | 11.54 | 2.08× |
| Windows AMD64 | generic | 79.43 | 42.71 | 1.86× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 10.16 | 9.23 | 1.10× |
| Darwin x86_64 | avx2 | 5.99 | 6.61 | 0.91× |
| Darwin x86_64 | generic | 15.55 | 11.25 | 1.38× |
| Darwin arm64 | generic | 9.18 | 11.35 | 0.81× |
| Linux x86_64 | avx2 | 3.15 | 3.02 | 1.04× |
| Linux x86_64 | generic | 10.60 | 10.46 | 1.01× |
| Windows AMD64 | avx2 | 3.38 | 3.23 | 1.05× |
| Windows AMD64 | generic | 11.03 | 10.62 | 1.04× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 89.48 | 54.14 | 1.65× |
| Darwin x86_64 | avx2 | 44.07 | 48.28 | 0.91× |
| Darwin x86_64 | generic | 107.94 | 72.52 | 1.49× |
| Darwin arm64 | generic | 63.35 | 58.12 | 1.09× |
| Linux x86_64 | avx2 | 33.72 | 27.07 | 1.25× |
| Linux x86_64 | generic | 102.73 | 70.02 | 1.47× |
| Windows AMD64 | avx2 | 33.48 | 33.08 | 1.01× |
| Windows AMD64 | generic | 104.45 | 67.48 | 1.55× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 49.23 | 43.93 | 1.12× |
| Darwin x86_64 | avx2 | 24.48 | 55.21 | 0.44× |
| Darwin x86_64 | generic | 64.01 | 74.03 | 0.86× |
| Darwin arm64 | generic | 40.23 | 71.73 | 0.56× |
| Linux x86_64 | avx2 | 19.16 | 31.11 | 0.62× |
| Linux x86_64 | generic | 53.78 | 63.85 | 0.84× |
| Windows AMD64 | avx2 | 19.66 | 38.75 | 0.51× |
| Windows AMD64 | generic | 54.73 | 65.80 | 0.83× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 37.52 | 43.74 | 0.86× |
| Darwin x86_64 | avx2 | 7.82 | 10.44 | 0.75× |
| Darwin x86_64 | generic | 820.82 | 519.90 | 1.58× |
| Darwin arm64 | generic | 13.42 | 44.85 | 0.30× |
| Linux x86_64 | avx2 | 9.39 | 10.56 | 0.89× |
| Linux x86_64 | generic | 36.04 | 191.21 | 0.19× |
| Windows AMD64 | avx2 | 20.81 | 7.02 | 2.96× |
| Windows AMD64 | generic | 84.30 | 23.93 | 3.52× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.38 | 55.04 | 2.48× |
| Darwin x86_64 | avx2 | 46.83 | 26.98 | 1.74× |
| Darwin x86_64 | generic | 193.67 | 92.11 | 2.10× |
| Darwin arm64 | generic | 112.76 | 75.51 | 1.49× |
| Linux x86_64 | avx2 | 46.22 | 22.81 | 2.03× |
| Linux x86_64 | generic | 163.38 | 71.58 | 2.28× |
| Windows AMD64 | avx2 | 31.24 | 19.75 | 1.58× |
| Windows AMD64 | generic | 167.91 | 74.13 | 2.26× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 4.39 | 4.55 | 0.97× |
| Darwin x86_64 | avx2 | 1.34 | 1.57 | 0.85× |
| Darwin x86_64 | generic | 9.41 | 8.41 | 1.12× |
| Darwin arm64 | generic | 2.08 | 2.26 | 0.92× |
| Linux x86_64 | avx2 | 0.74 | 0.70 | 1.05× |
| Linux x86_64 | generic | 4.92 | 5.16 | 0.95× |
| Windows AMD64 | avx2 | 2.00 | 2.02 | 0.99× |
| Windows AMD64 | generic | 4.06 | 4.38 | 0.93× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 101.12 | 101.07 | 1.00× |
| Darwin x86_64 | avx2 | 26.18 | 30.82 | 0.85× |
| Darwin x86_64 | generic | 150.37 | 130.43 | 1.15× |
| Darwin arm64 | generic | 78.78 | 93.41 | 0.84× |
| Linux x86_64 | avx2 | 18.23 | 18.19 | 1.00× |
| Linux x86_64 | generic | 111.50 | 109.28 | 1.02× |
| Windows AMD64 | avx2 | 24.73 | 24.72 | 1.00× |
| Windows AMD64 | generic | 79.85 | 79.91 | 1.00× |

### `neos-827175`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 43.33 | 43.76 | 0.99× |
| Darwin x86_64 | avx2 | 17.22 | 23.50 | 0.73× |
| Darwin x86_64 | generic | 66.90 | 56.84 | 1.18× |
| Darwin arm64 | generic | 31.54 | 37.91 | 0.83× |
| Linux x86_64 | avx2 | 13.41 | 13.62 | 0.98× |
| Linux x86_64 | generic | 38.67 | 38.91 | 0.99× |
| Windows AMD64 | avx2 | 12.44 | 12.30 | 1.01× |
| Windows AMD64 | generic | 41.18 | 41.89 | 0.98× |

### `neos-3083819-nubu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 189.94 | 25.66 | 7.40× |
| Darwin x86_64 | avx2 | 21.22 | 18.02 | 1.18× |
| Darwin x86_64 | generic | 65.74 | 75.66 | 0.87× |
| Darwin arm64 | generic | 36.64 | 23.02 | 1.59× |
| Linux x86_64 | avx2 | 10.27 | 5.54 | 1.85× |
| Linux x86_64 | generic | 203.62 | 20.61 | 9.88× |
| Windows AMD64 | avx2 | 42.05 | 18.85 | 2.23× |
| Windows AMD64 | generic | 215.55 | 37.72 | 5.71× |


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

The released wheels are fully optimised and stripped.  To debug CBC itself
(e.g. with GDB or LLDB), use the scripts in `scripts/` to build a local
debug-enabled binary.  These produce the same full feature set as the release
wheels (OpenBLAS, AMD, Nauty, pthreads) but compiled with `-O1 -g` and, on
x86_64, with `-march=haswell -DCOIN_AVX2=4` so you can debug AVX2-specific
code paths.

| Script | Platform | Environment | Output directory |
|---|---|---|---|
| `scripts/build_debug.sh` | Linux, macOS | native (host compiler) | `cbc_dist_debug_avx2/` (x86_64) or `cbc_dist_debug/` (ARM64) |
| `scripts/build_debug_manylinux.sh` | Linux | Docker — manylinux2014 container (exact CI parity) | same as above |
| `scripts/build_debug_windows.ps1` | Windows | MSYS2 / MinGW64 | `cbc_dist_debug_avx2\` |

### Quick start

**Linux / macOS (native build):**

```bash
# x86_64 → debug + AVX2 → cbc_dist_debug_avx2/bin/cbc
# ARM64  → debug only  → cbc_dist_debug/bin/cbc
./scripts/build_debug.sh

# With AddressSanitizer:
./scripts/build_debug.sh --asan

# With ThreadSanitizer:
./scripts/build_debug.sh --tsan

# Force a clean rebuild from scratch (required when switching sanitizers):
./scripts/build_debug.sh --asan --clean
```

**Linux (manylinux2014 container — matches CI exactly):**

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

| Sanitizer | Flag | What it catches | Runtime env var |
|---|---|---|---|
| AddressSanitizer | `--asan` | heap/stack buffer overflows, use-after-free, memory leaks | `ASAN_OPTIONS=detect_leaks=0` to suppress system-lib false positives |
| ThreadSanitizer  | `--tsan` | data races between threads | `TSAN_OPTIONS=halt_on_error=0` to log races without aborting |

ASan and TSan are mutually exclusive.  Neither is available on Windows/MinGW.
Always pass `--clean` when switching from one sanitizer to another to avoid
linking mismatched object files.

OpenBLAS is always built **without** sanitizer flags to avoid false positives
from hand-optimised BLAS assembly; only the COIN-OR stack is instrumented.

> **Note:** Debug binaries are not included in the published wheels because
> of their size.  They are intended for local development only.

## License

CBC and all COIN-OR components are distributed under the
[Eclipse Public License 2.0](https://opensource.org/licenses/EPL-2.0).
OpenBLAS is distributed under the BSD 3-Clause licence.
SuiteSparse AMD is distributed under the BSD 3-Clause licence.
Nauty is distributed under the Apache 2.0 licence.


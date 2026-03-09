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

The AVX2/Haswell build is **~3.2×** faster than the generic build on average (geometric mean across 21 instances, 3 x86_64 platforms: Darwin x86_64, Linux x86_64, Windows AMD64).

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

The test suite (`pytest`) solves 21 MIP instances and checks the optimal
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
| Linux aarch64 | 41.80 | — | — |
| Darwin x86_64 | 67.20 | 19.63 | 3.42× |
| Darwin arm64 | 40.36 | — | — |
| Linux x86_64 | 46.56 | 14.44 | 3.22× |
| Windows AMD64 | 49.52 | 16.46 | 3.01× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Linux aarch64 | 32.04 | — | — |
| Darwin x86_64 | 54.10 | 17.93 | 3.02× |
| Darwin arm64 | 32.45 | — | — |
| Linux x86_64 | 39.40 | 12.73 | 3.09× |
| Windows AMD64 | 39.70 | 15.03 | 2.64× |

## Per-instance results

### `pp08a`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 8.98 | 5.73 | 1.57× |
| Darwin x86_64 | avx2 | 5.60 | 13.52 | 0.41× |
| Darwin x86_64 | generic | 11.43 | 14.72 | 0.78× |
| Darwin arm64 | generic | 10.61 | 20.90 | 0.51× |
| Linux x86_64 | avx2 | 4.48 | 7.03 | 0.64× |
| Linux x86_64 | generic | 9.83 | 8.31 | 1.18× |
| Windows AMD64 | avx2 | 5.23 | 8.31 | 0.63× |
| Windows AMD64 | generic | 12.22 | 19.50 | 0.63× |

### `sprint_hidden06_j`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 219.78 | 198.73 | 1.11× |
| Darwin x86_64 | avx2 | 59.96 | 59.73 | 1.00× |
| Darwin x86_64 | generic | 209.26 | 221.22 | 0.95× |
| Darwin arm64 | generic | 147.51 | 139.47 | 1.06× |
| Linux x86_64 | avx2 | 55.95 | 54.90 | 1.02× |
| Linux x86_64 | generic | 241.13 | 204.83 | 1.18× |
| Windows AMD64 | avx2 | 61.36 | 58.74 | 1.04× |
| Windows AMD64 | generic | 261.81 | 220.33 | 1.19× |

### `air03`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 5.65 | 5.70 | 0.99× |
| Darwin x86_64 | avx2 | 1.97 | 2.28 | 0.86× |
| Darwin x86_64 | generic | 6.75 | 7.66 | 0.88× |
| Darwin arm64 | generic | 5.52 | 4.63 | 1.19× |
| Linux x86_64 | avx2 | 2.01 | 2.08 | 0.97× |
| Linux x86_64 | generic | 6.24 | 6.51 | 0.96× |
| Windows AMD64 | avx2 | 2.49 | 2.57 | 0.97× |
| Windows AMD64 | generic | 6.45 | 6.64 | 0.97× |

### `air04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 139.44 | 74.15 | 1.88× |
| Darwin x86_64 | avx2 | 62.41 | 41.08 | 1.52× |
| Darwin x86_64 | generic | 128.82 | 86.31 | 1.49× |
| Darwin arm64 | generic | 125.46 | 98.65 | 1.27× |
| Linux x86_64 | avx2 | 34.12 | 29.31 | 1.16× |
| Linux x86_64 | generic | 152.90 | 129.24 | 1.18× |
| Windows AMD64 | avx2 | 34.79 | 27.96 | 1.24× |
| Windows AMD64 | generic | 151.71 | 106.73 | 1.42× |

### `air05`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 51.06 | 34.99 | 1.46× |
| Darwin x86_64 | avx2 | 28.66 | 24.84 | 1.15× |
| Darwin x86_64 | generic | 63.42 | 51.50 | 1.23× |
| Darwin arm64 | generic | 61.02 | 39.00 | 1.56× |
| Linux x86_64 | avx2 | 15.16 | 12.17 | 1.25× |
| Linux x86_64 | generic | 57.52 | 42.92 | 1.34× |
| Windows AMD64 | avx2 | 18.88 | 14.46 | 1.31× |
| Windows AMD64 | generic | 58.82 | 42.64 | 1.38× |

### `nw04`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 40.17 | 40.64 | 0.99× |
| Darwin x86_64 | avx2 | 15.01 | 15.98 | 0.94× |
| Darwin x86_64 | generic | 39.70 | 44.31 | 0.90× |
| Darwin arm64 | generic | 39.55 | 40.68 | 0.97× |
| Linux x86_64 | avx2 | 11.52 | 11.92 | 0.97× |
| Linux x86_64 | generic | 57.59 | 54.92 | 1.05× |
| Windows AMD64 | avx2 | 16.70 | 17.11 | 0.98× |
| Windows AMD64 | generic | 67.71 | 56.34 | 1.20× |

### `mzzv11`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 209.74 | 176.10 | 1.19× |
| Darwin x86_64 | avx2 | 147.80 | 105.31 | 1.40× |
| Darwin x86_64 | generic | 581.52 | 442.96 | 1.31× |
| Darwin arm64 | generic | 291.02 | 201.27 | 1.45× |
| Linux x86_64 | avx2 | 131.83 | 113.89 | 1.16× |
| Linux x86_64 | generic | 219.97 | 225.07 | 0.98× |
| Windows AMD64 | avx2 | 123.67 | 196.76 | 0.63× |
| Windows AMD64 | generic | 267.79 | 266.34 | 1.01× |

### `trd445c`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 204.79 | 200.11 | 1.02× |
| Darwin x86_64 | avx2 | 127.46 | 122.70 | 1.04× |
| Darwin x86_64 | generic | 242.73 | 248.65 | 0.98× |
| Darwin arm64 | generic | 213.18 | 180.36 | 1.18× |
| Linux x86_64 | avx2 | 77.30 | 73.14 | 1.06× |
| Linux x86_64 | generic | 220.86 | 218.93 | 1.01× |
| Windows AMD64 | avx2 | 111.67 | 118.71 | 0.94× |
| Windows AMD64 | generic | 247.68 | 246.32 | 1.01× |

### `nursesched-sprint02`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 98.79 | 72.48 | 1.36× |
| Darwin x86_64 | avx2 | 38.49 | 39.16 | 0.98× |
| Darwin x86_64 | generic | 106.93 | 112.11 | 0.95× |
| Darwin arm64 | generic | 99.26 | 86.85 | 1.14× |
| Linux x86_64 | avx2 | 25.24 | 25.08 | 1.01× |
| Linux x86_64 | generic | 109.71 | 82.07 | 1.34× |
| Windows AMD64 | avx2 | 28.61 | 28.73 | 1.00× |
| Windows AMD64 | generic | 112.86 | 86.20 | 1.31× |

### `stein45`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 23.79 | 12.86 | 1.85× |
| Darwin x86_64 | avx2 | 10.75 | 9.79 | 1.10× |
| Darwin x86_64 | generic | 29.99 | 19.06 | 1.57× |
| Darwin arm64 | generic | 23.03 | 11.77 | 1.96× |
| Linux x86_64 | avx2 | 8.28 | 7.00 | 1.18× |
| Linux x86_64 | generic | 26.45 | 17.26 | 1.53× |
| Windows AMD64 | avx2 | 8.89 | 6.23 | 1.43× |
| Windows AMD64 | generic | 25.71 | 15.97 | 1.61× |

### `neos-810286`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 33.70 | 32.05 | 1.05× |
| Darwin x86_64 | avx2 | 15.59 | 17.12 | 0.91× |
| Darwin x86_64 | generic | 51.53 | 49.08 | 1.05× |
| Darwin arm64 | generic | 34.88 | 34.82 | 1.00× |
| Linux x86_64 | avx2 | 20.32 | 20.13 | 1.01× |
| Linux x86_64 | generic | 36.23 | 37.31 | 0.97× |
| Windows AMD64 | avx2 | 13.65 | 13.34 | 1.02× |
| Windows AMD64 | generic | 35.96 | 39.19 | 0.92× |

### `neos-1281048`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 31.39 | 15.90 | 1.97× |
| Darwin x86_64 | avx2 | 22.50 | 8.57 | 2.63× |
| Darwin x86_64 | generic | 139.45 | 18.07 | 7.72× |
| Darwin arm64 | generic | 47.71 | 16.89 | 2.83× |
| Linux x86_64 | avx2 | 20.46 | 8.08 | 2.53× |
| Linux x86_64 | generic | 33.35 | 28.16 | 1.18× |
| Windows AMD64 | avx2 | 14.83 | 12.69 | 1.17× |
| Windows AMD64 | generic | 35.13 | 18.46 | 1.90× |

### `j3050_8`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 6.20 | 6.05 | 1.03× |
| Darwin x86_64 | avx2 | 5.16 | 4.19 | 1.23× |
| Darwin x86_64 | generic | 9.13 | 9.58 | 0.95× |
| Darwin arm64 | generic | 10.71 | 6.77 | 1.58× |
| Linux x86_64 | avx2 | 2.16 | 2.07 | 1.04× |
| Linux x86_64 | generic | 6.94 | 6.76 | 1.03× |
| Windows AMD64 | avx2 | 2.29 | 2.56 | 0.89× |
| Windows AMD64 | generic | 8.33 | 6.77 | 1.23× |

### `qiu`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 59.23 | 24.78 | 2.39× |
| Darwin x86_64 | avx2 | 53.62 | 15.99 | 3.35× |
| Darwin x86_64 | generic | 76.96 | 34.71 | 2.22× |
| Darwin arm64 | generic | 89.20 | 30.41 | 2.93× |
| Linux x86_64 | avx2 | 33.31 | 11.36 | 2.93× |
| Linux x86_64 | generic | 63.03 | 33.06 | 1.91× |
| Windows AMD64 | avx2 | 24.72 | 12.19 | 2.03× |
| Windows AMD64 | generic | 71.13 | 42.05 | 1.69× |

### `gesa2-o`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 9.97 | 9.00 | 1.11× |
| Darwin x86_64 | avx2 | 5.79 | 5.47 | 1.06× |
| Darwin x86_64 | generic | 14.99 | 11.69 | 1.28× |
| Darwin arm64 | generic | 9.13 | 9.68 | 0.94× |
| Linux x86_64 | avx2 | 3.16 | 2.96 | 1.06× |
| Linux x86_64 | generic | 10.70 | 10.37 | 1.03× |
| Windows AMD64 | avx2 | 3.63 | 3.52 | 1.03× |
| Windows AMD64 | generic | 10.72 | 11.77 | 0.91× |

### `pk1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 87.17 | 42.35 | 2.06× |
| Darwin x86_64 | avx2 | 42.68 | 44.71 | 0.95× |
| Darwin x86_64 | generic | 109.14 | 81.27 | 1.34× |
| Darwin arm64 | generic | 66.82 | 54.28 | 1.23× |
| Linux x86_64 | avx2 | 33.25 | 31.48 | 1.06× |
| Linux x86_64 | generic | 104.03 | 65.67 | 1.58× |
| Windows AMD64 | avx2 | 35.42 | 27.20 | 1.30× |
| Windows AMD64 | generic | 96.90 | 71.61 | 1.35× |

### `mas76`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 47.07 | 47.88 | 0.98× |
| Darwin x86_64 | avx2 | 22.76 | 52.29 | 0.44× |
| Darwin x86_64 | generic | 64.37 | 85.43 | 0.75× |
| Darwin arm64 | generic | 41.37 | 59.64 | 0.69× |
| Linux x86_64 | avx2 | 19.01 | 29.45 | 0.65× |
| Linux x86_64 | generic | 53.91 | 63.34 | 0.85× |
| Windows AMD64 | avx2 | 20.26 | 36.84 | 0.55× |
| Windows AMD64 | generic | 51.41 | 63.11 | 0.81× |

### `app1-1`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 36.47 | 52.24 | 0.70× |
| Darwin x86_64 | avx2 | 7.13 | 9.20 | 0.78× |
| Darwin x86_64 | generic | 841.38 | 687.43 | 1.22× |
| Darwin arm64 | generic | 13.49 | 16.99 | 0.79× |
| Linux x86_64 | avx2 | 9.43 | 12.15 | 0.78× |
| Linux x86_64 | generic | 36.22 | 29.51 | 1.23× |
| Windows AMD64 | avx2 | 21.40 | 6.59 | 3.25× |
| Windows AMD64 | generic | 77.66 | 22.50 | 3.45× |

### `eil33-2`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 136.04 | 56.78 | 2.40× |
| Darwin x86_64 | avx2 | 50.10 | 28.41 | 1.76× |
| Darwin x86_64 | generic | 192.88 | 102.69 | 1.88× |
| Darwin arm64 | generic | 121.53 | 64.31 | 1.89× |
| Linux x86_64 | avx2 | 46.04 | 19.89 | 2.31× |
| Linux x86_64 | generic | 163.78 | 78.72 | 2.08× |
| Windows AMD64 | avx2 | 33.37 | 18.76 | 1.78× |
| Windows AMD64 | generic | 159.89 | 63.94 | 2.50× |

### `fiber`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 4.34 | 4.47 | 0.97× |
| Darwin x86_64 | avx2 | 1.65 | 1.57 | 1.05× |
| Darwin x86_64 | generic | 8.16 | 9.02 | 0.91× |
| Darwin arm64 | generic | 2.43 | 2.04 | 1.19× |
| Linux x86_64 | avx2 | 0.74 | 0.70 | 1.06× |
| Linux x86_64 | generic | 4.90 | 5.22 | 0.94× |
| Windows AMD64 | avx2 | 2.03 | 2.30 | 0.88× |
| Windows AMD64 | generic | 3.95 | 4.32 | 0.91× |

### `neos-2987310-joes`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Linux aarch64 | generic | 100.28 | 100.52 | 1.00× |
| Darwin x86_64 | avx2 | 31.88 | 27.62 | 1.15× |
| Darwin x86_64 | generic | 141.94 | 141.65 | 1.00× |
| Darwin arm64 | generic | 89.50 | 81.97 | 1.09× |
| Linux x86_64 | avx2 | 18.29 | 18.06 | 1.01× |
| Linux x86_64 | generic | 109.70 | 110.51 | 0.99× |
| Windows AMD64 | avx2 | 26.65 | 26.85 | 0.99× |
| Windows AMD64 | generic | 82.81 | 83.45 | 0.99× |


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

## License

CBC and all COIN-OR components are distributed under the
[Eclipse Public License 2.0](https://opensource.org/licenses/EPL-2.0).
OpenBLAS is distributed under the BSD 3-Clause licence.
SuiteSparse AMD is distributed under the BSD 3-Clause licence.
Nauty is distributed under the Apache 2.0 licence.


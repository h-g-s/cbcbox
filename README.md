# cbcbox

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

<!-- PERF_PLOT_START -->

![CBC solve time — generic vs AVX2/Haswell (Linux x86_64)](https://raw.githubusercontent.com/h-g-s/cbcbox/master/docs/perf_avx2_speedup.png)

*Single-threaded solve time across benchmark instances on Linux x86_64. Speedup factor shown above each pair. Lower is better.*

See also: [Windows AMD64 + macOS x86\_64 summary](https://raw.githubusercontent.com/h-g-s/cbcbox/master/docs/perf_avx2_other.png)

<!-- PERF_PLOT_END -->

## Build variants

On **x86_64 Linux, macOS, and Windows**, the wheel ships two complete sets of binaries:

| Variant | OpenBLAS kernel | Clp SIMD | Minimum CPU |
|---|---|---|---|
| `generic` | `DYNAMIC_ARCH` (runtime dispatch) | standard | any x86_64 |
| `avx2` | `HASWELL` (256-bit AVX2/FMA) | `-march=haswell -DCOIN_AVX2=4` (all Haswell ISA extensions + 4-double AVX2 layout) | Haswell (2013+) |

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
`generic` variant (OpenBLAS `DYNAMIC_ARCH=1`) and once for the `avx2` variant
(`TARGET=HASWELL`, `CXXFLAGS=-O3 -march=haswell -DCOIN_AVX2=4`).  AMD and Nauty
are built only once (they are pure combinatorial code with no BLAS dependency)
and reused by both COIN-OR variants.

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

The test suite (`pytest`) solves fifteen MIP instances and checks the optimal
objective values, in both single-threaded and parallel (3-thread) modes.
On x86_64 Linux, macOS, and Windows **each test is run twice** — once against
the `generic` binary and once against the `avx2` binary — and a side-by-side
performance comparison is recorded:

| Instance | Expected optimal | Time limit |
|---|---|---|
| `pp08a.mps.gz` | 7 350 | 2000 s |
| `sprint_hidden06_j.mps.gz` | 130 | 2000 s |
| `air03.mps.gz` | 340 160 | 2000 s |
| `air04.mps.gz` | 56 137 | 2000 s |
| `air05.mps.gz` | 26 374 | 2000 s |
| `nw04.mps.gz` | 16 862 | 2000 s |
| `mzzv11.mps.gz` | −21 718 | 2000 s |
| `trd445c.mps.gz` | −153 419.078836 | 2000 s |
| `nursesched-sprint02.mps.gz` | 58 | 2000 s |
| `stein45.mps.gz` | 30 | 2000 s |
| `neos-810286.mps.gz` | 2 877 | 2000 s |
| `neos-1281048.mps.gz` | 601 | 2000 s |
| `j3050_8.mps.gz` | 1 | 2000 s |
| `qiu.mps.gz` | −132.873136947 | 2000 s |
| `gesa2-o.mps.gz` | 25 779 856.3717 | 2000 s |

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
| Darwin x86_64 | 46.88 | 16.76 | 2.80× |
| Darwin arm64 | 35.72 | — | — |
| Windows AMD64 | 49.96 | 15.28 | 3.27× |

### 3 threads

| Platform | generic (s) | avx2 (s) | avx2 speedup |
|---|---|---|---|
| Darwin x86_64 | 34.37 | 16.54 | 2.08× |
| Darwin arm64 | 31.61 | — | — |
| Windows AMD64 | 45.31 | 16.48 | 2.75× |

## Per-instance results

### `pp08a.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 4.43 | 11.16 | 0.40× |
| Darwin x86_64 | generic | 9.32 | 6.52 | 1.43× |
| Darwin arm64 | generic | 8.86 | 12.14 | 0.73× |
| Windows AMD64 | avx2 | 4.98 | 7.31 | 0.68× |
| Windows AMD64 | generic | 13.30 | 20.96 | 0.63× |

### `sprint_hidden06_j.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 46.10 | 49.00 | 0.94× |
| Darwin x86_64 | generic | 166.49 | 164.75 | 1.01× |
| Darwin arm64 | generic | 117.40 | 116.09 | 1.01× |
| Windows AMD64 | avx2 | 58.08 | 57.48 | 1.01× |
| Windows AMD64 | generic | 253.97 | 231.89 | 1.10× |

### `air03.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 1.59 | 1.71 | 0.93× |
| Darwin x86_64 | generic | 7.17 | 6.12 | 1.17× |
| Darwin arm64 | generic | 3.74 | 4.62 | 0.81× |
| Windows AMD64 | avx2 | 2.39 | 2.61 | 0.92× |
| Windows AMD64 | generic | 6.52 | 6.20 | 1.05× |

### `air04.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 49.51 | 39.84 | 1.24× |
| Darwin x86_64 | generic | 108.18 | 71.42 | 1.51× |
| Darwin arm64 | generic | 101.37 | 77.75 | 1.30× |
| Windows AMD64 | avx2 | 32.90 | 28.93 | 1.14× |
| Windows AMD64 | generic | 157.28 | 128.07 | 1.23× |

### `air05.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 23.32 | 17.73 | 1.32× |
| Darwin x86_64 | generic | 55.07 | 40.49 | 1.36× |
| Darwin arm64 | generic | 45.97 | 41.33 | 1.11× |
| Windows AMD64 | avx2 | 17.64 | 13.65 | 1.29× |
| Windows AMD64 | generic | 60.04 | 42.21 | 1.42× |

### `nw04.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 12.16 | 13.96 | 0.87× |
| Darwin x86_64 | generic | 33.93 | 46.54 | 0.73× |
| Darwin arm64 | generic | 32.39 | 38.47 | 0.84× |
| Windows AMD64 | avx2 | 15.73 | 16.08 | 0.98× |
| Windows AMD64 | generic | 58.04 | 55.64 | 1.04× |

### `mzzv11.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 117.09 | 94.52 | 1.24× |
| Darwin x86_64 | generic | 476.47 | 333.68 | 1.43× |
| Darwin arm64 | generic | 239.62 | 214.84 | 1.12× |
| Windows AMD64 | avx2 | 118.46 | 222.86 | 0.53× |
| Windows AMD64 | generic | 261.27 | 269.50 | 0.97× |

### `trd445c.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 98.57 | 112.38 | 0.88× |
| Darwin x86_64 | generic | 200.93 | 202.68 | 0.99× |
| Darwin arm64 | generic | 171.81 | 188.80 | 0.91× |
| Windows AMD64 | avx2 | 103.02 | 100.52 | 1.02× |
| Windows AMD64 | generic | 241.19 | 231.39 | 1.04× |

### `nursesched-sprint02.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 29.92 | 41.20 | 0.73× |
| Darwin x86_64 | generic | 87.36 | 90.99 | 0.96× |
| Darwin arm64 | generic | 82.45 | 94.54 | 0.87× |
| Windows AMD64 | avx2 | 26.77 | 26.52 | 1.01× |
| Windows AMD64 | generic | 131.29 | 86.35 | 1.52× |

### `stein45.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 8.62 | 10.77 | 0.80× |
| Darwin x86_64 | generic | 24.42 | 17.16 | 1.42× |
| Darwin arm64 | generic | 18.49 | 13.54 | 1.37× |
| Windows AMD64 | avx2 | 8.48 | — | — |
| Windows AMD64 | generic | 27.34 | 17.13 | 1.60× |

### `neos-810286.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 12.48 | 14.28 | 0.87× |
| Darwin x86_64 | generic | 41.37 | 40.30 | 1.03× |
| Darwin arm64 | generic | 24.67 | 31.13 | 0.79× |
| Windows AMD64 | avx2 | 13.18 | 15.63 | 0.84× |
| Windows AMD64 | generic | 36.67 | 45.63 | 0.80× |

### `neos-1281048.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 17.78 | 9.66 | 1.84× |
| Darwin x86_64 | generic | 110.96 | 15.89 | 6.98× |
| Darwin arm64 | generic | 37.56 | 16.95 | 2.22× |
| Windows AMD64 | avx2 | 13.75 | 17.43 | 0.79× |
| Windows AMD64 | generic | 37.54 | 45.70 | 0.82× |

### `j3050_8.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 3.85 | 3.92 | 0.98× |
| Darwin x86_64 | generic | 7.18 | 7.63 | 0.94× |
| Darwin arm64 | generic | 7.70 | 6.77 | 1.14× |
| Windows AMD64 | avx2 | 2.19 | 2.37 | 0.92× |
| Windows AMD64 | generic | 8.67 | 6.97 | 1.24× |

### `qiu.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 42.56 | 15.79 | 2.70× |
| Darwin x86_64 | generic | 62.31 | 24.57 | 2.54× |
| Darwin arm64 | generic | 83.68 | 27.62 | 3.03× |
| Windows AMD64 | avx2 | 24.09 | 12.37 | 1.95× |
| Windows AMD64 | generic | 82.99 | 48.81 | 1.70× |

### `gesa2-o.mps.gz`

| Platform | Build | 1 thread (s) | 3 threads (s) | parallel speedup |
|---|---|---|---|---|
| Darwin x86_64 | avx2 | 4.68 | 5.11 | 0.92× |
| Darwin x86_64 | generic | 12.31 | 9.84 | 1.25× |
| Darwin arm64 | generic | 8.96 | 7.64 | 1.17× |
| Windows AMD64 | avx2 | 3.45 | 3.29 | 1.05× |
| Windows AMD64 | generic | 11.15 | 11.75 | 0.95× |


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


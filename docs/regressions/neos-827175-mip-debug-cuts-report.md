# `neos-827175` optimal-objective regression — `mip-debug-cuts` diagnostic report

**Date:** 2026-08-04
**CI run:** [30873234285](https://github.com/h-g-s/cbcbox/actions/runs/30873234285) (triggered on `cbcbox@2da946b`, Cbc `next` branch as of this run)
**Cbc build under test:** `CBC devel (git:0c2a6fb)` — COIN-OR Branch and Cut

## Summary

`tests/test_solve.py::test_solve[...-neos-827175.mps.gz-112.00152-2000]` fails
consistently on **macOS (both ARM64 and Intel, both `generic` and `avx2`
build variants)**: Cbc reports a final incumbent objective of **113.00152**
after hitting the 300s time limit, but the certified optimal objective
(confirmed independently via HiGHS and cross-referenced against
`~/experiments/cbc` runs) is **112.00152**. The Linux (ARM64 + x86_64,
all variants) and Windows builds do **not** reproduce this in the same CI
run — the incumbent Cbc finds there matches 112.00152 (see "Platform
results" below).

Because a certified reference optimal solution was available
(`tests/sols/neos-827175.sol`), the CI's new automatic diagnostic
(`tests/conftest.py`'s `pytest_runtest_makereport` hook) fired and ran
Cbc's `Cbc/test/mip-debug-cuts.cpp` row-cut debugger
(`Cbc_activateRowCutDebugger`) against the reference solution. This tool
flags **any** generated cut or bound-fixing that would exclude a known
feasible/optimal solution — i.e. it can catch a genuinely *invalid* cut
before it even causes a wrong final answer.

**Result: many invalid cuts/bound-fixings were flagged**, overwhelmingly
attributed to the **Probing** cut generator (cut generator index `0`),
with additional flags from `TwoMirCuts`, `Gomory`, `ZeroHalf`,
`MixedIntegerRounding2`, `Clique`, and `Knapsack`. This is the strongest
lead: Probing produced the *same* 5 invalid column bound-fixings
(forcing several variables' upper bound to `0` despite the reference
solution requiring a strictly positive value) identically across all
three captured logs (macOS ARM64 generic, macOS Intel generic, macOS
Intel AVX2), suggesting a deterministic bug rather than a floating-point/
threading race.

## How to reproduce locally

```bash
# from a Cbc "next" branch checkout, built with assertions active
# (non -DNDEBUG debug build — see cbcbox's setup.py _DEBUG_CFLAGS)
g++ -std=c++17 -O0 -g -I<dist>/include/coin-or \
    Cbc/test/mip-debug-cuts.cpp -o mip-debug-cuts \
    -L<dist>/lib -lCbc -Wl,-rpath,<dist>/lib

./mip-debug-cuts tests/neos-827175.mps.gz tests/sols/neos-827175.sol 300 0
```

(`tests/neos-827175.mps.gz` and `tests/sols/neos-827175.sol` are in the
`h-g-s/cbcbox` repo.) Full raw logs from the CI run are attached to this
report (see "Artifacts" below).

## Cut-generator violation counts

Counted via `grep -c "Cut generator N (...) produced invalid"` on each
platform's captured log (row cuts + column/bound-fixing cuts combined):

| Cut generator            | macOS ARM64 generic | macOS Intel generic | macOS Intel AVX2 |
|---------------------------|:---:|:---:|:---:|
| 0 — Probing                | 27  | 27  | 27  |
| 1 — Gomory                 | 11  |  3  |  3  |
| 2 — Knapsack                |  1  |  0  |  0  |
| 3 — Clique                  |  1  |  0  |  0  |
| 4 — MixedIntegerRounding2    |  2  |  0  |  0  |
| 6 — TwoMirCuts               | 31  |  6  |  6  |
| 7 — ZeroHalf                 |  4  |  1  |  1  |

**Probing's count (27) is identical across all three logs**, and inspection
shows the *first five* flagged column-bound violations are byte-for-byte
identical across all three platforms/variants (see below) — this is the
best starting point for investigation, since it points to a reproducible,
deterministic defect rather than a numerically-sensitive tie-break.

## Concrete example: Probing's invalid column (bound-fixing) cuts

From all three logs, identically, in the first Probing pass:

```
[pre-resolve check] Cut generator 0 (Probing) produced invalid COLUMN cut (bad new UB) on col 66  (C0000066): known=29.000000 new UB=0.000000 (pass 1)
[pre-resolve check] Cut generator 0 (Probing) produced invalid COLUMN cut (bad new UB) on col 155 (C0000155): known=1.000000  new UB=0.000000 (pass 1)
[pre-resolve check] Cut generator 0 (Probing) produced invalid COLUMN cut (bad new UB) on col 156 (C0000156): known=5.000000  new UB=0.000000 (pass 1)
[pre-resolve check] Cut generator 0 (Probing) produced invalid COLUMN cut (bad new UB) on col 110 (C0000110): known=2.000000  new UB=0.000000 (pass 1)
[pre-resolve check] Cut generator 0 (Probing) produced invalid COLUMN cut (bad new UB) on col 114 (C0000114): known=1.000000  new UB=0.000000 (pass 1)
```

Reading `known=X` as the reference/certified-optimal value for that
column: Probing fixes each of these columns' **upper bound to 0**, which
is inconsistent with the certified optimal solution needing e.g.
`col 66 = 29`. In the certified `.sol` file (`tests/sols/neos-827175.sol`),
0-based column 66 corresponds to:

```
     66 C0067                 29                       0     <- (from tests/sols/neos-827175.sol, whitespace-trimmed)
```

A second batch of identical Probing violations appears later in "pass 1"
of a subsequent go (cols 13, 59, 57, 41, 69, 29, 153, 155, 24, 54, 35, 26,
104, 114, 42, 22, 46, 3, 10, 86) — same pattern (`new UB=0.000000` against
a strictly positive known value), consistent across platforms.

## Example: `TwoMirCuts` invalid row cut

`TwoMirCuts` produces the largest count on ARM64 (31) vs. Intel (6) —
this divergence (unlike Probing's constant 27) suggests `TwoMirCuts`'s
invalid-cut count may be more sensitive to solve-path/tie-breaking
differences (e.g. AVX2 vs. generic numeric paths, or ARM64 vs. x86_64
FP results feeding into different cut rounds), while Probing's defect
looks structural/deterministic.

Example flagged row cut (5th invalid TwoMirCuts cut, pass 1, macOS
ARM64 generic log):

```
[pre-resolve check] Cut generator 6 (TwoMirCuts) produced invalid cut (5th in this go, pass 1)
[pre-resolve check]   cut lb=4 ub=1.797693135e+308 nElements=300
[pre-resolve check]     col 4393 coef=4 knownVal=0
[pre-resolve check]     col 4759 coef=4 knownVal=0
[pre-resolve check]     col 5125 coef=4 knownVal=0
[pre-resolve check]     col 5491 coef=4 knownVal=1
[pre-resolve check]     col 5813 coef=4 knownVal=0
...
```
(cut has `lb=4`, i.e. `sum(coef * knownVal) >= 4` is required, but
substituting the reference/known values into this cut's LHS evaluates to
something below the stated `lb=4` — i.e. the reference solution is cut
off).

## Final (post-search) outcome per log

| Platform / variant | Final reported objective | Certified optimal | Cbc-reported status |
|---|---|---|---|
| macOS ARM64 generic  | 113.00152 | 112.00152 | Stopped on time limit (gap 0.89%) |
| macOS Intel generic  | 113.00152 | 112.00152 | Stopped on time limit (gap 0.89%) |
| macOS Intel AVX2     | 113.00152 | 112.00152 | Stopped on time limit (gap 0.89%) |

`mip-debug-cuts`'s own summary line for all three: `result: not proven
obj=113.00152` (i.e. Cbc did *not* claim a proof of optimality here — it
hit the wall-clock time limit). **Caveat:** the diagnostic run above used
a 300s cap (`MIP_DEBUG_CUTS_TIME_LIMIT`, `conftest.py` default), not the
original test's exact 2000s budget, so the *specific* final incumbent may
differ in detail from the real `test_solve` run — but the **presence of
invalid Probing cuts is a structural symptom** that should be
investigated regardless of the exact time limit used.

## Suggested next steps for the Cbc-side investigation

1. Reproduce with a debug/assert-enabled Cbc build directly (not via
   `mip-debug-cuts`, though that remains the fastest repro) and set a
   breakpoint / add tracing in `CbcCutGenerator`/`CglProbing` where
   column bounds are tightened, focused on the deterministic column set
   flagged above (cols 66, 155, 156, 110, 114, 13, 59, 57, 41, 69, 29,
   153, 24, 54, 35, 26, 104, 42, 22, 46, 3, 10, 86 — 0-based Cbc column
   indices).
2. Since Probing's violation count (27) and the first 5 violating
   columns are byte-identical across ARM64/Intel/generic/AVX2, this is
   very likely **not** an AVX2 or FP-order issue but a logic bug in
   `CglProbing` (or in how Cbc consumes/validates its cuts) — check
   recent commits/changes to `CglProbing.cpp` (or its call sites in
   `CbcModel.cpp`) on the `next` branch.
3. `TwoMirCuts`'s far higher count on ARM64 (31) vs Intel (6/6) suggests
   a secondary, possibly numerically-sensitive issue in `CglTwomir` that
   is likely downstream of (amplified by) the Probing bug rather than
   independent — worth re-checking once Probing is fixed.
4. Re-run this same diagnostic (`mip-debug-cuts tests/neos-827175.mps.gz
   tests/sols/neos-827175.sol <time> 0`) after any fix to confirm zero
   "produced invalid" lines.

## Artifacts

Full raw logs (up to ~36K lines each) are available as CI artifacts on
run [30873234285](https://github.com/h-g-s/cbcbox/actions/runs/30873234285):
- `mip-debug-cuts-reports-macos-arm64` (contains the `generic` build's log)
- `mip-debug-cuts-reports-macos-intel` (contains both `generic` and `avx2` logs)

Reference solution used: `tests/sols/neos-827175.sol` (Cbc-native 3-token
format, certified via independent HiGHS solve + `~/experiments/cbc`
cross-validation, objective `112.00152`).

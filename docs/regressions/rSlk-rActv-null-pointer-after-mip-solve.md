# cbcbox 2.931 regression: null rSlk/rActv pointers after MIP solve

## Summary

python-mip was temporarily switched from `cbcbox` to `mipster` (a patched CBC
fork) because `mipster` carried three python-mip-specific correctness fixes
to CBC's C API that upstream/vanilla CBC does not have. `cbcbox` builds
**vanilla upstream CBC** (`coin-or/Cbc` branch `next`, via git clone in
`setup.py`, see `COIN_OR_BRANCH = "next"` and `COIN_REPOS` in
`~/dev/cbcbox/setup.py`), so it does **not** include these fixes.

We now want to switch python-mip back to `cbcbox` (a new version, 2.931,
was just released with CPU-dispatch AVX2 builds mirroring mipster's
approach). Testing showed this reintroduces one of the three original bugs.

## Reproduction

Repo: `~/dev/mip` (python-mip), branch `master`.

```python
import mip
m = mip.Model(solver_name='CBC')
m.verbose = 0
x = m.add_var('x', var_type=mip.CONTINUOUS)
y = m.add_var('y', var_type=mip.INTEGER)
z = m.add_var('z', var_type=mip.BINARY)
c1 = m.add_constr(x <= 10 * z)
c2 = m.add_constr(x <= 9.5)
c3 = m.add_constr(x + y <= 20)
m.objective = mip.maximize(4 * x + y - z)
m.optimize()          # proper MIP solve (not relax=True)
print(c1.slack)        # -0.0   (WRONG, expected 0.5)
```

Directly probing the C API after this MIP solve confirms the underlying
pointers are NULL:

```python
from mip.cbc import cbclib
cbclib.Cbc_getRowActivity(m.solver._model)[0]
# RuntimeError: cannot dereference null pointer from cdata 'double *'
```

Failing test in python-mip test suite (with `cbcbox>=2.931` installed and
`PMIP_CBC_LIBRARY` unset):

```
test/test_model.py::test_solve_relaxation[CBC]
  assert c1.slack == pytest.approx(0.5)
  AssertionError: assert -0.0 == 0.5 ± 5.0e-07
```

This test **passes** when the same environment uses `mipster` instead of
`cbcbox` (verified in a side-by-side venv comparison).

## Root cause

CBC's C API (`Cbc_C_Interface.cpp`) has a bug: after a MIP solve,
`Cbc_getMIPOptimizationResults` computes the row slack/activity vectors but
does not update the `model->rSlk` / `model->rActv` raw-pointer aliases that
`Cbc_cleanOptResults` had previously reset to `NULL`. Callers that fetch row
slack/activity via `Cbc_getRowSlack`/`Cbc_getRowActivity` after a MIP solve
(as `mip/cbc.py` does — see `Cbc_getRowSlack` calls around lines 1115, 1127,
1260, 1268, 1289 of `mip/cbc.py`) get a null pointer and either crash or
(when `cffi` silently returns something odd) get stale/zeroed data.

## How this was already fixed in mipster

Repo: `~/dev/mipster` (CBC fork used by the `mipster` PyPI package).
Commit `f75b01c6` — "fix: C API correctness for python-mip compatibility"
— fixes three issues in `src/Cbc_C_Interface.cpp`, one of which is exactly
this bug:

```diff
   Cbc_updateSlack(model, cbcModel.getRowActivity(), numRows );
+  model->rSlk = model->slack->data();
   /* storing row activity in MIP sol */
   memcpy(model->mipRowActivity->data(), cbcModel.getRowActivity(), sizeof(double)*numRows );
+  model->rActv = model->mipRowActivity->data();
```

The other two fixes in that same commit (not currently causing test
failures in python-mip's suite, but worth porting for parity/robustness):

1. **Auto-generate column names** in `Cbc_addColBuffer` when none supplied
   (format `C%07d`), so `var.name` is never empty (needed for
   `model.translate()` lookups by name in lazy-constraint callbacks).
2. **Sync `mipBestPossibleObjValue` to `obj_value`** when the MIP is proven
   optimal, to avoid spurious `bound > value` floating-point discrepancies
   (the dot-product recompute and `getBestPossibleObjValue()` use different
   FP paths).

Full diff for reference (`git show f75b01c6` in `~/dev/mipster`):

```diff
diff --git a/src/Cbc_C_Interface.cpp b/src/Cbc_C_Interface.cpp
index 634fddd3..e335bce2 100644
--- a/src/Cbc_C_Interface.cpp
+++ b/src/Cbc_C_Interface.cpp
@@ -881,6 +881,18 @@ static void Cbc_addColBuffer( Cbc_Model *model,
   model->cObj[p] = obj;
   model->nInt += (int)isInteger;
 
+  /* Auto-generate a column name when none is provided, matching the
+     convention used by commercial solvers (e.g. Gurobi assigns "C0000001").
+     This ensures that var.name is always non-empty, which is required for
+     variable look-up by name in callbacks (e.g. lazy constraint generators
+     that call model.translate()). */
+  char autoName[32];
+  if (name == NULL || name[0] == '\0') {
+    int globalCol = Cbc_getNumCols(model) + p;  /* total cols so far */
+    snprintf(autoName, sizeof(autoName), "C%07d", globalCol);
+    name = autoName;
+  }
+
   int ps = model->cNameStart[p];
   strncpy( model->cNames+ps, name, MAX_COL_NAME_SIZE );
   int len = std::min( (int)strlen(name), MAX_COL_NAME_SIZE );
@@ -2355,6 +2367,13 @@ static void Cbc_getMIPOptimizationResults( Cbc_Model *model, CbcModel &cbcModel
   for (int j=0 ; j<numCols ; ++j )
     model->obj_value += cbcModel.bestSolution()[j] * solver->getObjCoefficients()[j];
 
+  /* When proven optimal the best bound equals the incumbent by definition.
+     Sync mipBestPossibleObjValue to the freshly recomputed obj_value so that
+     callers always see bound == value instead of a tiny floating-point
+     discrepancy caused by the two different computation paths. */
+  if (model->mipIsProvenOptimal)
+    model->mipBestPossibleObjValue = model->obj_value;
+
   /* solution pool */
   for ( int i=0 ; i<numSols ; ++i ) {
     const double *xi = cbcModel.savedSolution(i);
@@ -2376,8 +2395,10 @@ static void Cbc_getMIPOptimizationResults( Cbc_Model *model, CbcModel &cbcModel
   } /* saving solution pool */
 
   Cbc_updateSlack(model, cbcModel.getRowActivity(), numRows );
+  model->rSlk = model->slack->data();
   /* storing row activity in MIP sol */
   memcpy(model->mipRowActivity->data(), cbcModel.getRowActivity(), sizeof(double)*numRows );
+  model->rActv = model->mipRowActivity->data();
 
   /* setting this solution as a MIPStart for possible next optimization */
   if (model->nColsMS) {
```

There's also an earlier, related mipster fix worth checking for parity:
`524d3f61` / `24ea9cf5` / `664e4f38` — "Fix Cbc_resolve not populating rSlk
(missing Cbc_updateSlack call)".

## Why cbcbox doesn't have this fix

`cbcbox` (repo `~/dev/cbcbox`, `setup.py`) builds **vanilla upstream CBC**:

```python
COIN_OR_BRANCH  = "next"
...
COIN_REPOS = [("CoinUtils", ...), ("Osi", ...), ("Clp", ...), ("Cgl", ...), ("Cbc", ...)]
...
src = clone_if_missing(name, url, COIN_OR_BRANCH)
```

It does not apply any source patches to the cloned `Cbc` repo (grep for
`patch` in `setup.py` only shows `patchelf` binary rpath patching, unrelated
to source patching). So the `Cbc_C_Interface.cpp` fixes from
`~/dev/mipster` commit `f75b01c6` (and possibly `524d3f61`) never make it
into cbcbox's build.

## What needs to happen for python-mip to switch back to cbcbox

Port the fix from `~/dev/mipster` commit `f75b01c6` (at minimum the
rSlk/rActv restoration; ideally all three fixes for parity) into
`cbcbox`'s build process. Options:

1. **Preferred**: Add a small patch step in `~/dev/cbcbox/setup.py` (or a
   `.patch` file applied after `clone_if_missing` for the `Cbc` repo) that
   applies the same `Cbc_C_Interface.cpp` changes before building.
2. Alternatively, point `cbcbox`'s `Cbc` clone at a maintained fork/branch
   that already carries these patches (e.g. cherry-pick `f75b01c6` onto a
   `cbcbox`-specific branch of a Cbc fork), rather than vanilla
   `coin-or/Cbc@next`.
3. Confirm no other mipster-side patches are needed by diffing
   `~/dev/mipster/src/Cbc_C_Interface.cpp` against the vanilla
   `coin-or/Cbc` version at the `next` branch tip to catch anything not
   surfaced by `git log -S`.

After patching, re-verify with python-mip's test suite:

```bash
cd ~/dev/mip
python3 -m venv /tmp/mip_test_env
env -u PMIP_CBC_LIBRARY /tmp/mip_test_env/bin/pip install -e ".[test]"
env -u PMIP_CBC_LIBRARY /tmp/mip_test_env/bin/python -m pytest test/ -k cbc -q
```

Note: the local shell environment has `PMIP_CBC_LIBRARY` set to a stale path
(`/home/haroldo/prog/cbc-pmip/lib/libCbc.so`), which overrides mip/cbc.py's
library auto-detection entirely. Must `unset`/`env -u` it (or update it) to
actually exercise the `cbcbox` code path.

Also note a separate, apparently unrelated flaky test:
`test/test_cbc_params.py::test_lp_time_limit_truncated` — fails because the
LP (BRAZIL3 relaxation) solves faster than the 3-second time limit used by
the test (cbcbox 2.931's AVX2 build appears to be quite a bit faster than
whatever was used when the test was written), so status comes back OPTIMAL
instead of TRUNCATED. This is a test-timing issue, not a correctness bug —
may want to increase problem size / lower the time limit in that test, but
it is out of scope for the rSlk/rActv fix.

## Current state of ~/dev/mip working tree

The `master` branch of `~/dev/mip` currently has *uncommitted* changes that
revert the mipster migration back to cbcbox:
- `pyproject.toml`: `dependencies = ["cffi>=1.15", "cbcbox>=2.931"]`
  (was `mipster>=0.2.4`)
- `mip/cbc.py`: loader restored to use `cbcbox.cbc_lib_dir()` /
  `cbcbox.cbc_dist_dir()` (libCbc.so / libCbc.dylib / bin/libCbc-0.dll),
  same as pre-mipster-migration code, while keeping the `__del__` /
  PyPy-safety guards (`getattr(self, "_model", None)`, etc.) that were
  added during the mipster migration (commit `64610aa`) — those guards
  are solver-agnostic and should stay.

**These changes should NOT be committed/merged until cbcbox has the
rSlk/rActv fix (and ideally the other two fixes), and the full python-mip
test suite passes cleanly with the patched cbcbox.**

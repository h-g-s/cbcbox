# macOS: libCbc.dylib fails to load — @rpath/libgcc_s.1.1.dylib not bundled

## Summary

cbcbox 2.933 (which fixes the earlier rSlk/rActv null-pointer regression,
see `rSlk-rActv-null-pointer-after-mip-solve.md` in this folder) introduced
a **new regression on macOS**: `libCbc.dylib` fails to `dlopen()` because it
references `@rpath/libgcc_s.1.1.dylib`, but that dylib is never copied into
the wheel's `lib/` directory.

This was caught in python-mip's GitHub Actions CI
(`coin-or/python-mip`, run
https://github.com/coin-or/python-mip/actions/runs/31889028431) right
after switching python-mip's CBC dependency back from `mipster` to
`cbcbox>=2.933`. All 8 `macos-15` matrix jobs (Python 3.10–3.14, pypy3.11)
failed identically; every other OS (Linux x86_64, Linux ARM64, Windows)
passed cleanly.

## Error

```
An error occurred while loading the CBC library:
cannot load library
  '.../site-packages/cbcbox/cbc_dist/lib/libCbc.dylib':
  dlopen(.../cbcbox/cbc_dist/lib/libCbc.dylib, 0x0002):
  Library not loaded: @rpath/libgcc_s.1.1.dylib
  Reason: tried: '.../cbcbox/cbc_dist/lib/libgcc_s.1.1.dylib' (no such file),
    '/opt/homebrew/Cellar/gcc/16.1.0/lib/gcc/current/gcc/aarch64-apple-darwin24/16/libgcc_s.1.1.dylib' (no such file),
    ... (several more homebrew paths, all "no such file") ...
```

This happened for the plain `cbc_dist` (generic, non-AVX2) build, which is
what's selected on the `macos-15` (Apple Silicon / arm64) CI runner since
AVX2 doesn't apply to ARM.

This means python-mip cannot switch back to `cbcbox` (from the temporary
`mipster` dependency) until this is fixed, even though the earlier
rSlk/rActv bug is confirmed fixed in 2.933.

## Root cause

In `~/dev/cbcbox/setup.py`, `bundle_dynamic_deps()` is responsible for
making the wheel self-contained on each OS by copying non-system shared
library dependencies next to the built binaries/libs and rewriting their
install names/rpaths. It decides what counts as "already handled / system,
don't bundle" via `_is_system_lib()`:

```python
def _is_system_lib(path: str) -> bool:
    """Return True for libs that should NOT be bundled into the wheel."""
    name = os.path.basename(path)
    if platform.system() == "Linux":
        return bool(_MANYLINUX_ALLOWED.match(name))
    # macOS: skip anything already using a loader-relative path, or in
    # the standard system library trees.
    return (
        path.startswith("@")
        or path.startswith("/usr/lib/")
        or path.startswith("/System/")
    )
```

The `path.startswith("@")` check assumes that if a dependency's install
name is already `@rpath/...` (or `@loader_path/...`, `@executable_path/...`),
it must already have been handled/bundled by an earlier pass of
`bundle_dynamic_deps` (which rewrites hard absolute paths to `@rpath/name`
after copying the lib in). That assumption is **false** when the
*original*, not-yet-processed library on the build machine was itself
built/installed with an `@rpath`-relative install name from the start —
which is exactly what recent Homebrew GCC (16.1.0, currently on
`macos-15` GitHub-hosted runners) does for `libgcc_s.1.1.dylib`. `otool -L`
on `libCbc.dylib` reports the dependency as `@rpath/libgcc_s.1.1.dylib`
straight from the linker, before cbcbox's own bundling pass ever touches
it. `_is_system_lib` then wrongly classifies it as "already relocatable /
don't need to bundle", so `bundle_dynamic_deps` skips copying it into
`lib/`, and the dangling `@rpath` reference has nothing to resolve to at
runtime, anywhere the wheel is installed (there is no `-add_rpath` pointing
at the Homebrew GCC lib dir, and even if there were, the target CI/end-user
machine won't have that specific Homebrew Cellar path).

This is presumably new since cbcbox last had CI passing on macOS (2.929,
per python-mip's CI history) — most likely GCC was bumped to a newer
version on the macOS runner image (or in the Homebrew formula) at some
point between then and the 2.933 build, changing how it reports its own
runtime lib's install name from an absolute path to `@rpath/...`.

## Suggested fix

`_is_system_lib` needs to distinguish "this is a loader-relative path we
already rewrote as part of bundling" (should skip) from "this is a
loader-relative path reported natively by the compiler/toolchain, not yet
bundled" (should NOT skip — must still be resolved and copied in).

Options, roughly in order of preference:

1. **Resolve `@rpath`/`@loader_path`/`@executable_path` refs to a real file
   before the skip decision.** Use `otool -l <path>` to read the binary's
   own `LC_RPATH` entries (and, transitively, the toolchain's known lib
   dirs, e.g. query `gcc -print-file-name=libgcc_s.1.1.dylib` or scan
   `$(brew --prefix gcc)/lib/gcc/current/`) to find the on-disk file that
   `@rpath/libgcc_s.1.1.dylib` currently resolves to, and bundle *that*,
   exactly like any other non-system dependency. Only truly skip
   `@`-prefixed deps that cannot be resolved to any file *and* are already
   present in `lib_dir` (meaning this function's own previous pass already
   put them there).
2. Simpler targeted fix: keep a `_visited`/"already bundled" set (the
   function already has one, `_visited`, threaded through recursive calls)
   and only treat `@`-prefixed names as "system/skip" if
   `os.path.basename(path) in _visited` (i.e., cbcbox itself already copied
   it in this build), otherwise resolve and bundle it like any other dep.
3. As a stopgap, explicitly special-case `libgcc_s*.dylib`,
   `libstdc++*.dylib`, `libquadmath*.dylib`, `libgfortran*.dylib` (GCC
   runtime libs) so they're always resolved via
   `gcc -print-file-name=<name>` and bundled regardless of how their
   install name looks, since these are exactly the transitive runtime
   dependencies of the Fortran/C++ toolchain used to build CoinUtils/Clp/Cbc
   on macOS.

Whichever approach, verify manually after the fix:

```bash
otool -L cbc_dist/lib/libCbc.dylib       # generic build
otool -L cbc_dist_avx2/lib/libCbc.dylib  # AVX2 build (Intel only)
```
All non-`/usr/lib`, non-`/System` entries should show as `@rpath/<name>`
with `<name>` present as an actual file in the same `lib/` directory (not
just a hopeful rpath reference).

## How to verify the fix

Once patched and a new cbcbox version is released:

```bash
cd ~/dev/mip
python3 -m venv /tmp/mip_test_env
env -u PMIP_CBC_LIBRARY /tmp/mip_test_env/bin/pip install -e ".[test]"
env -u PMIP_CBC_LIBRARY /tmp/mip_test_env/bin/python -m pytest test/ -k cbc -q
```

But since this bug is macOS-specific and this dev environment is Linux,
the authoritative check is python-mip's own CI matrix (includes
`macos-15`) — push a commit bumping `cbcbox>=<new version>` in
`~/dev/mip/pyproject.toml` and watch
`https://github.com/coin-or/python-mip/actions` for the `test (*, macos-15)`
jobs specifically.

## Current status of python-mip switch-back

`~/dev/mip` master branch: commit `319805a` ("Switch back to cbcbox for
the bundled CBC library") is already **pushed** with `cbcbox>=2.933`. CI
run `31889028431` shows:
- ✅ Linux x86_64 (Python 3.10–3.14, pypy3.11)
- ✅ Linux ARM64 (Python 3.10–3.14, pypy3.11)
- ✅ Windows (Python 3.10–3.14 — no pypy on Windows)
- ❌ macOS (Python 3.10–3.14, pypy3.11) — **all failing** due to this bug

python-mip's CBC-on-macOS support is broken on master until this cbcbox
bug is fixed and a new version is released.

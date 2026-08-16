# macOS: partial @rpath rewrite — internal COIN-OR libs still use absolute build paths

## Summary

Follow-up to `macos-libgcc_s-not-bundled.md`. cbcbox 2.934 shipped a fix
(commit `7844000`, "Fix macOS @rpath deps (e.g. libgcc_s) not bundled into
wheel") for the `libgcc_s.1.1.dylib` dlopen failure. That specific issue is
gone, but a **new/related dlopen failure** appears in its place: `libCbc.dylib`
now fails to load because one of the *internal* COIN-OR shared libraries it
depends on (`libOsiClp.0.dylib`) is still referenced by its **absolute
CI-build-machine path**, not `@rpath/...`.

Confirmed via python-mip's CI
(`coin-or/python-mip`, run
https://github.com/coin-or/python-mip/actions/runs/31965585717, triggered
by bumping to `cbcbox>=2.934`): all 6 `macos-15` matrix jobs (Python
3.10–3.14, pypy3.11) fail identically; Linux (x86_64 + ARM64) and Windows
all pass.

## Error

```
An error occurred while loading the CBC library:
cannot load library
  '.../site-packages/cbcbox/cbc_dist/lib/libCbc.dylib':
  dlopen(.../cbcbox/cbc_dist/lib/libCbc.dylib, 0x0002):
  Library not loaded: /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libOsiClp.0.dylib
  Referenced from: <...> .../cbcbox/cbc_dist/lib/libCbc.dylib
  Reason: tried: '/Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libOsiClp.0.dylib' (no such file), ...
```

The referenced path (`/Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/...`) is
the **cbcbox CI build machine's own working directory** — it obviously
does not exist on any other machine (or even a different CI run of
cbcbox's own build), so this dependency can never resolve outside the
exact build sandbox it was compiled in.

## Direct inspection (proof)

Downloaded the actual published wheel
(`cbcbox-2.934-py3-none-macosx_15_0_arm64.whl` from PyPI) and inspected
Mach-O load commands with `macholib` (since `otool` isn't available on
Linux):

```
=== libCbc.dylib ===
  LC_ID_DYLIB   /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libCbc.0.dylib
  LC_LOAD_DYLIB /usr/lib/libSystem.B.dylib
  LC_LOAD_DYLIB @rpath/libCgl.0.dylib                                        <- rewritten OK
  LC_LOAD_DYLIB /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libOsiClp.0.dylib   <- NOT rewritten
  LC_LOAD_DYLIB /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libClp.0.dylib      <- NOT rewritten
  LC_LOAD_DYLIB /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libopenblas.0.dylib <- NOT rewritten
  LC_LOAD_DYLIB /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libOsi.0.dylib      <- NOT rewritten
  LC_LOAD_DYLIB /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libCoinUtils.0.dylib <- NOT rewritten
  LC_LOAD_DYLIB /usr/lib/libz.1.dylib
  LC_LOAD_DYLIB /usr/lib/libc++.1.dylib
  LC_RPATH      @loader_path

=== libOsiClp.dylib ===
  LC_ID_DYLIB   /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libOsiClp.0.dylib
  LC_LOAD_DYLIB @rpath/libOsi.0.dylib          <- rewritten OK
  LC_LOAD_DYLIB @rpath/libClp.0.dylib          <- rewritten OK
  LC_LOAD_DYLIB /Users/runner/.../libopenblas.0.dylib   <- NOT rewritten
  LC_LOAD_DYLIB /Users/runner/.../libCoinUtils.0.dylib  <- NOT rewritten

=== libClp.dylib ===
  LC_ID_DYLIB   /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libClp.0.dylib
  LC_LOAD_DYLIB @rpath/libopenblas.0.dylib     <- rewritten OK
  LC_LOAD_DYLIB @rpath/libCoinUtils.0.dylib    <- rewritten OK

=== libOsi.dylib ===
  LC_ID_DYLIB   /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libOsi.0.dylib
  LC_LOAD_DYLIB @rpath/libCoinUtils.0.dylib    <- rewritten OK

=== libCoinUtils.dylib ===
  LC_ID_DYLIB   /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libCoinUtils.0.dylib
  (no non-system deps)

=== libCgl.dylib ===
  LC_ID_DYLIB   /Users/runner/work/cbcbox/cbcbox/cbc_dist/lib/libCgl.0.dylib
  LC_LOAD_DYLIB @rpath/libOsiClp.0.dylib       <- rewritten OK
  LC_LOAD_DYLIB /Users/runner/.../libClp.0.dylib        <- NOT rewritten
  LC_LOAD_DYLIB /Users/runner/.../libopenblas.0.dylib   <- NOT rewritten
  LC_LOAD_DYLIB /Users/runner/.../libOsi.0.dylib        <- NOT rewritten
  LC_LOAD_DYLIB /Users/runner/.../libCoinUtils.0.dylib  <- NOT rewritten
```

**Two extra observations beyond the missing rewrites:**

1. Every library's own `LC_ID_DYLIB` (its self-identity, used by other
   binaries at link time and matched at load time in some scenarios) is
   *also* still the absolute build path, never rewritten to
   `@rpath/<name>`. Only *references from other binaries* are targeted by
   `bundle_dynamic_deps`; the id of the library file itself is only
   rewritten when `dst` doesn't already exist (a *fresh copy*, see
   `install_name_tool -id` call) — but since these libraries already live
   in `lib_dir` from the start (they aren't being copied in from
   elsewhere), that `-id` rewrite path in `bundle_dynamic_deps` is never
   reached for them either.

2. The pattern of which refs got rewritten vs. not is inconsistent between
   libraries and doesn't correlate with anything about the dependency
   itself (e.g. `libCoinUtils.0.dylib` is correctly rewritten as a
   dependency of `libOsi.dylib` and `libClp.dylib`, but NOT rewritten as a
   dependency of `libOsiClp.dylib` or `libCgl.dylib`).

## Root cause (traced in `~/dev/cbcbox/setup.py`, function `bundle_dynamic_deps`)

```python
for install_name in _dynamic_deps_macos(binary):
    name = os.path.basename(install_name)
    if name in _visited:
        continue                      # <-- BUG: skips rewriting `binary`'s
                                       #     OWN reference too, not just the
                                       #     "copy this dependency file in"
                                       #     step.
    ...
    _visited.add(name)
    if install_name != f"@rpath/{name}":
        subprocess.run(["install_name_tool", "-change", install_name,
                         f"@rpath/{name}", binary], check=True)
    dst = os.path.join(lib_dir, name)
    if not os.path.exists(dst):
        shutil.copy2(src_path, dst)
        ...
        subprocess.run(["install_name_tool", "-id", f"@rpath/{name}", dst], check=True)
    bundle_dynamic_deps(dst, lib_dir, _visited)
```

`_visited` is meant to prevent infinite recursion / duplicate copy-and-id
work when the *same dependency file* is reached from multiple places in
the dependency graph (e.g. both `libCbc` and `libCgl` depend on
`libOsiClp`). That part is correct and necessary.

But the `if name in _visited: continue` guard is checked **before** the
`install_name_tool -change ... binary` line, so it also skips rewriting
the *current* binary's own load-command reference whenever the target
name happens to have already been visited via a **different** referencing
binary earlier in the (DFS) traversal. Since `bundle_dynamic_deps` is
invoked once per top-level `.dylib` found by
`_glob.glob(os.path.join(lib_dir, "*.dylib"))` in `_bundle_dist()`, and
each top-level call gets its own fresh `_visited` set (`_visited=None`
default), the exact pattern of "rewritten vs. not" ends up depending on
filesystem glob order and DFS traversal order across the whole library
set — which matches exactly what was observed (some deps of some
libraries got the `-change` applied, others of the same name in a
different library did not, depending on whether that name had already been
"visited" earlier in that same top-level call's recursion).

This is a **pre-existing bug** in `bundle_dynamic_deps`, likely dormant on
prior successful builds (e.g. 2.929) because the COIN-OR `next`-branch
build previously produced dylibs already linked with `-install_name
@rpath/...` (no absolute-path rewriting needed at all, so the buggy
`continue` never mattered). Something in a more recent build/toolchain
change (see `e7e2b35 Build COIN-OR stack from next branches, ...`, or a
newer `autotools`/`libtool` version on the CI image) started emitting
absolute install names again, which exposed this dormant bug in the
bundling script for the first time in 2.933/2.934.

## Suggested fix

Split the "already bundled this dependency file" concern from the "already
rewrote this exact reference in this exact binary" concern. Concretely:

```python
for install_name in _dynamic_deps_macos(binary):
    name = os.path.basename(install_name)

    # Always fix up *this* binary's own reference, regardless of whether
    # the target dependency has been bundled/visited before.
    if install_name != f"@rpath/{name}":
        src_path = install_name
        if install_name.startswith("@"):
            resolved = _resolve_macos_dep(binary, install_name)
            if not resolved:
                print(f"warning: could not resolve {install_name} "
                      f"referenced by {binary}; not bundled", file=sys.stderr)
            else:
                src_path = resolved
        subprocess.run(["install_name_tool", "-change", install_name,
                         f"@rpath/{name}", binary], check=True)
    else:
        src_path = None  # already @rpath; nothing to fix in `binary`

    if name in _visited:
        continue  # dependency file itself already bundled/recursed
    _visited.add(name)

    dst = os.path.join(lib_dir, name)
    if not os.path.exists(dst) and src_path:
        shutil.copy2(src_path, dst)
        os.chmod(dst, 0o755)
    # Always normalize the copied/existing lib's own id, even if it was
    # already present in lib_dir before this pass started (e.g. sibling
    # COIN-OR libs built straight into lib_dir, never "copied in").
    subprocess.run(["install_name_tool", "-id", f"@rpath/{name}", dst],
                    capture_output=True)  # ignore "already @rpath" no-ops
    bundle_dynamic_deps(dst, lib_dir, _visited)
```

Also consider sharing **one** `_visited` set across the entire
`_bundle_dist()` loop (pass it explicitly instead of relying on the
per-call default), so a dependency bundled/rewritten while processing one
top-level binary is recognized as already-bundled (for the copy-in step)
when reached again while processing a different top-level binary — while
still independently fixing every referencing binary's own load commands
each time, per the fix above.

Finally, normalize every library's own `LC_ID_DYLIB` to `@rpath/<name>`
unconditionally during `_bundle_dist()` (not just for freshly-copied
dependency files), since COIN-OR's own libraries (Cbc, Clp, Cgl, Osi,
OsiClp, CoinUtils) live in `lib_dir` from the start and never go through
the "freshly copied dependency" branch that currently performs the `-id`
rewrite.

## Verification after fix

```bash
otool -L cbc_dist/lib/libCbc.dylib
otool -L cbc_dist/lib/libOsiClp.dylib
otool -L cbc_dist/lib/libClp.dylib
otool -L cbc_dist/lib/libCgl.dylib
otool -L cbc_dist/lib/libOsi.dylib
```
Every entry (its own `-id` line included) should read `@rpath/<name>`
except genuine system libs (`/usr/lib/...`, `/System/...`). No absolute
paths pointing into a build sandbox should remain anywhere.

Since this dev environment is Linux, the authoritative check remains
python-mip's own CI (`macos-15` jobs) — bump `cbcbox>=<new version>` in
`~/dev/mip/pyproject.toml` and push, or (faster) verify directly against
the built wheel from cbcbox's own CI artifacts using `macholib` as shown
above, before cutting a new release.

## Current status of python-mip switch-back

`~/dev/mip` master branch, commit `0587467` ("chore: bump cbcbox
requirement to >=2.934") is pushed. CI run
https://github.com/coin-or/python-mip/actions/runs/31965585717:
- ✅ Linux x86_64 + ARM64, all Python versions + pypy3.11
- ✅ Windows, all Python versions
- ❌ macOS, all Python versions + pypy3.11 — still broken, now due to this
  *different* (but related) @rpath issue rather than the earlier
  libgcc_s one.

python-mip's CBC-on-macOS support remains broken on master until this is
fixed and a new cbcbox version is released.

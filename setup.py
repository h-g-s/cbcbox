import glob as _glob
import multiprocessing
import os
import platform
import re
import shlex
import shutil
import subprocess
import tarfile
import urllib.request

from setuptools import setup
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


# ── Wheel customisation ───────────────────────────────────────────────────────

class genericpy_bdist_wheel(_bdist_wheel):
    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.root_is_pure = False

    def get_tag(self):
        python, abi, plat = _bdist_wheel.get_tag(self)
        python, abi = "py3", "none"
        if os.environ.get("CIBUILDWHEEL", "0") == "1":
            if plat == "linux_x86_64":
                plat = "manylinux2014_x86_64"
            elif plat == "linux_aarch64":
                plat = "manylinux2014_aarch64"
        return python, abi, plat


cmdclass = {"bdist_wheel": genericpy_bdist_wheel}


# ── Constants ─────────────────────────────────────────────────────────────────

THIS_DIR      = os.path.abspath(os.path.dirname(__file__))
DIST_DIR      = os.path.join(THIS_DIR, "cbc_dist")
DIST_DIR_AVX2 = os.path.join(THIS_DIR, "cbc_dist_avx2")
LIB_DIR       = os.path.join(DIST_DIR, "lib")
NPROC    = str(max(1, multiprocessing.cpu_count()))

SUITESPARSE_TAG = "v7.12.2"
OPENBLAS_TAG    = "v0.3.31"
NAUTY_VERSION   = "2_8_9"
NAUTY_URL       = f"https://pallini.di.uniroma1.it/nauty{NAUTY_VERSION}.tar.gz"

# Build order matters: each project depends on the ones before it.
COIN_REPOS = [
    ("CoinUtils", "https://github.com/coin-or/CoinUtils.git"),
    ("Osi",       "https://github.com/coin-or/Osi.git"),
    ("Clp",       "https://github.com/coin-or/Clp.git"),
    ("Cgl",       "https://github.com/coin-or/Cgl.git"),
    ("Cbc",       "https://github.com/coin-or/Cbc.git"),
]

# Shared libraries allowed by the manylinux2014 policy (PEP 599).
# Anything NOT matching this pattern must be either linked statically
# or bundled inside the wheel.
_MANYLINUX_ALLOWED = re.compile(
    r"^lib(gcc_s|stdc\+\+|m|dl|rt|pthread|c|nsl|util|z|gomp|crypt|resolv)\."
    r"|^(linux-vdso|linux-gate|ld-linux)"
)

# ── Windows / MSYS2-MinGW64 constants ────────────────────────────────────────

# MSYS2 is pre-installed on windows-latest GitHub Actions runners.
_MSYS2_BASH = r"C:\msys64\usr\bin\bash.exe"

# DLLs that ship with Windows itself and must NOT be bundled.
_WIN_SYS_DLL = re.compile(
    r"^(kernel32|user32|ntdll|msvcrt|api-ms-win|ext-ms-win|advapi32|"
    r"shell32|ole32|oleaut32|ws2_32|mswsock|bcrypt|crypt32|secur32|"
    r"ucrtbase|vcruntime|hid|setupapi|cfgmgr32|imm32|version|winmm|"
    r"shlwapi|rpcrt4|comctl32|comdlg32|gdi32|netapi32|psapi|dbghelp)"
    r"\.dll$",
    re.IGNORECASE,
)


def _win_to_msys2(s: str) -> str:
    """Convert Windows absolute path references within *s* to MSYS2 format.

    'C:\\foo\\bar'          →  '/c/foo/bar'
    '--prefix=C:/foo/bar'   →  '--prefix=/c/foo/bar'
    '-LC:/foo/bar'          →  '-L/c/foo/bar'  (even when preceded by a flag letter)
    'https://example.com'   →  unchanged
    Strings without drive letters pass through unchanged.
    """
    s = str(s)
    # Protect URL schemes (e.g. "https://") so they aren't misidentified as
    # Windows drive letters.  Use a lambda so Python doesn't interpret \x in
    # the replacement string (re.sub string replacement doesn't allow \x).
    placeholder = "\x00\x00"
    s = re.sub(r'([A-Za-z]+)://', lambda m: m.group(1) + placeholder, s)
    # Convert Windows drive letters to MSYS2 /x/ format.
    s = re.sub(r'([A-Za-z]):[/\\]', lambda m: f"/{m.group(1).lower()}/", s)
    # Restore URL schemes and normalise remaining back-slashes.
    return s.replace('\x00\x00', '://').replace('\\', '/')


# ── Generic helpers ───────────────────────────────────────────────────────────

def run(*cmd, cwd=None, env=None):
    print(f">>> {' '.join(str(c) for c in cmd)}", flush=True)
    if platform.system() == "Windows":
        # Route every build command through MSYS2/MinGW64 so that autotools,
        # make, pkg-config, gfortran etc. are all available.
        parts = ["export PATH=/mingw64/bin:/usr/bin:$PATH"]
        if cwd:
            parts.append(f"cd {shlex.quote(_win_to_msys2(str(cwd)))}")
        parts.append(" ".join(shlex.quote(_win_to_msys2(str(c))) for c in cmd))
        subprocess.run([_MSYS2_BASH, "-lc", " && ".join(parts)],
                       check=True, env=env)
    else:
        subprocess.run(list(cmd), check=True, cwd=cwd, env=env)


def _is_x86_64() -> bool:
    return platform.machine().lower() in ("x86_64", "amd64")


def clone_if_missing(name, url, branch="master"):
    dest = os.path.join(THIS_DIR, name)
    if not os.path.exists(dest):
        # Use native git directly — avoids routing through MSYS2 where git
        # may not be on PATH, and avoids any path-conversion of the URL.
        print(f">>> git clone --depth 1 --branch {branch} {url} {dest}", flush=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, url, dest],
            check=True,
        )
    return dest


# ── Build OpenBLAS (static, with Fortran/LAPACK) ─────────────────────────────

def build_openblas(dest_dir, *, dynamic_arch=False, target=None):
    src = clone_if_missing(
        "OpenBLAS",
        "https://github.com/xianyi/OpenBLAS.git",
        OPENBLAS_TAG,
    )
    # OpenBLAS builds in-tree; always clean before each build so that a
    # second (AVX2) pass doesn't inherit object files from the first.
    run("make", "clean", cwd=src)

    make_vars = []
    if platform.system() == "Windows":
        make_vars.append("BINARY=64")
    if target:
        # Explicit CPU target (e.g. TARGET=HASWELL for AVX2 build).
        make_vars.append(f"TARGET={target}")
    elif dynamic_arch and platform.system() != "Windows":
        # DYNAMIC_ARCH=1 compiles multiple kernels and dispatches at runtime;
        # not used on Windows where the wheel is always x86_64 native.
        make_vars.append("DYNAMIC_ARCH=1")

    # Build static + shared libs (libs target skips test suite).
    # Building shared is required on all platforms so configure scripts
    # (CoinUtils LAPACK test) can link against the shared library — static
    # requires explicit Fortran runtime flags which is fragile.
    run("make", f"-j{NPROC}", "libs", "shared", *make_vars, cwd=src)
    run("make", *make_vars, f"PREFIX={dest_dir}", "install", cwd=src)


# ── Build SuiteSparse AMD (static only, direct compilation) ──────────────────

def build_amd():
    src = clone_if_missing(
        "SuiteSparse",
        "https://github.com/DrTimothyAldenDavis/SuiteSparse.git",
        SUITESPARSE_TAG,
    )
    ss_dir  = os.path.join(src, "SuiteSparse_config")
    amd_src = os.path.join(src, "AMD", "Source")
    amd_inc = os.path.join(src, "AMD", "Include")

    os.makedirs(LIB_DIR, exist_ok=True)
    inc_out = os.path.join(DIST_DIR, "include", "suitesparse")
    os.makedirs(inc_out, exist_ok=True)

    # AMD is a pure combinatorial/integer library — it doesn't use BLAS or
    # LAPACK at all.  Compiling directly from C source avoids the SuiteSparse
    # cmake build system which unconditionally runs FindBLAS (and fails when
    # only a static OpenBLAS is present because the link test needs the
    # Fortran runtime libraries).
    cc = os.environ.get("CC", "gcc")
    cflags = ["-O2", "-fPIC", f"-I{ss_dir}", f"-I{amd_inc}"]

    # SuiteSparse_config.c → libsuitesparseconfig.a
    ss_obj = os.path.join(THIS_DIR, "_ss_config.o")
    run(cc, *cflags, "-c",
        os.path.join(ss_dir, "SuiteSparse_config.c"), "-o", ss_obj)
    run("ar", "rcs", os.path.join(LIB_DIR, "libsuitesparseconfig.a"), ss_obj)

    # AMD/Source/*.c → libamd.a
    amd_objs = []
    for c_file in sorted(_glob.glob(os.path.join(amd_src, "*.c"))):
        obj = c_file[:-2] + ".o"
        run(cc, *cflags, "-c", c_file, "-o", obj)
        amd_objs.append(obj)
    run("ar", "rcs", os.path.join(LIB_DIR, "libamd.a"), *amd_objs)

    # Install headers
    for h in _glob.glob(os.path.join(amd_inc, "*.h")):
        shutil.copy2(h, inc_out)
    shutil.copy2(os.path.join(ss_dir, "SuiteSparse_config.h"), inc_out)


# ── Build nauty (static) ──────────────────────────────────────────────────────

def build_nauty():
    src = os.path.join(THIS_DIR, f"nauty{NAUTY_VERSION}")
    if not os.path.exists(src):
        tarball = os.path.join(THIS_DIR, f"nauty{NAUTY_VERSION}.tar.gz")
        if not os.path.exists(tarball):
            print(f"Downloading nauty from {NAUTY_URL}", flush=True)
            urllib.request.urlretrieve(NAUTY_URL, tarball)
        with tarfile.open(tarball) as tf:
            tf.extractall(THIS_DIR)

    # nauty ships its own configure; no --prefix support, so install manually.
    # Pass CFLAGS=-fPIC so the static archive can be linked into shared libs.
    run("./configure", "CFLAGS=-O2 -fPIC", cwd=src)
    run("make", "-j", NPROC, cwd=src)

    os.makedirs(LIB_DIR, exist_ok=True)
    inc = os.path.join(DIST_DIR, "include", "nauty")
    os.makedirs(inc, exist_ok=True)

    # nauty's Makefile produces "nauty.a" from source (distro packages rename
    # it to libnauty.a); accept either name.
    src_lib = os.path.join(src, "libnauty.a")
    if not os.path.exists(src_lib):
        src_lib = os.path.join(src, "nauty.a")
    shutil.copy2(src_lib, os.path.join(LIB_DIR, "libnauty.a"))
    for h in _glob.glob(os.path.join(src, "*.h")):
        shutil.copy2(h, inc)


# ── Build COIN-OR projects ────────────────────────────────────────────────────

def build_coin_or(dest_dir=None, extra_cxxflags=""):
    """Build the full COIN-OR stack and install into *dest_dir*.

    *extra_cxxflags* is appended to CXXFLAGS and can be used to enable
    architecture-specific optimisations (e.g. "-O3 -mavx2 -mfma -DCOIN_AVX2=4"
    for the Haswell-optimised build).
    """
    if dest_dir is None:
        dest_dir = DIST_DIR
    lib_dir = os.path.join(dest_dir, "lib")

    # AMD and nauty are pure combinatorial/integer libraries that do not
    # benefit from AVX2 and are only built once (into the base cbc_dist/).
    # Both COIN-OR variants can safely link against the same static archives.
    amd_inc   = os.path.join(DIST_DIR, "include", "suitesparse")
    nauty_inc = os.path.join(DIST_DIR, "include", "nauty")

    env = os.environ.copy()
    pkg_config_dir = os.path.join(lib_dir, "pkgconfig")
    # MSYS2 bash uses ':' as separator and MSYS2-format paths.
    if platform.system() == "Windows":
        env["PKG_CONFIG_PATH"] = (
            _win_to_msys2(pkg_config_dir) + ":" + env.get("PKG_CONFIG_PATH", "")
        )
    else:
        env["PKG_CONFIG_PATH"] = (
            pkg_config_dir + os.pathsep + env.get("PKG_CONFIG_PATH", "")
        )

    # Flags common to every project.
    # zlib is intentionally kept enabled (it is manylinux2014-allowed and
    # lets CBC read compressed MPS/LP files).
    common = [
        f"--prefix={dest_dir}",
        f"--libdir={lib_dir}",
        "--enable-static" if platform.system() != "Windows" else "--disable-static",
        "--enable-shared",      # produce .so/.dylib/.dll for cffi use
        "--disable-readline",   # libreadline not manylinux-allowed
        "--disable-bzlib",      # libbz2 not manylinux-allowed
        "--without-cholmod",    # use AMD instead
        "--without-glpk",       # not needed
        "--without-asl",        # AMPL solver library not needed
    ]
    if platform.system() == "Windows":
        # Declare both build and host as MinGW64 so that autoconf sets
        # cross_compiling=no (build==host) and uses the plain gcc/g++ from
        # /mingw64/bin rather than looking for x86_64-w64-mingw32-prefixed
        # cross-compiler tools.  With host_os=mingw32, libtool names DLLs as
        # lib*.dll (MinGW convention) rather than cyg*.dll (Cygwin convention).
        common += ["--build=x86_64-w64-mingw32", "--host=x86_64-w64-mingw32"]

    # Use a distinct build sub-directory per variant so that the generic and
    # AVX2 builds can coexist in the same cloned source tree.
    bld_suffix = "_build" if dest_dir == DIST_DIR else "_build_avx2"

    for name, url in COIN_REPOS:
        src = clone_if_missing(name, url)
        bld = os.path.join(src, bld_suffix)
        os.makedirs(bld, exist_ok=True)

        extra = []
        if name == "CoinUtils":
            # OpenBLAS provides both BLAS and LAPACK in one archive.
            # AMD provides fill-reducing ordering for sparse systems.
            extra += [
                f"--with-lapack-lflags=-L{lib_dir} -lopenblas",
                f"--with-amd-cflags=-I{amd_inc}",
                f"--with-amd-lflags=-L{LIB_DIR} -lamd -lsuitesparseconfig",
            ]
        elif name == "Clp":
            # Do NOT pass --with-amd-cflags here: Clp wraps #include <amd.h>
            # inside extern "C" {} in ClpCholeskyUfl.cpp, and SuiteSparse v7's
            # amd.h transitively includes C++ headers (<complex> etc.) which
            # clang rejects inside extern "C".  AMD ordering is still available
            # to CBC through CoinUtils which doesn't have this wrapping issue.
            extra += [
                f"--with-lapack-lflags=-L{lib_dir} -lopenblas",
            ]
        elif name == "Cbc":
            nauty_pthread = "" if platform.system() == "Windows" else " -lpthread"
            # Cbc's CbcSymmetry.hpp uses #include "nauty/nauty.h", so the
            # include flag must point to the parent of the nauty/ directory.
            nauty_parent = os.path.join(DIST_DIR, "include")
            extra += [
                f"--with-nauty-cflags=-I{nauty_parent}",
                f"--with-nauty-lflags=-L{LIB_DIR} -lnauty{nauty_pthread}",
                "--without-lapack",
                # Enable multi-threaded MIP search (parallel branch-and-bound).
                # Requires pthreads — available on all supported platforms.
                "--enable-cbc-parallel",
            ]
        else:  # Osi, Cgl — do not use LAPACK directly
            extra += ["--without-lapack"]

        configure = os.path.join(src, "configure")
        # clang (macOS) requires C++17 mode to accept aggregate assignment from
        # braced initializer lists (e.g. CoinDynamicConflictGraph.cpp).
        # -std=c++17 is harmless on GCC as well.
        # Note: -no-undefined is NOT passed here via LDFLAGS because it is a
        # libtool-specific flag, not a raw linker flag.  Passing it via LDFLAGS
        # causes configure's own link tests ("C compiler cannot create
        # executables") to fail with exit code 77 on MinGW.  COIN-OR's
        # AC_COIN_PROG_LIBTOOL macro already appends -no-undefined to
        # LT_LDFLAGS internally (aclocal.m4), which is the correct path —
        # it reaches libtool only when building shared libraries.
        cxxflags = f"-std=c++17{' ' + extra_cxxflags if extra_cxxflags else ''}"
        run(configure, *common, *extra, f"CXXFLAGS={cxxflags}", cwd=bld, env=env)
        run("make", "-j", NPROC, cwd=bld)
        run("make", "install", cwd=bld)


# ── Bundle dynamic dependencies ───────────────────────────────────────────────

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


def _soname_linux(lib_path: str) -> str:
    """Return the ELF SONAME of *lib_path*, falling back to its basename."""
    try:
        r = subprocess.run(
            ["patchelf", "--print-soname", lib_path],
            capture_output=True, text=True,
        )
        soname = r.stdout.strip()
        if soname:
            return soname
    except Exception:
        pass
    return os.path.basename(lib_path)


def _dynamic_deps_linux(path: str) -> dict:
    """Return {soname: resolved_path} for non-system deps on Linux."""
    out = subprocess.run(["ldd", path], capture_output=True, text=True).stdout
    deps = {}
    for line in out.splitlines():
        m = re.search(r"\s=>\s(/\S+)", line)
        if m and not _is_system_lib(m.group(1)):
            resolved = m.group(1)
            # Use the ELF soname as the destination filename so the dynamic
            # linker finds it even when ldd reports the versioned real file.
            deps[_soname_linux(resolved)] = resolved
    return deps


def _dynamic_deps_macos(path: str) -> list:
    """Return [install_name, ...] for non-system deps on macOS."""
    out = subprocess.run(
        ["otool", "-L", path], capture_output=True, text=True
    ).stdout
    deps = []
    for line in out.splitlines()[1:]:
        parts = line.strip().split()
        if parts and not _is_system_lib(parts[0]):
            deps.append(parts[0])
    return deps


def _dynamic_deps_windows(path: str) -> dict:
    """Return {dll_name: source_path} for non-system MinGW DLLs needed by *path*.

    Uses objdump (from MinGW64) to list DLL imports, then resolves each name
    against C:\\msys64\\mingw64\\bin\\ and DIST_DIR\\bin\\ (for DLLs installed
    by our own build, such as libopenblas.dll).
    """
    search_dirs = [r"C:\msys64\mingw64\bin", os.path.join(DIST_DIR, "bin")]
    r = subprocess.run(
        [_MSYS2_BASH, "-lc",
         "export PATH=/mingw64/bin:/usr/bin:$PATH && "
         f"objdump -p {shlex.quote(_win_to_msys2(path))} | grep 'DLL Name:'"],
        capture_output=True, text=True,
    )
    deps = {}
    for line in r.stdout.splitlines():
        m = re.search(r"DLL Name:\s+(\S+\.dll)", line, re.IGNORECASE)
        if m:
            name = m.group(1)
            if not _WIN_SYS_DLL.match(name):
                for search_dir in search_dirs:
                    candidate = os.path.join(search_dir, name)
                    if os.path.exists(candidate):
                        deps[name] = candidate
                        break
    return deps


def bundle_dynamic_deps(binary: str, lib_dir: str, _visited: set = None):
    """
    Inspect *binary* for non-system dynamic dependencies and handle them so
    the wheel is self-contained:

    Linux  — copies each .so to *lib_dir* and uses patchelf to set an
             $ORIGIN-relative RPATH on both the binary and every copied lib.
    macOS  — copies each .dylib to *lib_dir*, rewrites the install-name
             reference inside *binary* to @rpath/name, sets the copied
             lib's own id to @rpath/name, and adds an @loader_path rpath
             to the binary.
    Windows — copies each non-system MinGW DLL next to the binary (in its
              own directory); no rpath patching needed since Windows searches
              the executable's directory first.

    Recurses into copied libraries so transitive deps are also covered.
    If everything was statically linked this function is a no-op.
    """
    if _visited is None:
        _visited = set()
    os.makedirs(lib_dir, exist_ok=True)

    in_lib_dir = (
        os.path.dirname(os.path.realpath(binary)) == os.path.realpath(lib_dir)
    )

    if platform.system() == "Linux":
        rpath = "$ORIGIN" if in_lib_dir else "$ORIGIN/../lib"
        subprocess.run(["patchelf", "--set-rpath", rpath, binary], check=True)

        for name, src_path in _dynamic_deps_linux(binary).items():
            if name in _visited:
                continue
            _visited.add(name)
            dst = os.path.join(lib_dir, name)
            if not os.path.exists(dst):
                shutil.copy2(src_path, dst)
                os.chmod(dst, 0o755)
            bundle_dynamic_deps(dst, lib_dir, _visited)

    elif platform.system() == "Darwin":
        rpath = "@loader_path" if in_lib_dir else "@loader_path/../lib"
        # Silently ignore "already exists" errors from install_name_tool.
        subprocess.run(
            ["install_name_tool", "-add_rpath", rpath, binary],
            capture_output=True,
        )

        for install_name in _dynamic_deps_macos(binary):
            name = os.path.basename(install_name)
            if name in _visited:
                continue
            _visited.add(name)

            # Rewrite the hard-coded path in the binary to use @rpath.
            subprocess.run(
                ["install_name_tool", "-change", install_name, f"@rpath/{name}", binary],
                check=True,
            )
            dst = os.path.join(lib_dir, name)
            if not os.path.exists(dst):
                shutil.copy2(install_name, dst)
                os.chmod(dst, 0o755)
                # Give the copied lib a proper @rpath-relative install name.
                subprocess.run(
                    ["install_name_tool", "-id", f"@rpath/{name}", dst],
                    check=True,
                )
            bundle_dynamic_deps(dst, lib_dir, _visited)

    elif platform.system() == "Windows":
        # On Windows the loader finds DLLs in the same directory as the
        # executable. Copy all non-system MinGW DLLs there and recurse for
        # transitive dependencies (libgfortran → libquadmath, etc.).
        bin_dir = os.path.dirname(os.path.realpath(binary))
        for name, src_path in _dynamic_deps_windows(binary).items():
            if name in _visited:
                continue
            _visited.add(name)
            dst = os.path.join(bin_dir, name)
            if not os.path.exists(dst):
                shutil.copy2(src_path, dst)
                os.chmod(dst, 0o755)
            bundle_dynamic_deps(dst, lib_dir, _visited)


# ── Windows: mirror DLLs into lib/ ───────────────────────────────────────────

def copy_win_dlls_to_lib(dist_dir=None):
    """Copy every DLL from bin/ into lib/ as well.

    On Windows, libtool installs DLLs to bindir (bin/) and import libs
    (.dll.a) to libdir (lib/).  python-mip and other ctypes/cffi consumers
    locate libraries via cbcbox.cbc_lib_dir() which points to lib/, so all
    DLLs must also be present there — both the COIN-OR ones (libCbc.dll, …)
    and the bundled MinGW runtime DLLs they depend on.
    """
    if dist_dir is None:
        dist_dir = DIST_DIR
    bin_dir = os.path.join(dist_dir, "bin")
    lib_dir = os.path.join(dist_dir, "lib")
    os.makedirs(lib_dir, exist_ok=True)
    for dll in _glob.glob(os.path.join(bin_dir, "*.dll")):
        dst = os.path.join(lib_dir, os.path.basename(dll))
        if not os.path.exists(dst):
            shutil.copy2(dll, dst)



_cbc_exe = "cbc.exe" if platform.system() == "Windows" else "cbc"

if not os.path.exists(os.path.join(DIST_DIR, "bin", _cbc_exe)):
    build_openblas(DIST_DIR, dynamic_arch=True)
    build_amd()
    build_nauty()
    build_coin_or(DIST_DIR)

# AVX2-optimised build: x86_64 Linux and macOS only.
# Skipped on Windows because: (a) the CI build already takes ~67 min, and
# (b) all supported Windows CI runners are modern x86_64 machines anyway.
_build_avx2 = _is_x86_64() and platform.system() != "Windows"
if _build_avx2 and not os.path.exists(os.path.join(DIST_DIR_AVX2, "bin", _cbc_exe)):
    build_openblas(DIST_DIR_AVX2, target="HASWELL")
    build_coin_or(DIST_DIR_AVX2, extra_cxxflags="-O3 -mavx2 -mfma -DCOIN_AVX2=4")


def _bundle_dist(dist_dir):
    """Patch rpaths / bundle DLLs for all binaries and shared libs in *dist_dir*."""
    lib_dir    = os.path.join(dist_dir, "lib")
    bundle_dir = os.path.join(dist_dir, "bin") if platform.system() == "Windows" else lib_dir

    for bin_name in [_cbc_exe, "clp.exe" if platform.system() == "Windows" else "clp"]:
        bin_path = os.path.join(dist_dir, "bin", bin_name)
        if os.path.exists(bin_path):
            bundle_dynamic_deps(bin_path, bundle_dir)

    if platform.system() == "Windows":
        shared_pattern = os.path.join(dist_dir, "bin", "*.dll")
    elif platform.system() == "Darwin":
        shared_pattern = os.path.join(lib_dir, "*.dylib")
    else:
        shared_pattern = os.path.join(lib_dir, "*.so*")

    for lib_path in _glob.glob(shared_pattern):
        if not os.path.islink(lib_path):
            bundle_dynamic_deps(lib_path, bundle_dir)

    if platform.system() == "Windows":
        copy_win_dlls_to_lib(dist_dir)


_bundle_dist(DIST_DIR)
if _build_avx2 and os.path.isdir(DIST_DIR_AVX2):
    _bundle_dist(DIST_DIR_AVX2)


# ── Package ───────────────────────────────────────────────────────────────────

long_description = """\
**cbcbox** ships pre-built binaries of the
[CBC](https://github.com/coin-or/Cbc) MILP solver (COIN-OR Branch and Cut),
built from the latest master branch of the COIN-OR repositories.

Built with:
- OpenBLAS for optimised BLAS/LAPACK routines
- AMD reordering (SuiteSparse) for improved numerical performance
- Nauty for symmetry detection
- zlib for reading compressed MPS/LP files
"""

# setuptools requires package_dir values to be relative paths (not absolute).
# Use a staging dir inside THIS_DIR so we can pass a simple relative name.
_PKG_STAGING = "_cbcbox_pkg"
_pkg_dir = os.path.join(THIS_DIR, _PKG_STAGING)
if os.path.exists(_pkg_dir):
    shutil.rmtree(_pkg_dir)
os.makedirs(_pkg_dir)

try:
    dist_name = "cbc_dist"
    shutil.copytree(DIST_DIR, os.path.join(_pkg_dir, dist_name), dirs_exist_ok=True)

    package_data_patterns = [f"{dist_name}/**"]

    # Include the AVX2-optimised build when present (x86_64 Linux/macOS only).
    dist_name_avx2 = "cbc_dist_avx2"
    if os.path.isdir(DIST_DIR_AVX2):
        shutil.copytree(DIST_DIR_AVX2, os.path.join(_pkg_dir, dist_name_avx2),
                        dirs_exist_ok=True)
        package_data_patterns.append(f"{dist_name_avx2}/**")

    for fname in ["__init__.py", "__main__.py"]:
        shutil.copy2(os.path.join(THIS_DIR, "src", fname), os.path.join(_pkg_dir, fname))

    setup(
        cmdclass=cmdclass,
        long_description=long_description,
        long_description_content_type="text/markdown",
        packages=["cbcbox"],
        zip_safe=False,
        package_dir={"cbcbox": _PKG_STAGING},
        package_data={
            "cbcbox": package_data_patterns,
        },
    )
finally:
    shutil.rmtree(_pkg_dir, ignore_errors=True)

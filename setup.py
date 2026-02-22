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
from tempfile import TemporaryDirectory

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

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
DIST_DIR = os.path.join(THIS_DIR, "cbc_dist")
LIB_DIR  = os.path.join(DIST_DIR, "lib")
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
    Strings without drive letters pass through unchanged.
    """
    return re.sub(
        r'([A-Za-z]):[/\\]',
        lambda m: f"/{m.group(1).lower()}/",
        str(s),
    ).replace("\\", "/")


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


def clone_if_missing(name, url, branch="master"):
    dest = os.path.join(THIS_DIR, name)
    if not os.path.exists(dest):
        run("git", "clone", "--depth", "1", "--branch", branch, url, dest)
    return dest


# ── Build OpenBLAS (static, with Fortran/LAPACK) ─────────────────────────────

def build_openblas():
    src = clone_if_missing(
        "OpenBLAS",
        "https://github.com/xianyi/OpenBLAS.git",
        OPENBLAS_TAG,
    )
    # Build a static-only OpenBLAS with full LAPACK (Fortran) support.
    # libgfortran and libquadmath will be dynamic deps of the final binary;
    # bundle_dynamic_deps() detects and copies them into the wheel automatically.
    make_extra = ["BINARY=64"] if platform.system() == "Windows" else []
    run("make", f"-j{NPROC}", "NO_SHARED=1", *make_extra, cwd=src)
    run("make", "NO_SHARED=1", *make_extra, f"PREFIX={DIST_DIR}", "install", cwd=src)


# ── Build SuiteSparse AMD (static only) ───────────────────────────────────────

def build_amd():
    src = clone_if_missing(
        "SuiteSparse",
        "https://github.com/DrTimothyAldenDavis/SuiteSparse.git",
        SUITESPARSE_TAG,
    )
    bld = os.path.join(THIS_DIR, "_build_SuiteSparse")
    os.makedirs(bld, exist_ok=True)
    # On Windows use MinGW Makefiles so cmake drives the MinGW64 GCC toolchain.
    cmake_gen = (["-G", "MinGW Makefiles"] if platform.system() == "Windows" else [])
    run(
        "cmake", src,
        *cmake_gen,
        f"-DCMAKE_INSTALL_PREFIX={DIST_DIR}",
        "-DCMAKE_INSTALL_LIBDIR=lib",
        "-DCMAKE_BUILD_TYPE=Release",
        # AMD is a pure integer/combinatorial library that doesn't use BLAS
        # or LAPACK at all. Disable BLAS detection so cmake doesn't run a
        # FindBLAS link test (which would fail for a freshly-built static
        # OpenBLAS missing its gfortran runtime libs at test time).
        f"-DCMAKE_PREFIX_PATH={DIST_DIR}",
        "-DSUITESPARSE_USE_BLAS=OFF",
        "-DSUITESPARSE_USE_LAPACK=OFF",
        # Build static libs only; no shared libs to bundle.
        "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_STATIC_LIBS=ON",
        "-DSUITESPARSE_ENABLE_PROJECTS=amd",
        "-DSUITESPARSE_USE_OPENMP=OFF",   # avoids libgomp in static link
        "-DSUITESPARSE_USE_CUDA=OFF",
        "-DSUITESPARSE_USE_FORTRAN=OFF",
        "-DSUITESPARSE_DEMOS=OFF",
        cwd=bld,
    )
    run("cmake", "--build", bld, "--config", "Release", "--parallel", NPROC)
    run("cmake", "--install", bld)
    # AMD_static → libamd.a, SuiteSparseConfig_static → libsuitesparseconfig.a


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
    run("./configure", cwd=src)
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

def build_coin_or():
    amd_inc   = os.path.join(DIST_DIR, "include", "suitesparse")
    nauty_inc = os.path.join(DIST_DIR, "include", "nauty")

    env = os.environ.copy()
    pkg_config_dir = os.path.join(LIB_DIR, "pkgconfig")
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
        f"--prefix={DIST_DIR}",
        f"--libdir={LIB_DIR}",
        "--enable-static",
        "--disable-shared",
        "--disable-readline",   # libreadline not manylinux-allowed
        "--disable-bzlib",      # libbz2 not manylinux-allowed
        "--without-cholmod",    # use AMD instead
        "--without-glpk",       # not needed
        "--without-asl",        # AMPL solver library not needed
    ]

    for name, url in COIN_REPOS:
        src = clone_if_missing(name, url)
        bld = os.path.join(src, "_build")
        os.makedirs(bld, exist_ok=True)

        extra = []
        if name == "CoinUtils":
            # OpenBLAS provides both BLAS and LAPACK in one static archive.
            # libgfortran / libquadmath are dynamic deps that bundle_dynamic_deps
            # will copy into the wheel.
            extra += [f"--with-lapack-lflags=-L{LIB_DIR} -lopenblas"]
        elif name == "Clp":
            extra += [
                f"--with-amd-cflags=-I{amd_inc}",
                f"--with-amd-lflags=-L{LIB_DIR} -lamd -lsuitesparseconfig -lm",
                f"--with-lapack-lflags=-L{LIB_DIR} -lopenblas",
            ]
        elif name == "Cbc":
            nauty_pthread = "" if platform.system() == "Windows" else " -lpthread"
            extra += [
                f"--with-nauty-cflags=-I{nauty_inc}",
                f"--with-nauty-lflags=-L{LIB_DIR} -lnauty{nauty_pthread}",
                "--without-lapack",
            ]
        else:  # Osi, Cgl — do not use LAPACK directly
            extra += ["--without-lapack"]

        configure = os.path.join(src, "configure")
        # clang (macOS) requires C++17 mode to accept aggregate assignment from
        # braced initializer lists (e.g. CoinDynamicConflictGraph.cpp).
        # -std=c++17 is harmless on GCC as well.
        run(configure, *common, *extra, "CXXFLAGS=-std=c++17", cwd=bld, env=env)
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
    against C:\\msys64\\mingw64\\bin\\.
    """
    mingw_bin = r"C:\msys64\mingw64\bin"
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
                candidate = os.path.join(mingw_bin, name)
                if os.path.exists(candidate):
                    deps[name] = candidate
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


# ── Main build ────────────────────────────────────────────────────────────────

_cbc_exe = "cbc.exe" if platform.system() == "Windows" else "cbc"

if not os.path.exists(os.path.join(DIST_DIR, "bin", _cbc_exe)):
    build_openblas()
    build_amd()
    build_nauty()
    build_coin_or()

# Patch rpaths / bundle DLLs for every built binary.
for _bin_name in [_cbc_exe, "clp.exe" if platform.system() == "Windows" else "clp"]:
    _bin_path = os.path.join(DIST_DIR, "bin", _bin_name)
    if os.path.exists(_bin_path):
        # On Windows bundle into bin/ so DLLs sit next to the executable.
        _bundle_dir = os.path.join(DIST_DIR, "bin") if platform.system() == "Windows" else LIB_DIR
        bundle_dynamic_deps(_bin_path, _bundle_dir)


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

with TemporaryDirectory() as tmp_dir:
    dist_name = "cbc_dist"
    shutil.copytree(DIST_DIR, os.path.join(tmp_dir, dist_name), dirs_exist_ok=True)

    for fname in ["__init__.py", "__main__.py"]:
        shutil.copy2(os.path.join(THIS_DIR, "src", fname), os.path.join(tmp_dir, fname))

    setup(
        name="cbcbox",
        version="2.10.12",
        cmdclass=cmdclass,
        description="cbcbox: binary distribution of the CBC MILP solver",
        long_description=long_description,
        long_description_content_type="text/markdown",
        license="EPL-2.0",
        packages=["cbcbox"],
        zip_safe=False,
        package_dir={"cbcbox": tmp_dir},
        package_data={
            "cbcbox": [f"{dist_name}/**"],
        },
    )

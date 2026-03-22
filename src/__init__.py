import glob as _glob
import os
import platform
import subprocess


def _has_avx2() -> bool:
    """Return True if the running CPU supports AVX2 instructions."""
    if platform.machine().lower() not in ("x86_64", "amd64"):
        return False
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("flags"):
                        return "avx2" in line.split(":", 1)[1].split()
        elif platform.system() == "Darwin":
            r = subprocess.run(
                ["sysctl", "-n", "hw.optional.avx2_0"],
                capture_output=True, text=True,
            )
            return r.stdout.strip() == "1"
        elif os.name == "nt":
            import ctypes
            # PF_AVX2_INSTRUCTIONS_AVAILABLE = 40
            return bool(ctypes.windll.kernel32.IsProcessorFeaturePresent(40))
    except Exception:
        pass
    return False


def _print_build_info(dist_dir: str) -> None:
    """Print a short summary of the selected build to stdout."""
    cbc_exe  = "cbc.exe" if os.name == "nt" else "cbc"
    cbc_bin  = os.path.join(dist_dir, "bin", cbc_exe)
    lib_dir  = os.path.join(dist_dir, "lib")
    libs     = sorted(
        os.path.basename(p)
        for p in _glob.glob(os.path.join(lib_dir, "libCbc*"))
               + _glob.glob(os.path.join(lib_dir, "libClp*"))
               + _glob.glob(os.path.join(lib_dir, "libopenblas*"))
        if not os.path.islink(p)
    )
    # Check debug_avx2 before avx2 — the name ends with _avx2 in both cases.
    variant  = (
        "debug_avx2" if dist_dir.endswith("_debug_avx2")
        else "avx2"  if dist_dir.endswith("_avx2")
        else "debug" if dist_dir.endswith("_debug")
        else "generic"
    )
    print(f"[cbcbox] CBCBOX_BUILD={variant}")
    print(f"[cbcbox]   binary  : {cbc_bin}")
    print(f"[cbcbox]   lib dir : {lib_dir}")
    if libs:
        print(f"[cbcbox]   libs    : {', '.join(libs)}")


def cbc_dist_dir() -> str:
    pkg_dir        = os.path.abspath(os.path.dirname(__file__))
    base_dir       = os.path.join(pkg_dir, "cbc_dist")
    avx2_dir       = os.path.join(pkg_dir, "cbc_dist_avx2")
    debug_dir      = os.path.join(pkg_dir, "cbc_dist_debug")
    debug_avx2_dir = os.path.join(pkg_dir, "cbc_dist_debug_avx2")

    override = os.environ.get("CBCBOX_BUILD", "").strip().lower()
    if override == "avx2":
        if not os.path.isdir(avx2_dir):
            raise RuntimeError(
                "CBCBOX_BUILD=avx2 requested but the AVX2 build is not "
                "present in this installation (x86_64 Linux/macOS/Windows only)."
            )
        chosen = avx2_dir
    elif override == "debug":
        # On x86_64 the only debug variant shipped is debug+AVX2 (haswell).
        # On other architectures the plain debug build is used.
        if os.path.isdir(debug_avx2_dir):
            chosen = debug_avx2_dir
        elif os.path.isdir(debug_dir):
            chosen = debug_dir
        else:
            raise RuntimeError(
                "CBCBOX_BUILD=debug requested but no debug build is present "
                "in this installation."
            )
    elif override == "generic":
        chosen = base_dir
    elif override:
        raise ValueError(
            f"Unknown CBCBOX_BUILD value {override!r}. "
            "Use 'generic', 'avx2', or 'debug'."
        )
    else:
        # Auto-select: prefer AVX2 when available and supported by the CPU.
        chosen = avx2_dir if os.path.isdir(avx2_dir) and _has_avx2() else base_dir

    verbose = os.environ.get("CBCBOX_VERBOSE", "").strip() == "1"
    if override or verbose:
        _print_build_info(chosen)

    return chosen


def cbc_bin_path() -> str:
    return os.path.join(cbc_dist_dir(), "bin", "cbc.exe" if os.name == "nt" else "cbc")


def cbc_include_dir() -> str:
    return os.path.join(cbc_dist_dir(), "include", "coin")


def cbc_lib_dir() -> str:
    return os.path.join(cbc_dist_dir(), "lib")

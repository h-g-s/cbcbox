#!/usr/bin/env bash
# build_debug.sh — Build a debug-enabled CBC binary locally (native build).
#
# Supports Linux and macOS.  For Linux, this script builds natively against the
# host system's libraries.  If you need an exact manylinux2014-compatible binary
# (matching CI), use build_debug_manylinux.sh instead.
#
# Variant selection (automatic, based on host architecture):
#   x86_64 / AMD64  →  CBCBOX_BUILD_VARIANT=debug_avx2
#                       Flags: -O1 -g -march=haswell -DCOIN_AVX2=4
#                       Output: cbc_dist_debug_avx2/bin/cbc
#
#   ARM64 / aarch64 →  CBCBOX_BUILD_VARIANT=debug
#                       Flags: -O1 -g -fno-omit-frame-pointer
#                       Output: cbc_dist_debug/bin/cbc
#
# All builds include: OpenBLAS (-O1 -g, no sanitizer), AMD (SuiteSparse),
# Nauty, pthreads.  OpenBLAS is always built without sanitizer flags to avoid
# false positives from hand-optimised BLAS kernels.
#
# Sanitizer options (Linux and macOS only; mutually exclusive):
#   --asan   AddressSanitizer  (-fsanitize=address)
#   --tsan   ThreadSanitizer   (-fsanitize=thread)
#
# Prerequisites:
#   Common:  python3, pip, make, autoconf, automake, libtool, pkg-config
#   Linux:   gcc, g++, gfortran, patchelf
#            Ubuntu/Debian: sudo apt-get install gcc g++ gfortran patchelf make \
#                             autoconf automake libtool pkg-config
#            RHEL/CentOS:  sudo yum install gcc gcc-c++ gcc-gfortran patchelf make \
#                             autoconf automake libtool pkgconfig
#   macOS:   Xcode command-line tools + gfortran
#            brew install gcc  (provides gfortran)
#
# Usage:
#   ./scripts/build_debug.sh [--asan] [--tsan] [--clean]
#
#   --asan   Enable AddressSanitizer (Linux/macOS only).
#   --tsan   Enable ThreadSanitizer  (Linux/macOS only).
#   --clean  Delete the output directory before building (force full rebuild).
#            Always use --clean when switching sanitizers.
#
# After a successful build, run the solver:
#   cbc_dist_debug_avx2/bin/cbc --help          # x86_64
#   cbc_dist_debug/bin/cbc --help               # ARM64
#
# Debugging with GDB (Linux):
#   gdb cbc_dist_debug_avx2/bin/cbc
#   (gdb) run mymodel.mps
#
# Debugging with LLDB (macOS):
#   lldb cbc_dist_debug/bin/cbc
#   (lldb) run mymodel.mps
#
# Note on AddressSanitizer:
#   If you see false positives from system libraries, suppress them with:
#     ASAN_OPTIONS=detect_leaks=0 cbc_dist_debug_avx2/bin/cbc mymodel.mps
#
# Note on ThreadSanitizer:
#   TSan reports data races.  Run with:
#     TSAN_OPTIONS=halt_on_error=0 cbc_dist_debug_avx2/bin/cbc mymodel.mps

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ── Parse arguments ───────────────────────────────────────────────────────────
CLEAN=0
SANITIZE=""
for arg in "$@"; do
    case "$arg" in
        --clean) CLEAN=1 ;;
        --asan)  SANITIZE="address" ;;
        --tsan)  SANITIZE="thread"  ;;
        *) echo "Unknown argument: $arg"; echo "Usage: $0 [--asan] [--tsan] [--clean]"; exit 1 ;;
    esac
done

if [[ "$SANITIZE" == "address" && "$(uname -s)" == "Windows_NT" ]]; then
    echo "ERROR: --asan is not supported on Windows."
    exit 1
fi
if [[ "$SANITIZE" == "thread" && "$(uname -s)" == "Windows_NT" ]]; then
    echo "ERROR: --tsan is not supported on Windows."
    exit 1
fi

# ── Detect architecture ───────────────────────────────────────────────────────
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64|amd64)
        VARIANT="debug_avx2"
        OUT_DIR="$REPO_ROOT/cbc_dist_debug_avx2"
        ;;
    arm64|aarch64)
        VARIANT="debug"
        OUT_DIR="$REPO_ROOT/cbc_dist_debug"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

OS="$(uname -s)"
echo "==> cbcbox debug build"
echo "    OS:        $OS"
echo "    Arch:      $ARCH"
echo "    Variant:   $VARIANT"
echo "    Sanitizer: ${SANITIZE:-none}"
echo "    Output:    $OUT_DIR"
echo ""

# ── Optional clean ────────────────────────────────────────────────────────────
if [[ $CLEAN -eq 1 ]]; then
    echo "==> Cleaning output directory: $OUT_DIR"
    rm -rf "$OUT_DIR"
    # Also wipe build subdirectories inside source trees so COIN-OR reconfigures.
    for name in CoinUtils Osi Clp Cgl Cbc; do
        bld_dir="$REPO_ROOT/$name/_build_debug"
        bld_dir_avx2="$REPO_ROOT/$name/_build_debug_avx2"
        [[ -d "$bld_dir" ]]      && { echo "    Removing $bld_dir";      rm -rf "$bld_dir"; }
        [[ -d "$bld_dir_avx2" ]] && { echo "    Removing $bld_dir_avx2"; rm -rf "$bld_dir_avx2"; }
    done
    echo ""
fi

# ── Check prerequisites ───────────────────────────────────────────────────────
check_cmd() {
    command -v "$1" &>/dev/null || {
        echo "ERROR: '$1' not found. $2"
        exit 1
    }
}

check_cmd python3    "Install Python 3."
check_cmd gfortran   "Install gfortran. On macOS: brew install gcc. On Linux: apt-get install gfortran."
check_cmd make       "Install make."
check_cmd autoconf   "Install autoconf."
check_cmd automake   "Install automake."
check_cmd libtool    "Install libtool."
check_cmd pkg-config "Install pkg-config."

if [[ "$OS" == "Linux" ]]; then
    # patchelf is required to set RPATH on Linux binaries.
    if ! command -v patchelf &>/dev/null; then
        echo "==> patchelf not found; attempting to install via pip..."
        python3 -m pip install --quiet patchelf || {
            echo "ERROR: patchelf is required on Linux."
            echo "  Install with: sudo apt-get install patchelf"
            echo "           or:  pip install patchelf"
            exit 1
        }
    fi
fi

# Ensure setuptools and wheel are available.
python3 -m pip install --quiet setuptools wheel

# ── Build ─────────────────────────────────────────────────────────────────────
echo "==> Starting build (this will take a while)..."
echo "    Logs will appear below."
echo ""

CBCBOX_BUILD_VARIANT="$VARIANT" \
CBCBOX_BUILD_ONLY=1 \
CBCBOX_SANITIZE="$SANITIZE" \
    python3 setup.py build_ext

# ── Report ────────────────────────────────────────────────────────────────────
CBC_BIN="$OUT_DIR/bin/cbc"
if [[ -x "$CBC_BIN" ]]; then
    echo ""
    echo "==> Build successful!"
    echo ""
    echo "    Binary:  $CBC_BIN"
    echo "    Libs:    $OUT_DIR/lib/"
    echo ""
    echo "    Quick smoke test:"
    echo "      $CBC_BIN -solve -quit"
    echo ""
    if [[ "$VARIANT" == "debug_avx2" ]]; then
        echo "    GDB (Linux):   gdb $CBC_BIN"
        echo "    LLDB (macOS):  lldb $CBC_BIN"
    fi
    if [[ "$SANITIZE" == "address" ]]; then
        echo ""
        echo "    ASan tip: suppress false positives from system libs:"
        echo "      ASAN_OPTIONS=detect_leaks=0 $CBC_BIN mymodel.mps"
    elif [[ "$SANITIZE" == "thread" ]]; then
        echo ""
        echo "    TSan tip: continue on race reports instead of halting:"
        echo "      TSAN_OPTIONS=halt_on_error=0 $CBC_BIN mymodel.mps"
    fi
else
    echo ""
    echo "ERROR: Build completed but $CBC_BIN was not found."
    exit 1
fi

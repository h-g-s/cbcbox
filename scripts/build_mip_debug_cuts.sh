#!/usr/bin/env bash
# Compile Cbc/test/mip-debug-cuts.cpp against a freshly-built debug COIN-OR
# stack and drop the resulting binary into <dist_dir>/bin/, so it travels
# with the rest of the debug artifact tarball uploaded by the "Compile ...
# debug" CI jobs and is available to the downstream "Package ... wheel" jobs
# (see tests/conftest.py's automatic mip-debug-cuts invocation on an
# objective-mismatch test_solve failure).
#
# mip-debug-cuts activates Osi's row-cut debugger; the CoinAssert checks it
# relies on require a non-NDEBUG ("--debug") Cbc build, which is exactly
# what cbc_dist_debug*/  already is (see setup.py's _DEBUG_CFLAGS -- no
# -DNDEBUG is ever added to the debug variant's CXXFLAGS).
#
# Usage: build_mip_debug_cuts.sh <dist_dir> [<Cbc-source-dir>]
#   <dist_dir>        e.g. cbc_dist_debug or cbc_dist_debug_avx2
#   <Cbc-source-dir>  defaults to ./Cbc (cloned at the repo root by setup.py)
#
# Silently does nothing (exit 0) if the Cbc source tree or the debug binary
# are not present -- this keeps the step harmless to run unconditionally.
set -euo pipefail

DIST_DIR="${1:?usage: build_mip_debug_cuts.sh <dist_dir> [<Cbc-source-dir>]}"
CBC_SRC="${2:-Cbc}"

if [ ! -f "${CBC_SRC}/test/mip-debug-cuts.cpp" ]; then
  echo "[build_mip_debug_cuts] ${CBC_SRC}/test/mip-debug-cuts.cpp not found -- skipping."
  exit 0
fi
if [ ! -d "${DIST_DIR}/lib" ]; then
  echo "[build_mip_debug_cuts] ${DIST_DIR}/lib not found -- skipping."
  exit 0
fi

INCLUDE_DIR="${DIST_DIR}/include/coin-or"
LIB_DIR="${DIST_DIR}/lib"
BIN_DIR="${DIST_DIR}/bin"
mkdir -p "${BIN_DIR}"

OUT="${BIN_DIR}/mip-debug-cuts"
CXX="${CXX:-c++}"

case "$(uname -s)" in
  Darwin)
    RPATH_FLAGS=(-Wl,-rpath,@loader_path/../lib)
    ;;
  MINGW*|MSYS*|CYGWIN*)
    OUT="${BIN_DIR}/mip-debug-cuts.exe"
    RPATH_FLAGS=()
    ;;
  *)
    RPATH_FLAGS=(-Wl,-rpath,'$ORIGIN/../lib')
    ;;
esac

echo "[build_mip_debug_cuts] compiling ${OUT} against ${DIST_DIR} ..."
"${CXX}" -std=c++17 -O0 -g \
  -I"${INCLUDE_DIR}" \
  "${CBC_SRC}/test/mip-debug-cuts.cpp" \
  -o "${OUT}" \
  -L"${LIB_DIR}" -lCbc \
  "${RPATH_FLAGS[@]}"

echo "[build_mip_debug_cuts] built ${OUT}"

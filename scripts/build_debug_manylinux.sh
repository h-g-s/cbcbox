#!/usr/bin/env bash
# build_debug_manylinux.sh — Build a debug-enabled CBC binary inside a
# manylinux2014 Docker container, matching the CI build environment exactly.
#
# This is the recommended approach when you need the debug binary to be
# ABI-compatible with the CI release wheels (e.g. for reproducing a bug that
# only appears in the manylinux build).  For quick local debugging without
# Docker, use build_debug.sh instead.
#
# Variant selection (automatic, based on host architecture):
#   x86_64  →  CBCBOX_BUILD_VARIANT=debug_avx2
#               Container: quay.io/pypa/manylinux2014_x86_64
#               Flags: -O1 -g -march=haswell -DCOIN_AVX2=4
#               Output: cbc_dist_debug_avx2/bin/cbc
#
#   aarch64 →  CBCBOX_BUILD_VARIANT=debug
#               Container: quay.io/pypa/manylinux2014_aarch64
#               Flags: -O1 -g -fno-omit-frame-pointer
#               Output: cbc_dist_debug/bin/cbc
#
# Prerequisites:
#   - Docker (with the ability to run Linux containers)
#
# Usage:
#   ./scripts/build_debug_manylinux.sh [--asan] [--tsan] [--clean]
#
#   --asan   Enable AddressSanitizer.  libasan is provided by the manylinux2014
#            GCC toolchain on both architectures.
#   --tsan   Enable ThreadSanitizer.
#   --clean  Delete the output directory before building (force full rebuild).
#            Always use --clean when switching sanitizers.
#
# Note on source-level debugging:
#   The binary is built inside a container, but the source files are bind-
#   mounted from your working tree at /project.  GDB/LLDB will resolve source
#   paths automatically as long as you run the debugger from the same repo root,
#   or use: (gdb) set substitute-path /project <repo-root>
#
# Note on file ownership:
#   Files created inside the container are owned by root.  The script fixes
#   ownership automatically after the container exits.

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

# ── Check prerequisites ───────────────────────────────────────────────────────
command -v docker &>/dev/null || {
    echo "ERROR: Docker is not installed or not in PATH."
    echo ""
    echo "  ── Easiest install (all distros, recommended) ─────────────────────────"
    echo "  The official convenience script detects your OS automatically:"
    echo ""
    echo "    curl -fsSL https://get.docker.com | sh"
    echo "    sudo systemctl enable --now docker  # creates the 'docker' group"
    echo "    sudo usermod -aG docker \$USER       # then log out and back in"
    echo ""
    echo "  ── Manual install ─────────────────────────────────────────────────────"
    echo "  NOTE: run these in bash (not fish/zsh): type 'bash' first if needed."
    echo ""
    # Detect the distro so we only show the relevant block.
    _distro_id=$(bash -c '. /etc/os-release 2>/dev/null && echo "${ID:-}"' 2>/dev/null || true)
    case "$_distro_id" in
        ubuntu)
            echo "  Detected: Ubuntu"
            echo "    sudo apt-get update && sudo apt-get install -y ca-certificates curl"
            echo "    sudo install -m 0755 -d /etc/apt/keyrings"
            echo "    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \\"
            echo "         -o /etc/apt/keyrings/docker.asc && sudo chmod a+r /etc/apt/keyrings/docker.asc"
            echo "    echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \\"
            echo "         https://download.docker.com/linux/ubuntu \$(bash -c '. /etc/os-release && echo \"\$VERSION_CODENAME\"') stable\" \\"
            echo "         | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null"
            echo "    sudo apt-get update  # warnings from unrelated repos are OK"
            echo "    sudo apt-get install -y docker-ce docker-ce-cli containerd.io"
            echo "    sudo systemctl enable --now docker"
            echo "    sudo usermod -aG docker \$USER  # then log out and back in"
            ;;
        debian)
            echo "  Detected: Debian"
            echo "    # Remove any stale docker.list from a previous attempt first:"
            echo "    sudo rm -f /etc/apt/sources.list.d/docker.list"
            echo "    sudo apt-get update && sudo apt-get install -y ca-certificates curl"
            echo "    sudo install -m 0755 -d /etc/apt/keyrings"
            echo "    sudo curl -fsSL https://download.docker.com/linux/debian/gpg \\"
            echo "         -o /etc/apt/keyrings/docker.asc && sudo chmod a+r /etc/apt/keyrings/docker.asc"
            echo "    echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \\"
            echo "         https://download.docker.com/linux/debian \$(bash -c '. /etc/os-release && echo \"\$VERSION_CODENAME\"') stable\" \\"
            echo "         | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null"
            echo "    sudo apt-get update  # warnings from unrelated repos are OK"
            echo "    sudo apt-get install -y docker-ce docker-ce-cli containerd.io"
            echo "    sudo systemctl enable --now docker"
            echo "    sudo usermod -aG docker \$USER  # then log out and back in"
            ;;
        fedora|rhel|centos|rocky|almalinux)
            echo "  Detected: Fedora / RHEL / CentOS / Rocky / AlmaLinux"
            echo "    sudo dnf -y install dnf-plugins-core"
            echo "    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo"
            echo "    sudo dnf install -y docker-ce docker-ce-cli containerd.io"
            echo "    sudo systemctl enable --now docker"
            echo "    sudo usermod -aG docker \$USER  # then log out and back in"
            ;;
        *)
            echo "  See the full install guide for your distro:"
            echo "    https://docs.docker.com/engine/install/"
            ;;
    esac
    echo ""
    echo "  Full docs: https://docs.docker.com/engine/install/"
    exit 1
}

docker info &>/dev/null || {
    echo "ERROR: Docker daemon is not running or you lack permission to use it."
    echo ""
    echo "  Start the daemon:"
    echo "    sudo systemctl start docker"
    echo "    sudo systemctl enable docker   # start automatically on boot"
    echo ""
    echo "  If you get a permission error, add yourself to the docker group:"
    echo "    sudo usermod -aG docker \$USER"
    echo "  Then log out and back in (or run: newgrp docker)."
    exit 1
}

# ── Detect architecture ───────────────────────────────────────────────────────
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64|amd64)
        VARIANT="debug_avx2"
        IMAGE="quay.io/pypa/manylinux2014_x86_64"
        OUT_DIR="$REPO_ROOT/cbc_dist_debug_avx2"
        ;;
    aarch64|arm64)
        VARIANT="debug"
        IMAGE="quay.io/pypa/manylinux2014_aarch64"
        OUT_DIR="$REPO_ROOT/cbc_dist_debug"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        echo "Supported: x86_64, aarch64"
        exit 1
        ;;
esac

echo "==> cbcbox debug build (manylinux2014 container)"
echo "    Arch:      $ARCH"
echo "    Variant:   $VARIANT"
echo "    Sanitizer: ${SANITIZE:-none}"
echo "    Container: $IMAGE"
echo "    Output:    $OUT_DIR"
echo ""

# ── Optional clean ────────────────────────────────────────────────────────────
if [[ $CLEAN -eq 1 ]]; then
    echo "==> Cleaning output directory: $OUT_DIR"
    # Use Docker to remove root-owned files if necessary.
    if [[ -d "$OUT_DIR" ]]; then
        docker run --rm -v "$REPO_ROOT:/project" "$IMAGE" \
            bash -c "rm -rf /project/$(basename "$OUT_DIR")"
    fi
    # Wipe COIN-OR build subdirectories.
    for name in CoinUtils Osi Clp Cgl Cbc; do
        for suffix in _build_debug _build_debug_avx2; do
            bld_dir="$REPO_ROOT/$name/$suffix"
            if [[ -d "$bld_dir" ]]; then
                echo "    Removing $bld_dir"
                docker run --rm -v "$REPO_ROOT:/project" "$IMAGE" \
                    bash -c "rm -rf /project/$name/$suffix"
            fi
        done
    done
    echo ""
fi

# ── Build inside container ────────────────────────────────────────────────────
echo "==> Pulling container image (cached if already present)..."
docker pull "$IMAGE"
echo ""
echo "==> Starting build inside container (this will take a while)..."
echo ""

docker run --rm \
    -v "$REPO_ROOT:/project" \
    -e CBCBOX_BUILD_VARIANT="$VARIANT" \
    -e CBCBOX_BUILD_ONLY=1 \
    -e CBCBOX_SANITIZE="$SANITIZE" \
    "$IMAGE" \
    bash -c '
        set -euo pipefail
        export PATH=/opt/python/cp313-cp313/bin:$PATH
        yum install -y gcc-gfortran >/dev/null
        pip install --quiet setuptools wheel patchelf
        cd /project
        python setup.py build_ext
    '

# ── Fix ownership (files created as root inside the container) ────────────────
if [[ -d "$OUT_DIR" ]]; then
    sudo chown -R "$USER:$(id -gn)" "$OUT_DIR" 2>/dev/null || true
fi

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
    echo "    GDB:   gdb $CBC_BIN"
    echo ""
    echo "    Note: debug symbols reference source paths under /project/ (the"
    echo "    container mount point).  GDB will find them automatically when run"
    echo "    from this repo root, or use:"
    echo "      (gdb) set substitute-path /project $REPO_ROOT"
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

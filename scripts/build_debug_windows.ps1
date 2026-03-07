# build_debug_windows.ps1 — Build a debug-enabled CBC binary on Windows using
# MSYS2/MinGW64.
#
# Mirrors the CI compile-windows job but with CBCBOX_BUILD_VARIANT=debug_avx2,
# producing a binary with full debug symbols and AVX2 code paths enabled.
#
# Variant: debug_avx2 (Windows is always x86_64 / AMD64)
#   Flags:  -O1 -g -march=haswell -fno-omit-frame-pointer -DCOIN_AVX2=4
#   Output: cbc_dist_debug_avx2\bin\cbc.exe
#
# All features: OpenBLAS (-O1 -g), AMD (SuiteSparse), Nauty, pthreads.
# Note: AddressSanitizer is not available with MinGW64.
#
# Prerequisites:
#   - MSYS2 installed at C:\msys64 (https://www.msys2.org/)
#   - Python 3 with pip (python.exe must be in PATH or virtual env activated)
#
# Usage:
#   .\scripts\build_debug_windows.ps1 [-Clean]
#
#   -Clean  Delete the output directory before building (force full rebuild).
#
# After a successful build, run the solver:
#   cbc_dist_debug_avx2\bin\cbc.exe --help
#
# Debugging with GDB (MinGW64):
#   C:\msys64\mingw64\bin\gdb.exe cbc_dist_debug_avx2\bin\cbc.exe

[CmdletBinding()]
param(
    [switch]$Asan,
    [switch]$Tsan,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

if ($Asan -and $Tsan) {
    Write-Error "-Asan and -Tsan are mutually exclusive."
    exit 1
}
if ($Asan -or $Tsan) {
    Write-Warning "AddressSanitizer and ThreadSanitizer are not supported by MinGW64 on Windows."
    Write-Warning "The -Asan / -Tsan flags are ignored.  Use WSL2 with build_debug.sh for sanitizer builds."
}

$Sanitize = ""   # Windows: sanitizers not available

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$MSYS2Bash = "C:\msys64\usr\bin\bash.exe"
$Variant   = "debug_avx2"
$OutDir    = Join-Path $RepoRoot "cbc_dist_debug_avx2"

Write-Host "==> cbcbox debug build (Windows / MSYS2 MinGW64)" -ForegroundColor Cyan
Write-Host "    Variant:   $Variant"
Write-Host "    Sanitizer: none (not supported on Windows/MinGW)"
Write-Host "    Output:    $OutDir"
Write-Host ""

# ── Check prerequisites ───────────────────────────────────────────────────────
if (-not (Test-Path $MSYS2Bash)) {
    Write-Error @"
MSYS2 not found at C:\msys64.
Install MSYS2 from https://www.msys2.org/ and run the first-time setup.
"@
    exit 1
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "python.exe not found in PATH. Install Python 3 or activate a virtual environment."
    exit 1
}

# ── Optional clean ────────────────────────────────────────────────────────────
if ($Clean) {
    Write-Host "==> Cleaning output directory: $OutDir"
    if (Test-Path $OutDir) {
        Remove-Item -Recurse -Force $OutDir
    }
    # Wipe COIN-OR debug_avx2 build subdirectories.
    foreach ($name in @("CoinUtils", "Osi", "Clp", "Cgl", "Cbc")) {
        $bld = Join-Path $RepoRoot "$name\_build_debug_avx2"
        if (Test-Path $bld) {
            Write-Host "    Removing $bld"
            Remove-Item -Recurse -Force $bld
        }
    }
    Write-Host ""
}

# ── Install MinGW64 toolchain via pacman ──────────────────────────────────────
Write-Host "==> Installing MinGW64 toolchain via pacman..."
$pacmanCmd = @"
export PATH=/mingw64/bin:/usr/bin:\$PATH
pacman -Sy --noconfirm 2>&1 | tail -3
pacman -S --needed --noconfirm \
    mingw-w64-x86_64-gcc \
    mingw-w64-x86_64-gcc-fortran \
    make \
    autoconf automake libtool pkg-config 2>&1 | tail -5
"@
& $MSYS2Bash -lc $pacmanCmd
if ($LASTEXITCODE -ne 0) {
    Write-Error "pacman setup failed."
    exit 1
}

# ── Install Python build dependencies ────────────────────────────────────────
Write-Host "==> Installing Python build dependencies..."
python -m pip install --quiet setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed."
    exit 1
}

# ── Build ─────────────────────────────────────────────────────────────────────
Write-Host "==> Starting build (this will take a while)..."
Write-Host ""

$env:CBCBOX_BUILD_VARIANT = $Variant
$env:CBCBOX_BUILD_ONLY    = "1"

python setup.py build_ext
$buildExitCode = $LASTEXITCODE

Remove-Item Env:\CBCBOX_BUILD_VARIANT -ErrorAction SilentlyContinue
Remove-Item Env:\CBCBOX_BUILD_ONLY    -ErrorAction SilentlyContinue

if ($buildExitCode -ne 0) {
    Write-Error "Build failed with exit code $buildExitCode."
    exit $buildExitCode
}

# ── Report ────────────────────────────────────────────────────────────────────
$CbcBin = Join-Path $OutDir "bin\cbc.exe"
if (Test-Path $CbcBin) {
    Write-Host ""
    Write-Host "==> Build successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "    Binary:  $CbcBin"
    Write-Host "    Libs:    $(Join-Path $OutDir 'lib')"
    Write-Host ""
    Write-Host "    Quick smoke test:"
    Write-Host "      & '$CbcBin' -solve -quit"
    Write-Host ""
    Write-Host "    GDB (MinGW64):"
    Write-Host "      C:\msys64\mingw64\bin\gdb.exe '$CbcBin'"
} else {
    Write-Error "Build completed but $CbcBin was not found."
    exit 1
}

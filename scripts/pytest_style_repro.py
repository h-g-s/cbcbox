"""Reproduce the Windows generic-variant CBC crash using the exact same
subprocess invocation pattern as tests/test_solve.py::_solve_and_get_obj
(subprocess.run with capture_output=True), instead of a direct/gdb-piped
invocation. Prints the raw returncode, which on Windows directly identifies
the crash type (e.g. -1073741819 = 0xC0000005 = STATUS_ACCESS_VIOLATION,
-1073740791 = 0xC0000409 = STATUS_STACK_BUFFER_OVERRUN /GS failure,
-1073741795 = 0xC000001D = STATUS_ILLEGAL_INSTRUCTION, etc.) without
needing a debugger attached at all.
"""
import os
import subprocess
import sys
import time

CBC_BIN = sys.argv[1]
MPS_DIR = sys.argv[2]
INSTANCES = sys.argv[3:]


def run_one(mps_file, seconds=120):
    cmd = [CBC_BIN, mps_file, f"-seconds={seconds}", "-timem", "elapsed", "-solve", "-quit"]
    env = os.environ.copy()
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=seconds + 120, env=env)
    elapsed = time.time() - t0
    return result, elapsed


for inst in INSTANCES:
    mps_file = os.path.join(MPS_DIR, f"{inst}.mps.gz")
    print(f"=== {inst} ===", flush=True)
    try:
        result, elapsed = run_one(mps_file)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after full budget", flush=True)
        continue
    # Hex form makes it easy to look up the NTSTATUS code.
    rc = result.returncode
    rc_hex = f"0x{rc & 0xFFFFFFFF:08X}" if rc < 0 else hex(rc)
    print(f"  returncode={rc} ({rc_hex})  elapsed={elapsed:.1f}s", flush=True)
    out = result.stdout + result.stderr
    if "Optimal" in out or "Objective value" in out or "Result -" in out:
        print(f"  -> completed normally (found result text)", flush=True)
    else:
        print(f"  -> CRASHED (no result text found, output len={len(out)})", flush=True)
        print(f"  --- last 1500 chars of combined stdout+stderr ---", flush=True)
        print(out[-1500:], flush=True)
        print(f"  --- end ---", flush=True)

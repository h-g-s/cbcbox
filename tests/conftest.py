"""pytest configuration: collect CBC timing results and write a markdown report."""
import json
import os
import platform
import re
import subprocess
import sys

import pytest

import cbcbox

DATA_DIR = os.path.dirname(__file__)
SOLS_DIR = os.path.join(DATA_DIR, "sols")
# Nested under PERF_REPORT_DIR (already redirected to a host-visible output
# directory for Linux cibuildwheel jobs, which run tests inside an isolated
# container -- see wheel.yml's CIBW_ENVIRONMENT_LINUX) so these diagnostic
# logs are retrievable the same way the performance report is.
MIP_DEBUG_CUTS_REPORTS_DIR = os.path.join(
    os.environ.get("PERF_REPORT_DIR") or DATA_DIR, "mip_debug_cuts_reports"
)
MIP_DEBUG_CUTS_TIME_LIMIT = float(os.environ.get("CBCBOX_MIP_DEBUG_CUTS_TIME_LIMIT", "300"))


def _get_build_variants():
    """Return [(variant_name, binary_path), ...] for every available CBC build.

    Always includes 'generic'; adds 'avx2' when cbc_dist_avx2/ is present
    (x86_64 Linux/macOS/Windows wheels only).
    """
    pkg_dir = os.path.abspath(os.path.dirname(cbcbox.__file__))
    cbc_exe = "cbc.exe" if os.name == "nt" else "cbc"
    variants = []
    for name, subdir in [("generic", "cbc_dist"), ("avx2", "cbc_dist_avx2")]:
        binary = os.path.join(pkg_dir, subdir, "bin", cbc_exe)
        if os.path.isfile(binary):
            variants.append((name, binary))
    return variants


def pytest_configure(config):
    config._perf_results = []


def _find_mip_debug_cuts_binary():
    """Locate Cbc/test/mip-debug-cuts, built (see scripts/build_mip_debug_cuts.sh)
    into cbc_dist_debug(_avx2)/bin/ alongside the debug CBC binary during the
    CI "Compile ... debug" jobs. Returns None if no debug build/tool shipped
    with this installation (e.g. local `pip install -e .` without a debug
    variant, or CBCBOX_BUILD_VARIANT limited the build to non-debug variants).
    """
    pkg_dir = os.path.abspath(os.path.dirname(cbcbox.__file__))
    exe_name = "mip-debug-cuts.exe" if os.name == "nt" else "mip-debug-cuts"
    for subdir in ("cbc_dist_debug", "cbc_dist_debug_avx2"):
        candidate = os.path.join(pkg_dir, subdir, "bin", exe_name)
        if os.path.isfile(candidate):
            return candidate
    return None


def _run_mip_debug_cuts(instance_filename, node_id):
    """Activate Osi's row-cut debugger (via Cbc/test/mip-debug-cuts) against
    *instance_filename* using the matching tests/sols/<name>.sol reference
    solution, to help diagnose a wrong-objective test_solve failure: any cut,
    bound-fixing, or branching decision that would exclude the reference
    solution is flagged in the tool's output.

    Returns (log_path, captured_output) or None when either the reference
    solution or a debug-build mip-debug-cuts binary is unavailable (nothing
    to run -- e.g. local dev installs without a debug variant built).
    """
    name = instance_filename
    if name.endswith(".mps.gz"):
        name = name[: -len(".mps.gz")]
    sol_path = os.path.join(SOLS_DIR, f"{name}.sol")
    if not os.path.isfile(sol_path):
        return None

    binary = _find_mip_debug_cuts_binary()
    if binary is None:
        return None

    instance_path = os.path.join(DATA_DIR, instance_filename)
    cmd = [binary, instance_path, sol_path, str(MIP_DEBUG_CUTS_TIME_LIMIT), "0"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=MIP_DEBUG_CUTS_TIME_LIMIT + 60,
        )
        output = f"$ {' '.join(cmd)}\n(exit code {result.returncode})\n\n{result.stdout}{result.stderr}"
    except Exception as exc:  # pragma: no cover - defensive
        output = f"[mip-debug-cuts] failed to execute {cmd}: {exc}"

    os.makedirs(MIP_DEBUG_CUTS_REPORTS_DIR, exist_ok=True)
    safe_node_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", node_id)
    log_path = os.path.join(MIP_DEBUG_CUTS_REPORTS_DIR, f"{safe_node_id}.log")
    with open(log_path, "w") as f:
        f.write(output)
    return log_path, output


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """On a test_solve/test_solve_parallel objective-mismatch failure, if a
    reference solution (tests/sols/<name>.sol) and a debug mip-debug-cuts
    binary are both available, automatically run the row-cut-debugger
    diagnostic and attach its output to the failure report -- so CI logs
    immediately show which cut/bound-fixing/branch invalidated the known
    reference solution, without requiring a manual repro step.
    """
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return

    test_name = getattr(item, "originalname", None) or item.name
    if not test_name.startswith("test_solve"):
        return

    excinfo = call.excinfo
    if excinfo is None or not issubclass(excinfo.type, AssertionError):
        return
    message = str(excinfo.value)
    if "Expected" not in message or "got" not in message:
        return  # not the "wrong objective" assertion -- e.g. binary missing.

    callspec = getattr(item, "callspec", None)
    filename = callspec.params.get("filename") if callspec else None
    if not filename:
        return

    result = _run_mip_debug_cuts(filename, item.nodeid)
    if result is None:
        return
    log_path, output = result
    instance_name = filename[:-len(".mps.gz")] if filename.endswith(".mps.gz") else filename
    banner = (
        f"\n\n{'=' * 78}\n"
        f"[mip-debug-cuts] objective mismatch detected for {filename} -- "
        f"activated Cbc's row-cut debugger with the certified reference "
        f"solution (tests/sols/{instance_name}.sol) "
        f"to flag any cut/bound-fixing/branch that would exclude it.\n"
        f"Full output saved to: {log_path}\n"
        f"{'-' * 78}\n{output}\n{'=' * 78}\n"
    )
    report.longrepr = str(report.longrepr) + banner


@pytest.fixture(params=_get_build_variants(), ids=lambda v: v[0])
def cbc_variant(request):
    """Parameterised fixture: yields (variant_name, cbc_binary_path).

    Runs each test once per available build (generic, and avx2 when present).
    """
    return request.param


def pytest_sessionfinish(session, exitstatus):
    results = getattr(session.config, '_perf_results', [])
    if not results:
        return

    sys_name = platform.system()
    machine  = platform.machine()
    py_ver   = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    base_dir = os.environ.get("PERF_REPORT_DIR") or os.path.dirname(__file__)

    # --- JSON (machine-readable, consumed by the combine_reports CI job) ------
    payload = {
        "platform": sys_name,
        "machine":  machine,
        "python_version": py_ver,
        "results": results,
    }

    # --- Markdown (human-readable, per-platform quick view) -------------------
    variants      = list(dict.fromkeys(r.get("build_variant", "generic") for r in results))
    instances     = list(dict.fromkeys(r["instance"] for r in results))
    thread_counts = sorted({r["threads"] for r in results})

    lines = [
        "# CBC Performance Report",
        "",
        f"**Platform:** {sys_name} {machine}  ",
        f"**Python:** {py_ver}  ",
        "",
    ]

    if len(variants) > 1:
        # Side-by-side comparison table per thread count.
        lines += ["## Build variant comparison", ""]
        for threads in thread_counts:
            lines += [f"### {threads} thread{'s' if threads > 1 else ''}", ""]
            lookup = {
                (r["instance"], r.get("build_variant", "generic")): r.get("elapsed_s")
                for r in results if r["threads"] == threads
            }
            header = ["Instance"] + [f"{v} (s)" for v in variants] + ["avx2 speedup"]
            lines.append("| " + " | ".join(header) + " |")
            lines.append("|" + "|".join(["---"] * len(header)) + "|")
            for instance in instances:
                row = [f"`{instance}`"]
                times = {v: lookup.get((instance, v)) for v in variants}
                for v in variants:
                    t = times[v]
                    row.append(f"{t:.2f}" if t is not None else "n/a")
                gen_t  = times.get("generic")
                avx2_t = times.get("avx2")
                if gen_t and avx2_t and avx2_t > 0:
                    row.append(f"{gen_t / avx2_t:.2f}×")
                else:
                    row.append("n/a")
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")
    else:
        # Single variant — flat table.
        lines += [
            "| Instance | Build | Threads | Elapsed (s) | Objective |",
            "|---|---|---|---|---|",
        ]
        for r in results:
            elapsed = f"{r['elapsed_s']:.2f}" if r['elapsed_s'] is not None else "n/a"
            lines.append(
                f"| `{r['instance']}` | {r.get('build_variant', 'generic')} "
                f"| {r['threads']} | {elapsed} | {r['objective']:.1f} |"
            )
        lines.append("")

    try:
        with open(os.path.join(base_dir, "perf_report.json"), "w") as f:
            json.dump(payload, f, indent=2)
        with open(os.path.join(base_dir, "perf_report.md"), "w") as f:
            f.write("\n".join(lines))
    except OSError as exc:
        print(f"\n[cbcbox] WARNING: could not write perf report to {base_dir!r}: {exc}",
              file=sys.stderr)

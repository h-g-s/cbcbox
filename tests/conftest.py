"""pytest configuration: collect CBC timing results and write a markdown report."""
import json
import os
import platform
import sys

import pytest

import cbcbox


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
    with open(os.path.join(base_dir, "perf_report.json"), "w") as f:
        json.dump(payload, f, indent=2)

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

    with open(os.path.join(base_dir, "perf_report.md"), "w") as f:
        f.write("\n".join(lines))

"""pytest configuration: collect CBC timing results and write a markdown report."""
import json
import os
import platform
import sys

import pytest


def pytest_configure(config):
    config._perf_results = []


def pytest_sessionfinish(session, exitstatus):
    results = getattr(session.config, '_perf_results', [])
    if not results:
        return

    sys_name = platform.system()
    machine  = platform.machine()
    py_ver   = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    base_dir = os.path.dirname(__file__)

    # --- JSON (machine-readable, consumed by the combine_reports CI job) ------
    payload = {
        "platform": sys_name,
        "machine": machine,
        "python_version": py_ver,
        "results": results,
    }
    with open(os.path.join(base_dir, "perf_report.json"), "w") as f:
        json.dump(payload, f, indent=2)

    # --- Markdown (human-readable, per-platform quick view) -------------------
    lines = [
        "# CBC Performance Report",
        "",
        f"**Platform:** {sys_name} {machine}  ",
        f"**Python:** {py_ver}  ",
        "",
        "| Instance | Threads | Elapsed (s) | Objective |",
        "|---|---|---|---|",
    ]
    for r in results:
        elapsed = f"{r['elapsed_s']:.2f}" if r['elapsed_s'] is not None else "n/a"
        lines.append(
            f"| `{r['instance']}` | {r['threads']} | {elapsed} | {r['objective']:.1f} |"
        )
    lines.append("")

    with open(os.path.join(base_dir, "perf_report.md"), "w") as f:
        f.write("\n".join(lines))

"""pytest configuration: collect CBC timing results and write a markdown report."""
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

    out = os.path.join(os.path.dirname(__file__), "perf_report.md")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"\nPerformance report written to {out}")

"""Combine per-platform perf_report.json files into a single markdown table.

Usage:
    python combine_perf_reports.py <reports_dir> <output.md>

<reports_dir> is the directory created by actions/download-artifact with
merge-multiple: false — it contains one sub-directory per platform, each
holding a perf_report.json.
"""
import glob
import json
import os
import sys

reports_dir = sys.argv[1] if len(sys.argv) > 1 else "perf_reports"
output_md   = sys.argv[2] if len(sys.argv) > 2 else "perf_report_combined.md"

json_files = sorted(glob.glob(os.path.join(reports_dir, "**", "perf_report.json"),
                               recursive=True))
if not json_files:
    print(f"No perf_report.json files found under {reports_dir!r} — nothing to combine.")
    sys.exit(0)

all_data = []
for jf in json_files:
    with open(jf) as f:
        all_data.append(json.load(f))

# Collect ordered unique instances and thread counts.
seen_instances = set()
instances = []
for data in all_data:
    for r in data["results"]:
        if r["instance"] not in seen_instances:
            instances.append(r["instance"])
            seen_instances.add(r["instance"])

thread_counts = sorted({r["threads"] for data in all_data for r in data["results"]})

# Platform label: "Linux x86_64", "Darwin arm64", "Windows AMD64" etc.
def plat_label(data):
    return f"{data['platform']} {data['machine']}"

lines = [
    "# CBC Performance Report — All Platforms",
    "",
    f"Results from **{len(all_data)}** platform(s).",
    "",
]

for instance in instances:
    lines += [f"## `{instance}`", ""]

    # Header: Platform | 1 thread (s) | 3 threads (s) | Speedup
    thread_hdrs = [f"{t} thread{'s' if t > 1 else ''} (s)" for t in thread_counts]
    header = ["Platform"] + thread_hdrs
    if len(thread_counts) >= 2:
        header.append("Speedup")
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")

    for data in all_data:
        times = {r["threads"]: r["elapsed_s"]
                 for r in data["results"] if r["instance"] == instance}
        if not times:
            continue

        row = [plat_label(data)]
        for t in thread_counts:
            elapsed = times.get(t)
            row.append(f"{elapsed:.2f}" if elapsed is not None else "n/a")

        if len(thread_counts) >= 2:
            seq = times.get(thread_counts[0])
            par = times.get(thread_counts[-1])
            if seq and par and par > 0:
                row.append(f"{seq / par:.2f}×")
            else:
                row.append("n/a")

        lines.append("| " + " | ".join(row) + " |")

    lines.append("")

with open(output_md, "w") as f:
    f.write("\n".join(lines))

print(f"Combined report written to {output_md} ({len(all_data)} platforms, "
      f"{len(instances)} instances)")

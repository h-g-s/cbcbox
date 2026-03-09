"""Combine per-platform perf_report.json files into a single markdown report.

Usage:
    python combine_perf_reports.py <reports_dir> <output.md> [README.md]

<reports_dir> is the directory created by actions/download-artifact with
merge-multiple: false — it contains one sub-directory per platform, each
holding a perf_report.json.

If README.md is provided the content between
  <!-- PERF_RESULTS_START --> and <!-- PERF_RESULTS_END -->
is replaced with the generated summary + per-instance tables.
"""
import glob
import json
import math
import os
import sys

README_START   = "<!-- PERF_RESULTS_START -->"
README_END     = "<!-- PERF_RESULTS_END -->"
SPEEDUP_START  = "<!-- PERF_SPEEDUP_START -->"
SPEEDUP_END    = "<!-- PERF_SPEEDUP_END -->"

reports_dir = sys.argv[1] if len(sys.argv) > 1 else "perf_reports"
output_md   = sys.argv[2] if len(sys.argv) > 2 else "perf_report_combined.md"
readme_path = sys.argv[3] if len(sys.argv) > 3 else None

json_files = sorted(glob.glob(os.path.join(reports_dir, "**", "perf_report.json"),
                               recursive=True))
if not json_files:
    print(f"No perf_report.json files found under {reports_dir!r} — nothing to combine.")
    sys.exit(0)

all_data = []
for jf in json_files:
    with open(jf) as f:
        all_data.append(json.load(f))

# ── helpers ───────────────────────────────────────────────────────────────────

def geomean(values):
    valid = [v for v in values if v is not None and v > 0]
    if not valid:
        return None
    return math.exp(sum(math.log(v) for v in valid) / len(valid))

def fmt(v):
    return f"{v:.2f}" if v is not None else "—"

def plat_label(data):
    return f"{data['platform']} {data['machine']}"

# ── collect ordered unique keys ───────────────────────────────────────────────

seen_plats = set()
platforms = []
for data in all_data:
    p = plat_label(data)
    if p not in seen_plats:
        platforms.append(p)
        seen_plats.add(p)

seen_inst = set()
instances = []
for data in all_data:
    for r in data["results"]:
        if r["instance"] not in seen_inst:
            instances.append(r["instance"])
            seen_inst.add(r["instance"])

thread_counts = sorted({r["threads"] for data in all_data for r in data["results"]})
all_variants  = sorted({r.get("build_variant", "generic")
                         for data in all_data for r in data["results"]})

# lookup: (platform_label, variant, instance, threads) -> elapsed_s
lookup = {}
for data in all_data:
    p = plat_label(data)
    for r in data["results"]:
        key = (p, r.get("build_variant", "generic"), r["instance"], r["threads"])
        lookup[key] = r.get("elapsed_s")

# ── summary section ───────────────────────────────────────────────────────────

def summary_section():
    """One table per thread count: rows = platforms, cols = variants (geomean)."""
    lines = ["## Summary", "",
             "Geometric mean solve time (seconds) across all test instances.", ""]
    has_avx2 = "avx2" in all_variants
    for threads in thread_counts:
        t_label = f"{threads} thread" + ("s" if threads > 1 else "")
        lines += [f"### {t_label}", ""]
        header = ["Platform", "generic (s)"]
        if has_avx2:
            header += ["avx2 (s)", "avx2 speedup"]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")
        for plat in platforms:
            gen_times = [lookup.get((plat, "generic", inst, threads)) for inst in instances]
            gen_gm    = geomean(gen_times)
            row = [plat, fmt(gen_gm)]
            if has_avx2:
                avx2_times = [lookup.get((plat, "avx2", inst, threads)) for inst in instances]
                avx2_gm    = geomean(avx2_times)
                speedup    = f"{gen_gm / avx2_gm:.2f}×" if (gen_gm and avx2_gm) else "—"
                row += [fmt(avx2_gm), speedup]
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    return lines

# ── per-instance section ──────────────────────────────────────────────────────

def instances_section():
    """One table per instance: rows = (platform, variant), cols = thread counts."""
    lines = ["## Per-instance results", ""]
    thread_hdrs = [f"{t} thread{'s' if t > 1 else ''} (s)" for t in thread_counts]
    for instance in instances:
        label = instance.replace(".mps.gz", "")
        lines += [f"### `{label}`", ""]
        header = ["Platform", "Build"] + thread_hdrs
        if len(thread_counts) >= 2:
            header.append("parallel speedup")
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")
        for plat in platforms:
            for variant in all_variants:
                times = {t: lookup.get((plat, variant, instance, t)) for t in thread_counts}
                if all(v is None for v in times.values()):
                    continue
                row = [plat, variant]
                for t in thread_counts:
                    row.append(fmt(times.get(t)))
                if len(thread_counts) >= 2:
                    seq = times.get(thread_counts[0])
                    par = times.get(thread_counts[-1])
                    row.append(f"{seq / par:.2f}×" if (seq and par and par > 0) else "—")
                lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    return lines

# ── average AVX2 speedup (x86_64, single thread) ─────────────────────────────

def _avx2_speedup_sentence():
    """Return a one-line markdown summary of the geometric-mean AVX2 speedup.

    Considers only x86_64 platforms (Linux x86_64 and Windows AMD64 and
    macOS x86_64) at 1 thread.  Returns None when insufficient data.
    """
    if "avx2" not in all_variants:
        return None

    x86_platforms = [p for p in platforms
                     if "x86_64" in p or "AMD64" in p]
    if not x86_platforms:
        return None

    ratios = []
    for plat in x86_platforms:
        for inst in instances:
            g = lookup.get((plat, "generic", inst, 1))
            a = lookup.get((plat, "avx2",    inst, 1))
            if g and a and a > 0:
                ratios.append(g / a)

    if not ratios:
        return None

    gm = math.exp(sum(math.log(r) for r in ratios) / len(ratios))
    n_inst  = len({inst for plat in x86_platforms for inst in instances
                   if lookup.get((plat, "avx2", inst, 1))})
    n_plat  = len(x86_platforms)
    plat_str = ", ".join(x86_platforms)
    return (
        f"The AVX2/Haswell build is **~{gm:.1f}×** faster than the generic build "
        f"on average (geometric mean across {n_inst} instances, {n_plat} x86_64 "
        f"platform{'s' if n_plat != 1 else ''}: {plat_str})."
    )

# ── assemble ──────────────────────────────────────────────────────────────────

body_lines = summary_section() + instances_section()

full_lines = [
    "# CBC Performance Report — All Platforms",
    "",
    f"Results from **{len(all_data)}** platform(s), **{len(instances)}** instance(s).",
    "",
] + body_lines

with open(output_md, "w") as f:
    f.write("\n".join(full_lines))

print(f"Combined report written to {output_md} "
      f"({len(all_data)} platforms, {len(instances)} instances)")

# ── update README ─────────────────────────────────────────────────────────────

if readme_path and os.path.exists(readme_path):
    with open(readme_path) as f:
        readme = f.read()

    # ── per-instance / summary tables ─────────────────────────────────────────
    if README_START not in readme or README_END not in readme:
        print(f"Markers not found in {readme_path} — skipping README update.")
    else:
        section = "\n".join(body_lines)
        before  = readme[:readme.index(README_START) + len(README_START)]
        after   = readme[readme.index(README_END):]
        readme  = before + "\n\n" + section + "\n\n" + after
        print(f"README performance tables updated: {readme_path}")

    # ── average AVX2 speedup blurb ────────────────────────────────────────────
    speedup_sentence = _avx2_speedup_sentence()
    if speedup_sentence and SPEEDUP_START in readme and SPEEDUP_END in readme:
        before = readme[:readme.index(SPEEDUP_START) + len(SPEEDUP_START)]
        after  = readme[readme.index(SPEEDUP_END):]
        readme = before + "\n\n" + speedup_sentence + "\n\n" + after
        print(f"README speedup blurb updated: {speedup_sentence}")

    with open(readme_path, "w") as f:
        f.write(readme)

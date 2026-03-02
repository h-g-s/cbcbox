"""Generate performance comparison plots (generic vs AVX2/Haswell) for x86_64 platforms.

Usage:
    python generate_perf_plots.py <reports_dir> <output.png> [README.md]

Reads all perf_report.json files under <reports_dir> and writes:
  - <output.png>               — Linux x86_64 only (main plot embedded in README)
  - docs/perf_avx2_other.png   — Windows AMD64 + macOS x86_64 (linked from README)

If README.md is given, the content between
  <!-- PERF_PLOT_START --> and <!-- PERF_PLOT_END -->
is replaced with a Markdown image reference pointing at the generated PNG.
"""

import glob
import json
import os
import sys

PLOT_START = "<!-- PERF_PLOT_START -->"
PLOT_END   = "<!-- PERF_PLOT_END -->"

# Main plot: Linux x86_64 only
MAIN_PLATFORMS = {
    ("Linux", "x86_64"): "Linux x86_64",
}

# Secondary plot: Windows + macOS Intel
OTHER_PLATFORMS = {
    ("Windows", "AMD64"):   "Windows AMD64",
    ("Darwin",  "x86_64"):  "macOS x86_64",
}

GITHUB_RAW = "https://raw.githubusercontent.com/h-g-s/cbcbox/master"

reports_dir = sys.argv[1] if len(sys.argv) > 1 else "perf_reports"
output_png  = sys.argv[2] if len(sys.argv) > 2 else "docs/perf_avx2_speedup.png"
readme_path = sys.argv[3] if len(sys.argv) > 3 else None

# Derive secondary output path from primary
other_png = os.path.join(os.path.dirname(output_png), "perf_avx2_other.png")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import numpy as np
except ImportError:
    print("matplotlib/numpy not available — skipping plot generation")
    sys.exit(0)

# ── load data ─────────────────────────────────────────────────────────────────

json_files = sorted(glob.glob(os.path.join(reports_dir, "**", "perf_report.json"),
                               recursive=True))
if not json_files:
    print(f"No perf_report.json files found under {reports_dir!r} — skipping plot")
    sys.exit(0)

all_data = []
for jf in json_files:
    with open(jf) as f:
        all_data.append(json.load(f))

# ── helper: build lookup for a set of platform keys ───────────────────────────

def build_lookup(platform_map):
    lookup = {}
    for data in all_data:
        pk = (data["platform"], data["machine"])
        if pk not in platform_map:
            continue
        label = platform_map[pk]
        for r in data["results"]:
            key = (label, r.get("build_variant", "generic"), r["instance"], r["threads"])
            elapsed = r.get("elapsed_s")
            if elapsed is not None:
                lookup[key] = elapsed
    return lookup

# ── collect ordered instances ─────────────────────────────────────────────────

seen_inst = set()
instances = []
for data in all_data:
    for r in data["results"]:
        if r["instance"] not in seen_inst:
            instances.append(r["instance"])
            seen_inst.add(r["instance"])

THREADS = 1  # single-threaded comparison

# ── styling ───────────────────────────────────────────────────────────────────

INST_LABELS   = [i.replace(".mps.gz", "") for i in instances]
COLOR_GENERIC = "#6c8ebf"
COLOR_AVX2    = "#e8a020"
STYLE_BG      = "#f8f9fa"
GRID_COLOR    = "#d0d4da"

def draw_plot(platform_map, title, output_file):
    lookup = build_lookup(platform_map)
    if not lookup:
        print(f"No data for {title} — skipping")
        return False

    present = {platform_map[pk] for data in all_data
               for pk in [((data["platform"], data["machine"]))]
               if pk in platform_map}
    platforms = [v for v in platform_map.values() if v in present]
    platforms = [p for p in platforms
                 if any(lookup.get((p, "avx2", inst, THREADS)) for inst in instances)]

    if not platforms:
        print(f"No AVX2 data for {title} — skipping")
        return False

    n_plat = len(platforms)
    n_inst = len(instances)
    fig, axes = plt.subplots(n_plat, 1,
                             figsize=(max(10, n_inst * 1.6), 4.5 * n_plat),
                             constrained_layout=True)
    if n_plat == 1:
        axes = [axes]

    fig.patch.set_facecolor(STYLE_BG)
    fig.suptitle(f"CBC solver: generic vs AVX2/Haswell build  ·  single thread  ({title})",
                 fontsize=13, fontweight="bold", color="#1a1a2e")

    x     = np.arange(n_inst)
    width = 0.34

    for ax, plat in zip(axes, platforms):
        ax.set_facecolor(STYLE_BG)

        gen_times  = [lookup.get((plat, "generic", inst, THREADS)) or 0 for inst in instances]
        avx2_times = [lookup.get((plat, "avx2",    inst, THREADS)) or 0 for inst in instances]

        ax.bar(x - width / 2, gen_times,  width,
               label="generic",         color=COLOR_GENERIC,
               edgecolor="white", linewidth=0.6, zorder=3)
        ax.bar(x + width / 2, avx2_times, width,
               label="AVX2 / Haswell", color=COLOR_AVX2,
               edgecolor="white", linewidth=0.6, zorder=3)

        for i, (g, a) in enumerate(zip(gen_times, avx2_times)):
            if g and a and g > 0 and a > 0:
                speedup = g / a
                top = max(g, a)
                ax.text(x[i], top * 1.12, f"{speedup:.2f}×",
                        ha="center", va="bottom", fontsize=8.5, fontweight="bold",
                        color="#d04000" if speedup > 1.05 else "#444")

        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}s"))
        ax.yaxis.grid(True, which="both", color=GRID_COLOR, linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(GRID_COLOR)
        ax.set_xticks(x)
        ax.set_xticklabels(INST_LABELS, rotation=18, ha="right", fontsize=9)
        ax.set_ylabel("Solve time (log scale)", fontsize=9)
        ax.set_title(plat, fontsize=11, fontweight="semibold", pad=6)
        ax.legend(framealpha=0.85, fontsize=9, loc="upper left")

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    fig.savefig(output_file, dpi=150, bbox_inches="tight", facecolor=STYLE_BG)
    print(f"Plot saved → {output_file}")
    plt.close(fig)
    return True

# ── generate plots ────────────────────────────────────────────────────────────

main_ok  = draw_plot(MAIN_PLATFORMS,  "Linux x86_64",                output_png)
other_ok = draw_plot(OTHER_PLATFORMS, "Windows AMD64 + macOS x86_64", other_png)

# ── update README ─────────────────────────────────────────────────────────────

if readme_path and os.path.exists(readme_path) and main_ok:
    with open(readme_path) as f:
        readme = f.read()
    if PLOT_START not in readme or PLOT_END not in readme:
        print(f"Plot markers not found in {readme_path} — skipping README update")
    else:
        # Use absolute URLs so images render on PyPI
        repo_root = os.path.dirname(os.path.abspath(readme_path))
        img_rel   = os.path.relpath(output_png, repo_root)
        other_rel = os.path.relpath(other_png,  repo_root)
        img_url   = GITHUB_RAW + "/" + img_rel.replace(os.sep, "/")
        other_url = GITHUB_RAW + "/" + other_rel.replace(os.sep, "/")
        other_link = (f"[Windows AMD64 + macOS x86_64 summary]({other_url})"
                      if other_ok else "")
        img_md = (
            f"![CBC solve time — generic vs AVX2/Haswell (Linux x86_64)]({img_url})\n\n"
            f"*Single-threaded solve time across benchmark instances on Linux x86_64. "
            f"Speedup factor shown above each pair. Lower is better.*"
        )
        if other_link:
            img_md += f"\n\nSee also: {other_link}"
        before = readme[:readme.index(PLOT_START) + len(PLOT_START)]
        after  = readme[readme.index(PLOT_END):]
        with open(readme_path, "w") as f:
            f.write(before + "\n\n" + img_md + "\n\n" + after)
        print(f"README updated with plot reference")


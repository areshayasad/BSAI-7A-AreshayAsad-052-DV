"""
Part C — palette proof (completed).

    python3 starter/palette_check.py

Runs as given: it simulates three kinds of colour-vision deficiency on two
palettes and saves a before/after swatch sheet. Your job is to swap in your
own palette, read the result honestly, and answer the four questions in the
brief.

Roughly 1 man in 12 and 1 woman in 200 has some form of colour-vision
deficiency. In a cohort of 60 students that is about three people who cannot
read a red/green chart. They will not tell you. The simulation will.
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vizlib import (PALETTE, save_fig, simulate_cvd, style_defaults,   # noqa: E402
                    verdict, worst_pair)

ROOT = os.path.dirname(os.path.abspath(__file__))
style_defaults()

# ----------------------------------------------------------------- TODO 1
# Replace this with a palette you actually like the look of — matplotlib's
# tab10 first four, Excel's defaults, something from a dashboard you admire.
# Do not pick one you already know is safe; the point is to find out.
MY_PALETTE = ["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728"]   # matplotlib tab10
MY_LABEL = "matplotlib tab10, first four"

COURSE_PALETTE = PALETTE["series"] + [PALETTE["series_4th"]]
KINDS = ["normal", "deutan", "protan", "tritan"]


def swatch_sheet(palettes, path):
    fig, axes = plt.subplots(len(palettes), len(KINDS),
                             figsize=(3.0 * len(KINDS), 2.1 * len(palettes)))
    if len(palettes) == 1:
        axes = axes.reshape(1, -1)
    for row, (pal, label) in enumerate(palettes):
        for col, kind in enumerate(KINDS):
            ax = axes[row, col]
            shown = pal if kind == "normal" else simulate_cvd(pal, kind)
            for i, hexc in enumerate(shown):
                ax.add_patch(plt.Rectangle((i, 0), 0.92, 1, color=hexc))
                ax.text(i + 0.46, -0.22, f"S{i+1}", ha="center", fontsize=8,
                        color=PALETTE["ink_soft"])
            ax.set_xlim(-0.1, len(pal))
            ax.set_ylim(-0.4, 1.1)
            ax.axis("off")
            ax.set_title(kind, fontsize=10)
        axes[row, 0].text(-0.05, 1.42, label, transform=axes[row, 0].transAxes,
                          fontsize=11, fontweight="bold", color=PALETTE["ink"])
    fig.suptitle("Prove it, do not claim it", x=0.006, ha="left",
                 fontsize=13, fontweight="bold", color=PALETTE["ink"])
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    out = save_fig(fig, path,
                   "Machado, Oliveira & Fernandes (2009) severity-1.0 "
                   "matrices, applied in linear RGB.")
    plt.close(fig)
    return out


def audit(pal, label):
    """
    The numbers, not the impression.

    `vizlib.worst_pair` measures every pair in OKLab, which is near-uniform,
    so a single threshold means the same thing for every hue. The thresholds
    are documented on `vizlib.delta_e`.
    """
    print(label)
    rows = []
    for kind in ["normal", "deutan", "protan", "tritan"]:
        i, j, a, b, d = worst_pair(pal, kind)
        rows.append((kind, i, j, a, b, d))
        print(f"  {kind:7s} closest pair  S{i} {a} vs S{j} {b}"
              f"   ΔE {d:5.1f}   {verdict(d)}")
    print()
    return rows


def main():
    out = swatch_sheet([(MY_PALETTE, MY_LABEL),
                        (COURSE_PALETTE, "The course palette")],
                       os.path.join(ROOT, "partC_palette.png"))
    print("wrote", out, "\n")

    audit(MY_PALETTE, MY_LABEL)
    audit(COURSE_PALETTE, "The course palette (3 slots + the 4th)")

    # ---- Q3: the worst pair in each palette, every pair compared, every vision type
    print("Q3 - worst pair per palette across all four vision types")
    for pal, label in [(MY_PALETTE, MY_LABEL), (COURSE_PALETTE, "course palette + 4th slot"),
                       (PALETTE["series"], "course palette, 3 slots only")]:
        worst = min((worst_pair(pal, k) + (k,) for k in KINDS), key=lambda r: r[4])
        i, j, a, b, d, kind = worst
        print(f"  {label:30s} S{i} {a} vs S{j} {b} under {kind}: dE {d:.1f} ({verdict(d)})")
    print()
    print("Q3 reading: tab10 collapses badly. Under protanopia the orange and green are 0.7 apart (the same")
    print("colour) and under deuteranopia green and red are 4.1 apart. That is the red/green failure.")
    print("The course palette has a weak pair too: the 4th slot (#CC79A7, pink) against the green (#009E73)")
    print("under deuteranopia, dE 7.5, inside the 6-8 band that is legal ONLY with a second encoding. So")
    print("the pink may appear only with direct labels, a different marker or a table view, and it falls")
    print("below 3:1 contrast on white, so never as a thin line on its own. The 3-slot set never drops")
    print("below dE 8.4 (tritan), which clears the 8 target.")
    print()
    print("Q4 - my rule for more than three categories:")
    print("  Three colours is the ceiling for colour alone. Past three I keep the three-slot palette and")
    print("  add a second channel instead of another hue: marker shape (vizlib.MARKERS), direct labels")
    print("  at the line ends, or small multiples / a sorted table. If two categories can only be told")
    print("  apart by colour, the chart is not finished.")


if __name__ == "__main__":
    main()

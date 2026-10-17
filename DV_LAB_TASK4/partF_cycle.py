#!/usr/bin/env python3
"""
Part F (bonus) - Week 1's flights question, settled on data I found myself.

    python3 partF_cycle.py            -> partF_cycle.png (300 dpi) + printed audit/answer
    python3 partF_cycle.py --download -> refresh partF_data/ from the source URL first

The Week 1 question: the seasonal swing looks bigger every year - is the
SEASONALITY growing, or is the SERIES growing?

Data: REAL, not synthetic. U.S. Bureau of Labor Statistics unemployed persons by
industry, monthly, Jan 2000 - Feb 2010 (14 industries; the category column is
`series`), via vega-datasets. Downloaded 2026-10-18. See partF_data/SOURCE.md.
Series studied: Construction (strong winter seasonality, and the 2008-09
recession triples its level - the cleanest test of the question).
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.tsa.seasonal import seasonal_decompose

from tslib import PALETTE, audit_index, banked_figsize, cycle_plot, save_fig, style_defaults

URL = ("https://raw.githubusercontent.com/vega/vega-datasets/main/data/"
       "unemployment-across-industries.json")
LOCAL = HERE / "partF_data" / "unemployment-across-industries.json"
SERIES = "Construction"


def load() -> pd.DataFrame:
    if "--download" in sys.argv:
        urllib.request.urlretrieve(URL, LOCAL)
    d = pd.read_json(LOCAL)
    d["month"] = pd.to_datetime(dict(year=d.year, month=d.month, day=1))
    return d


def main() -> None:
    style_defaults()
    d = load()
    print("=" * 78)
    print("PART F - is the seasonality growing, or the series? (REAL data, BLS via vega-datasets)")
    print("=" * 78)
    print(f"source: {URL}\ndownloaded 2026-10-18; categories (industries): {d.series.nunique()}; "
          f"rows {len(d):,}; each industry {d.groupby('series').size().iloc[0]} months")

    # ------------------------------------------------------------- 2: audit
    s = d[d.series == SERIES].set_index("month")["count"].sort_index()
    a = audit_index(s, "MS")
    print(f"\nAUDIT (tslib.audit_index, freq MS) on {SERIES}:")
    print(f"  dtype_ok={a['dtype_ok']}  monotonic={a['monotonic']}  duplicated={a['n_duplicated']}  "
          f"missing months={a['n_missing']}  span={a['span'][0][:10]} .. {a['span'][1][:10]}")
    print(f"  partial_tail={a['partial_tail']} (last year {a['tail_period']} has only {a['tail_count']} "
          f"month(s) of 12)")
    print(f"  -> {len(s)} months = 10 complete years (2000-2009) + Jan-Feb 2010. The partial 2010 is kept "
          f"in the series plots, but excluded from every per-year statistic below.")
    assert a["n_duplicated"] == 0 and a["n_missing"] == 0

    # ------------------------------------------------- decompositions
    add = seasonal_decompose(s, model="additive", period=12)
    mul = seasonal_decompose(s, model="multiplicative", period=12)
    add_amp = float(add.seasonal.iloc[:12].max() - add.seasonal.iloc[:12].min())
    mul_lo, mul_hi = float(mul.seasonal.iloc[:12].min()), float(mul.seasonal.iloc[:12].max())
    tr = add.trend.dropna()
    ra = add.resid.dropna()
    rm = mul.resid.dropna()
    idx = ra.index.intersection(rm.index)
    rho_add = spearmanr(tr.loc[idx], ra.loc[idx].abs())[0]
    rho_mul = spearmanr(tr.loc[idx], (rm.loc[idx] - 1).abs())[0]
    # the same question asked year by year (complete years only)
    yr = s[:"2009-12"].groupby(s[:"2009-12"].index.year).agg(["mean", "min", "max"])
    yr["swing"] = yr["max"] - yr["min"]
    yr["swing_pct_of_mean"] = yr.swing / yr["mean"] * 100
    r_abs = np.corrcoef(yr["mean"], yr.swing)[0, 1]
    r_rel = np.corrcoef(yr["mean"], yr.swing_pct_of_mean)[0, 1]
    first, last = yr.iloc[0], yr.iloc[-1]
    lvl_x = last["mean"] / first["mean"]
    swing_x = last.swing / first.swing
    print(f"\nPER-YEAR (2000-2009): mean level x{lvl_x:.2f}, absolute swing (max-min) x{swing_x:.2f}")
    print(yr.round(1).to_string())
    print(f"  corr(level, absolute swing)      = {r_abs:+.2f}")
    print(f"  corr(level, swing as % of level) = {r_rel:+.2f}")
    print(f"\nDECOMPOSITIONS (period 12):")
    print(f"  additive        seasonal peak-to-trough = {add_amp:,.0f} thousand persons")
    print(f"  multiplicative  seasonal factor range   = {mul_lo:.2f} .. {mul_hi:.2f}")
    print(f"  size of residual vs level (Spearman rho of |resid| with trend):")
    print(f"      additive residual        rho = {rho_add:+.2f}")
    print(f"      multiplicative residual  rho = {rho_mul:+.2f}")
    mult_better = abs(rho_mul) < abs(rho_add)
    print(f"  -> the {'multiplicative' if mult_better else 'additive'} model leaves residuals "
          f"that depend less on the level.")

    # ----------------------------------------------------------- the figure
    fig_w, bank_h = banked_figsize(s.to_numpy(float), width=9.0)
    ratio = fig_w / bank_h
    print(f"\nASPECT RATIO of panel 1 (banked to 45 degrees, tslib.banked_figsize): "
          f"{fig_w:.1f} wide x {bank_h:.2f} high = {ratio:.1f} : 1")
    fig = plt.figure(figsize=(16, 6.2))
    gs = fig.add_gridspec(1, 4, width_ratios=[2.2, 1.35, 0.9, 0.9], wspace=0.34,
                          left=0.05, right=0.99, top=0.76, bottom=0.17)
    a1 = fig.add_subplot(gs[0])
    a1.plot(s.index, s.values, color=PALETTE["series"][0], linewidth=1.6)
    a1.set_box_aspect(bank_h / fig_w)
    a1.set_ylim(0, None)
    a1.set_ylabel("Unemployed (thousand persons)")
    a1.set_xlabel("Month")
    a1.set_title(f"Series drawn at the banked aspect ratio\n({ratio:.1f}:1 width:height, 45° median slope)",
                 loc="left", fontsize=10)

    a2 = fig.add_subplot(gs[1])
    cycle_plot(a2, s[:"2009-12"], by="month")
    a2.set_ylim(0, None)
    a2.set_ylabel("Unemployed (thousand persons)")
    a2.set_title("Cycle plot: one line per year\n(2000 faint → 2009 dark)", loc="left", fontsize=10)
    a2.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    for yy in (2000, 2009):
        yv = s[str(yy)]
        a2.text(12.2, yv.iloc[-1], str(yy), fontsize=8, va="center", color=PALETTE["ink_soft"])

    a3 = fig.add_subplot(gs[2])
    a4 = fig.add_subplot(gs[3], sharex=a3)
    a3.plot(ra.index, ra.values, color=PALETTE["series"][1], linewidth=1.0)
    a3.axhline(0, color=PALETTE["ink_soft"], linewidth=0.8)
    a3.set_title("Additive\nresidual", loc="left", fontsize=10)
    a3.set_ylabel("Residual (thousand persons)")
    a4.plot(rm.index, rm.values, color=PALETTE["series"][2], linewidth=1.0)
    a4.axhline(1, color=PALETTE["ink_soft"], linewidth=0.8)
    a4.set_title("Multiplicative\nresidual", loc="left", fontsize=10)
    a4.set_ylabel("Residual (ratio to 1)")
    for ax in (a3, a4):
        ax.tick_params(axis="x", labelrotation=45, labelsize=8)
        ax.set_xlabel("Month")

    if r_rel < -0.5:
        kind = "additive-like"
        head = (f"{SERIES}: the series grew ×{lvl_x:.1f} but its seasonal swing only ×{swing_x:.1f} — "
                f"the swing is NOT growing with the series")
    elif r_rel > 0.5:
        kind = "multiplicative-like"
        head = f"{SERIES}: the seasonal swing grows in step with the series (×{swing_x:.1f} vs ×{lvl_x:.1f})"
    else:
        kind = "ambiguous"
        head = f"{SERIES}: level ×{lvl_x:.1f}, swing ×{swing_x:.1f} — the evidence does not separate the models"
    fig.suptitle(head, x=0.05, y=0.97, ha="left", fontsize=13, fontweight="bold")
    save_fig(fig, HERE / "partF_cycle.png",
             note=("Source: U.S. Bureau of Labor Statistics, unemployed persons by industry (Construction), monthly "
                   "Jan 2000 - Feb 2010, via vega-datasets; downloaded 2026-10-18. REAL data (not course data). "
                   "Cycle plot uses complete years 2000-2009; the partial 2010 (2 months) is shown in panel 1 only. "
                   f"Panel 1 aspect banked to 45°: {ratio:.1f}:1."))
    plt.close(fig)

    # --------------------------------------------------------------- answer
    print("\nANSWER (two sentences):")
    print(f"  Between 2000 and 2009 the series' level rose x{lvl_x:.1f} but its absolute seasonal swing moved "
          f"only x{swing_x:.1f}, so the swing fell from {first.swing_pct_of_mean:.0f}% to "
          f"{last.swing_pct_of_mean:.0f}% of the level (corr of level with swing-as-%-of-level {r_rel:+.2f}).")
    if kind == "additive-like":
        print("  So the seasonality is NOT growing in proportion to the series, and 'the series is just growing' "
              "does not explain the swing either: in this recession the extra unemployed were added "
              "year-round (additive), not as a bigger winter surge.")
    elif kind == "multiplicative-like":
        print("  So the swing is growing because the series is: the seasonality is a constant proportion of the level.")
    else:
        print("  So neither story is supported strongly enough to call.")
    print(f"  Caveat: the residual test is weak for BOTH models (|rho| {abs(rho_add):.2f} additive, "
          f"{abs(rho_mul):.2f} multiplicative, both under 0.15) and slightly favours the multiplicative model, so it")
    print("  does not overturn the per-year result; the multiplicative decomposition also forces a constant")
    print("  proportion that the per-year numbers contradict. One series in one recession; it need not agree")
    print("  with the Week 1 flights case, and the disagreement is reported as found.")

if __name__ == "__main__":
    main()

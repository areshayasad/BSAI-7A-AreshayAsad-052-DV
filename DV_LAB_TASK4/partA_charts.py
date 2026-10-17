#!/usr/bin/env python3
"""
Part A - rebuild nine charts, then plot the nine honest redesigns.

Run:  python3 partA_charts.py
Out:  figs/caseNN_rebuild.png   the analyst's chart, built from the recipe
      figs/caseNN_redesign.png  the honest chart
      partA_numbers.json        every number the diagnosis quotes
      partA_output.txt          the self-checks, printed

The rebuilds are DELIBERATELY the analysts' charts - they are the thing being
diagnosed. All data is SYNTHETIC course data (CDB601220 Week 4).
"""
from __future__ import annotations

import io
import json
import sys
import textwrap
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

from tslib import PALETTE, exclusivity_check, lag_at_turn, style_defaults

DATA = HERE / "data"
FIGS = HERE / "figs"
FIGS.mkdir(exist_ok=True)
BLUE, ORANGE, GREEN, PINK = PALETTE["series"] + [PALETTE["series_4th"]]
GREY, INK, SOFT = PALETTE["muted"], PALETTE["ink"], PALETTE["ink_soft"]
N: dict = {}                       # every number quoted in the diagnosis


def ttl(ax, text, width=62, size=10.5):
    ax.set_title("\n".join(textwrap.wrap(text, width)), loc="left", fontsize=size)


def save(fig, name):
    fig.savefig(FIGS / name, dpi=300, bbox_inches="tight", facecolor=PALETTE["surface"])
    plt.close(fig)


def src(fig, extra=""):
    fig.text(0.01, -0.07, "SYNTHETIC course data, CDB601220 Week 4. " + extra,
             fontsize=6.5, color=SOFT, ha="left", va="top")


def check(label, ok, got):
    print(f"   self-check {label:<54} {'PASS' if ok else 'FAIL'}   ({got})")
    assert ok, label


# ============================================================ 1  string dates
def case01():
    print("\nCASE 1  orders / string months")
    d = pd.read_csv(DATA / "case01_orders_stringdate.csv")
    s = d.sort_values("month").reset_index(drop=True)            # the recipe
    diff = s.orders.diff().dropna()
    drops = sorted(-diff[diff < 0].astype(int))
    check("24 points", len(s) == 24, len(s))
    check("drops of 958 and 978", drops == [958, 978], drops)
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(range(24), s.orders, marker="o", color=BLUE)
    ax.set_xticks(range(24), s.month, rotation=90, fontsize=7)
    ax.set_ylim(0, 7000)
    for k in diff[diff < 0].index:
        ax.annotate(f"−{-diff[k]:,.0f}", (k, s.orders[k]), xytext=(k + 0.6, s.orders[k] - 1300),
                    fontsize=8, color=ORANGE, arrowprops=dict(arrowstyle="->", color=ORANGE))
    ax.set_ylabel("Orders per month (count)")
    ax.set_xlabel("Month, sorted as TEXT (the recipe)")
    ttl(ax, "Claim: “Orders peak in Q1 and collapse every year — a clear annual cycle”")
    src(fig)
    save(fig, "case01_rebuild.png")

    # honest
    d["month_dt"] = pd.to_datetime(d.month, format="%Y-%m")
    c = d.sort_values("month_dt").set_index("month_dt").orders
    ch = c.diff().dropna()
    pos_after_sort = pd.Series(range(len(d)), index=d.sort_values("month").index)
    n_moved = int((d.sort_values("month").index != d.sort_values("month_dt").index).sum())
    N["c1"] = dict(first=int(c.iloc[0]), last=int(c.iloc[-1]),
                   total_pct=float((c.iloc[-1] / c.iloc[0] - 1) * 100),
                   n_neg=int((ch < 0).sum()), n_changes=int(len(ch)),
                   min_change=int(ch.min()), max_change=int(ch.max()),
                   monthly_pct=float(((c.iloc[-1] / c.iloc[0]) ** (1 / 23) - 1) * 100),
                   drops=drops, n_moved=n_moved,
                   dec24=int(c["2024-12-01"]), feb24=int(c["2024-02-01"]),
                   feb25=int(c["2025-02-01"]), dec25=int(c["2025-12-01"]),
                   oct24=int(c["2024-10-01"]), may25=int(c["2025-05-01"]))
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(c.index, c.values, marker="o", color=BLUE)
    ax.set_ylim(0, 7000)
    ax.set_ylabel("Orders per month (count)")
    ax.set_xlabel("Month (parsed as a date, plotted in calendar order)")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ttl(ax, f"Orders rose every single month — {c.iloc[0]:,} to {c.iloc[-1]:,} "
            f"(+{N['c1']['total_pct']:.0f}%); no peak, no collapse")
    ax.annotate(f"{N['c1']['n_neg']} falls in {N['c1']['n_changes']} month-on-month changes\n"
                f"(smallest rise +{N['c1']['min_change']})", xy=(c.index[14], c.iloc[14]),
                xytext=(c.index[3], 6300), fontsize=8.5, color=INK,
                arrowprops=dict(arrowstyle="->", color=SOFT))
    src(fig, "Axis starts at zero; months parsed with pd.to_datetime(format='%Y-%m').")
    save(fig, "case01_redesign.png")


# ============================================================ 2  shop closed
def case02():
    print("\nCASE 2  sales / shop closed")
    d = pd.read_csv(DATA / "case02_shop_closed.csv", parse_dates=["date"])
    check("69 points, first 207, last 253, +22%",
          len(d) == 69 and d.sales_pkr_k.iloc[0] == 207 and d.sales_pkr_k.iloc[-1] == 253
          and round((253 / 207 - 1) * 100) == 22, f"{d.sales_pkr_k.iloc[0]}->{d.sales_pkr_k.iloc[-1]}")
    x = np.arange(len(d))
    m, b = np.polyfit(x, d.sales_pkr_k, 1)
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(x, d.sales_pkr_k, color=BLUE, marker="o", markersize=2.5, linewidth=1.3)
    ax.plot(x, m * x + b, color=ORANGE, linestyle="--", label=f"least-squares trend, {m:.2f} per row")
    ax.set_ylim(0, 300)
    ax.set_xlabel("Row number (the recipe — the dates are ‘just labels’)")
    ax.set_ylabel("Sales per trading day (PKR thousand)")
    ax.legend(loc="lower right")
    ttl(ax, "Claim: “Sales grew steadily, 22%, across the quarter”")
    src(fig)
    save(fig, "case02_rebuild.png")

    s = d.set_index("date").sales_pkr_k
    full = s.reindex(pd.date_range(s.index.min(), s.index.max()))
    gap = full[full.isna()].index
    pre, post = s[:gap[0] - pd.Timedelta(days=1)], s[gap[-1] + pd.Timedelta(days=1):]
    sl_pre = np.polyfit((pre.index - pre.index[0]).days, pre.values, 1)[0]
    sl_post = np.polyfit((post.index - post.index[0]).days, post.values, 1)[0]
    sl_cal = np.polyfit((s.index - s.index[0]).days, s.values, 1)[0]
    dow = s.groupby(s.index.dayofweek).mean()
    N["c2"] = dict(n=len(s), span=int(len(full)), n_gap=int(len(gap)),
                   gap_start=str(gap[0].date()), gap_end=str(gap[-1].date()),
                   pre_mean=float(pre.mean()), post_mean=float(post.mean()),
                   n_pre=int(len(pre)), n_post=int(len(post)),
                   step=float(post.mean() - pre.mean()),
                   step_pct=float((post.mean() / pre.mean() - 1) * 100),
                   slope_row=float(m), slope_cal=float(sl_cal), sl_pre=float(sl_pre),
                   sl_post=float(sl_post), dow_min=float(dow.min()), dow_max=float(dow.max()),
                   dow_spread_pct=float((dow.max() / dow.min() - 1) * 100),
                   pre_last=int(pre.iloc[-1]), post_first=int(post.iloc[0]),
                   pre_first7=float(pre.iloc[:7].mean()), pre_last7=float(pre.iloc[-7:].mean()))
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(full.index, full.values, color=BLUE, linewidth=1.4)
    ax.axvspan(gap[0], gap[-1], color=GREY, alpha=0.25, linewidth=0)
    ax.text(gap[0] + (gap[-1] - gap[0]) / 2, 40, f"shop closed\n{len(gap)} days\n(no data)", ha="center",
            fontsize=8.5, color=SOFT)
    ax.hlines(pre.mean(), pre.index[0], pre.index[-1], color=ORANGE, linestyle="--")
    ax.hlines(post.mean(), post.index[0], post.index[-1], color=ORANGE, linestyle="--")
    ax.text(pre.index[1], pre.mean() - 28, f"mean {pre.mean():.0f}", fontsize=8.5, color=ORANGE)
    ax.text(post.index[2], post.mean() - 28, f"mean {post.mean():.0f}", fontsize=8.5, color=ORANGE)
    ax.set_ylim(0, 300)
    ax.set_ylabel("Sales per trading day (PKR thousand)")
    ax.set_xlabel("Calendar date (gap kept: equal distance = equal time)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ttl(ax, f"Sales did not grow steadily: they stepped up {N['c2']['step_pct']:.0f}% "
            f"(+{N['c2']['step']:.0f}k) across a {len(gap)}-day closure")
    src(fig, "Days with no trading are NaN, so the line breaks.")
    save(fig, "case02_redesign.png")


# ====================================================== 3  levels vs flows
def case03():
    print("\nCASE 3  bandwidth / level summed")
    d = pd.read_csv(DATA / "case03_bandwidth_levels.csv", parse_dates=["ts"]).set_index("ts")
    dsum = d.concurrent_users.resample("D").sum()
    jun, jul = dsum["2025-06"].mean(), dsum["2025-07"].mean()
    check("June ~8,800, July ~12,500, +43%", abs(jun - 8800) < 100 and abs(jul - 12500) < 100
          and round((jul / jun - 1) * 100) == 43, f"{jun:,.0f} -> {jul:,.0f}")
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(dsum.index, dsum.values, color=BLUE)
    ax.set_ylim(0, 15000)
    ax.set_ylabel("Concurrent users per day (sum of hourly readings)")
    ax.set_xlabel("Date")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ttl(ax, "Claim: “Peak load jumped 43% overnight on 1 July”")
    src(fig)
    save(fig, "case03_rebuild.png")

    dmean = d.concurrent_users.resample("D").mean()
    cnt = d.concurrent_users.resample("D").count()
    dmax = d.concurrent_users.resample("D").max()
    byt_sum = d.bytes_served.resample("D").sum()
    jm, jlm = dmean["2025-06"].mean(), dmean["2025-07"].mean()
    N["c3"] = dict(jun_sum=float(jun), jul_sum=float(jul), sum_pct=float((jul / jun - 1) * 100),
                   jun_mean=float(jm), jul_mean=float(jlm), mean_pct=float((jlm / jm - 1) * 100),
                   jun_hours=float(cnt["2025-06"].mean()), jul_hours=float(cnt["2025-07"].mean()),
                   jun_rows=int(cnt["2025-06"].sum()), jun_possible=720,
                   cover_pct=float(cnt["2025-06"].sum() / 720 * 100),
                   hour_ratio=float(cnt["2025-07"].mean() / cnt["2025-06"].mean()),
                   bytes_sum_pct=float((byt_sum["2025-07"].mean() / byt_sum["2025-06"].mean() - 1) * 100),
                   bytes_hr_jun=float(d.bytes_served["2025-06"].mean()),
                   bytes_hr_jul=float(d.bytes_served["2025-07"].mean()),
                   bytes_hr_pct=float((d.bytes_served["2025-07"].mean() / d.bytes_served["2025-06"].mean() - 1) * 100),
                   max_jun=float(dmax["2025-06"].mean()), max_jul=float(dmax["2025-07"].mean()),
                   max_pct=float((dmax["2025-07"].mean() / dmax["2025-06"].mean() - 1) * 100),
                   min_hours_jun=int(cnt["2025-06"].min()), max_hours_jun=int(cnt["2025-06"].max()),
                   full_days_jun=int((cnt["2025-06"] == 24).sum()),
                   full_days_jul=int((cnt["2025-07"] == 24).sum()),
                   corr_sum_count=float(np.corrcoef(cnt, dsum)[0, 1]),
                   corr_mean_count=float(np.corrcoef(cnt, dmean)[0, 1]),
                   missing_hours=int(len(pd.date_range(d.index.min(), d.index.max(), freq="h")) - len(d)))
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 5.2), sharex=True,
                                 gridspec_kw=dict(height_ratios=[2, 1], hspace=0.12))
    a1.plot(dmean.index, dmean.values, color=BLUE)
    a1.set_ylim(0, 800)
    a1.set_ylabel("Concurrent users\n(mean of recorded hourly readings)")
    ttl(a1, f"Load was flat ({N['c3']['mean_pct']:+.1f}%); the +43% is June having only "
            f"{N['c3']['jun_hours']:.0f} of 24 hours recorded per day", 64)
    a2.bar(cnt.index, cnt.values, color=GREEN, width=0.8)
    a2.set_ylim(0, 26)
    a2.set_ylabel("Hours recorded\nper day (count)")
    a2.set_xlabel("Date")
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    for a in (a1, a2):
        a.axvline(pd.Timestamp("2025-07-01"), color=GREY, linewidth=1, linestyle=":")
    src(fig, "A level (users connected at an instant) is averaged, never summed.")
    save(fig, "case03_redesign.png")


# ======================================================== 4  turning point
def case04():
    print("\nCASE 4  conversion / trailing mean")
    d = pd.read_csv(DATA / "case04_intervention_lag.csv", parse_dates=["date"]).set_index("date").conversion_pct
    tr = d.rolling(31).mean()
    ce = d.rolling(31, center=True).mean()
    check("trailing mean bottoms out 2025-09-07", str(tr.idxmin().date()) == "2025-09-07", tr.idxmin().date())
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(d.index, d.values, color=GREY, alpha=0.6, linewidth=0.9, label="Daily conversion (raw)")
    ax.plot(tr.index, tr.values, color=BLUE, label="31-day trailing mean")
    ax.axvline(tr.idxmin(), color=BLUE, linestyle=":")
    ax.annotate("‘started working’\n7 Sep", (tr.idxmin(), tr.min()), xytext=(tr.idxmin() - pd.Timedelta(days=48), 3.75),
                fontsize=8.5, arrowprops=dict(arrowstyle="->", color=SOFT))
    ax.set_ylabel("Conversion (% of sessions, daily)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.set_xlabel("Date (2025)")
    ax.legend(loc="upper right", fontsize=8)
    ttl(ax, "Claim: “The new checkout flow started working on 7 September”")
    src(fig)
    save(fig, "case04_rebuild.png")

    ce7 = d.rolling(7, center=True).mean()
    x = np.arange(len(d)); y = d.values
    best = None
    for k in range(20, len(d) - 20):
        X = np.column_stack([np.ones(len(d)), x, np.maximum(0, x - k)])
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        sse = ((y - X @ beta) ** 2).sum()
        if best is None or sse < best[0]:
            best = (sse, k, beta)
    kink = d.index[best[1]]
    X = np.column_stack([np.ones(len(d)), x, np.maximum(0, x - best[1])])
    fit = pd.Series(X @ best[2], index=d.index)
    lg = lag_at_turn(d, 31, how="min")
    wk = d.resample("W").mean()
    after = wk[wk.idxmin():]
    rises = int((after.diff().dropna() > 0).sum())
    N["c4"] = dict(trailing=str(lg["trailing_turn"].date()), centred=str(lg["centred_turn"].date()),
                   lag=lg["lag_periods"], half=lg["half_window"],
                   centred7=str(ce7.idxmin().date()), kink=str(kink.date()),
                   raw_min=str(d.idxmin().date()), tr_min=float(tr.min()), ce_min=float(ce.min()),
                   daily_sd=float(d.diff().std() / np.sqrt(2)), rise=float(d.iloc[-30:].mean() - d.iloc[:1].mean() * 0
                                                                          - d["2025-08-10":"2025-08-31"].mean()),
                   lo=float(d["2025-08-10":"2025-08-31"].mean()), hi=float(d.iloc[-14:].mean()),
                   n_weeks_rise=rises, n_weeks_after=int(len(after) - 1),
                   week_min=str(wk.idxmin().date()))
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(d.index, d.values, color=GREY, alpha=0.55, linewidth=0.9, label="Daily conversion (raw)")
    ax.plot(ce.index, ce.values, color=BLUE, label="31-day centred mean")
    ax.plot(tr.index, tr.values, color=ORANGE, linestyle="--", label="31-day trailing mean (the claim)")
    ax.plot(fit.index, fit.values, color=GREEN, linewidth=1.2, label="two-line fit (kink 28 Aug)")
    ax.axvline(lg["centred_turn"], color=BLUE, linestyle=":")
    ax.axvline(lg["trailing_turn"], color=ORANGE, linestyle=":")
    ax.annotate("", xy=(lg["trailing_turn"], 3.02), xytext=(lg["centred_turn"], 3.02),
                arrowprops=dict(arrowstyle="<->", color=INK))
    ax.text(lg["centred_turn"] + (lg["trailing_turn"] - lg["centred_turn"]) / 2, 2.93,
            f"{lg['lag_periods']} days\n= half-window", ha="center", va="top", fontsize=8.5)
    ax.set_ylim(2.7, 4.1)
    ax.set_ylabel("Conversion (% of sessions, daily)")
    ax.set_xlabel("Date (2025)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.legend(loc="upper right", fontsize=7.5)
    ttl(ax, f"The turn is about 23 Aug (centred), not 7 Sep: a {lg['lag_periods']}-day trailing "
            f"lag is half the 31-day window")
    src(fig, "y-axis does not start at zero (line chart of a rate, not bars).")
    save(fig, "case04_redesign.png")


# ====================================================== 5  seasonal window
def case05():
    print("\nCASE 5  revenue / cherry-picked window")
    d = pd.read_csv(DATA / "case05_revenue_window.csv")
    d["m"] = pd.to_datetime(d.month, format="%Y-%m")
    s = d.set_index("m").revenue_pkr_m
    w = s["2025-05":"2025-11"]
    check("7 points, 158.8 -> 92.2, -41.9%", len(w) == 7 and w.iloc[0] == 158.8 and w.iloc[-1] == 92.2
          and round((w.iloc[-1] / w.iloc[0] - 1) * 100, 1) == -41.9, f"{w.iloc[0]} -> {w.iloc[-1]}")
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(w.index, w.values, marker="o", color=BLUE)
    ax.set_ylim(0, 180)
    ax.set_ylabel("Revenue per month (PKR million)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.set_xlabel("Month (May–Nov 2025 only)")
    for t, v in w.items():
        ax.text(t, v + 6, f"{v:.0f}", ha="center", fontsize=8)
    ttl(ax, "Claim: “Revenue has fallen for six straight months”")
    src(fig)
    save(fig, "case05_rebuild.png")

    by = {y: s[str(y)].to_numpy() for y in (2023, 2024, 2025)}
    fall = {y: float(by[y][10] / by[y][4] - 1) * 100 for y in by}     # Nov vs May
    yoy = s["2025"].to_numpy() / s["2024"].to_numpy() - 1
    yoy2 = s["2024"].to_numpy() / s["2023"].to_numpy() - 1
    tot = s.groupby(s.index.year).sum()
    n_decl = {y: int((np.diff(by[y][4:11]) < 0).sum()) for y in by}
    N["c5"] = dict(fall=fall, yoy_min=float(yoy.min() * 100), yoy_max=float(yoy.max() * 100),
                   yoy_months_up=int((yoy > 0).sum()), yoy_dec=float(yoy[11] * 100),
                   yoy_may_nov_mean=float(np.mean(yoy[4:11]) * 100),
                   tot={int(k): float(v) for k, v in tot.items()},
                   tot24=float((tot[2024] / tot[2023] - 1) * 100),
                   tot25=float((tot[2025] / tot[2024] - 1) * 100),
                   n_decl=n_decl, peak_month={y: int(np.argmax(by[y]) + 1) for y in by},
                   trough_month={y: int(np.argmin(by[y]) + 1) for y in by},
                   n=len(w), y2025_dec=float(by[2025][11]), y2025_may=float(by[2025][4]),
                   jan25=float(by[2025][0]), jan23=float(by[2023][0]))
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.axvspan(4.5, 11.5, color=GREY, alpha=0.18, linewidth=0)
    cols = {2023: GREY, 2024: SOFT, 2025: BLUE}
    yoff = {2023: -5, 2024: 0, 2025: 5}
    for y in (2023, 2024, 2025):
        ax.plot(range(1, 13), by[y], marker="o", markersize=3.5, color=cols[y], linewidth=2.2 if y == 2025 else 1.6)
        ax.text(12.15, by[y][11] + yoff[y], f"{y}", color=cols[y], fontsize=9, va="center", fontweight="bold")
    ax.text(0.8, 22, "Fall from May to November in each year:\n" + "\n".join(
        f"  {y}: {fall[y]:+.1f}%" for y in (2023, 2024, 2025)), fontsize=8.5, color=INK, va="bottom")
    ax.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    ax.set_xlim(0.7, 12.9)
    ax.set_ylim(0, 180)
    ax.set_ylabel("Revenue per month (PKR million)")
    ax.set_xlabel("Month of year (shaded = the analyst’s May–Nov window)")
    ttl(ax, f"Every year falls ~42% from May to November — and each year sits above the last "
            f"(2025: +{N['c5']['tot25']:.0f}% on 2024)")
    src(fig, "Cycle plot: one line per year (tslib.cycle_plot idea).")
    save(fig, "case05_redesign.png")


# ===================================================== 6  partial month
def case06():
    print("\nCASE 6  orders / partial October")
    d = pd.read_csv(DATA / "case06_monthly_partial.csv", parse_dates=["date"]).set_index("date").orders
    m = d.resample("MS").sum()
    check("ten bars; Sep 10,805; Oct 4,041 (37%)", len(m) == 10 and m.iloc[-2] == 10805 and m.iloc[-1] == 4041
          and round(m.iloc[-1] / m.iloc[-2] * 100) == 37, f"{m.iloc[-2]}, {m.iloc[-1]}")
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.bar(m.index, m.values, width=22, color=BLUE)
    ax.set_ylim(0, 12000)
    ax.set_ylabel("Orders per month (count, sum)")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.set_xlabel("Month (2025)")
    ax.text(m.index[-1], m.iloc[-1] + 250, f"{m.iloc[-1]:,}", ha="center", fontsize=8.5, color=ORANGE)
    ttl(ax, "Claim: “Orders collapsed in October”")
    src(fig)
    save(fig, "case06_rebuild.png")

    mean = d.resample("MS").mean()
    cnt = d.resample("MS").count()
    N["c6"] = dict(sep_total=int(m.iloc[-2]), oct_total=int(m.iloc[-1]),
                   oct_pct=float(m.iloc[-1] / m.iloc[-2] * 100), oct_days=int(cnt.iloc[-1]),
                   oct_possible=31, oct_mean=float(mean.iloc[-1]), sep_mean=float(mean.iloc[-2]),
                   mean_pct=float((mean.iloc[-1] / mean.iloc[-2] - 1) * 100),
                   oct_min=int(d["2025-10"].min()), oct_max=int(d["2025-10"].max()),
                   jan_mean=float(mean.iloc[0]), last_date=str(d.index.max().date()),
                   cover_pct=float(cnt.iloc[-1] / 31 * 100),
                   prorated=float(mean.iloc[-1] * 31), highest=bool(mean.idxmax() == mean.index[-1]),
                   n_months_up=int((mean.diff().dropna() > 0).sum()))
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    bars = ax.bar(mean.index, mean.values, width=22, color=BLUE)
    bars[-1].set_hatch("////")
    bars[-1].set_facecolor("white")
    bars[-1].set_edgecolor(BLUE)
    ax.set_ylim(0, 450)
    ax.set_ylabel("Orders per day (monthly mean of daily totals)")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.set_xlabel("Month (2025)")
    for t, v in mean.items():
        ax.text(t, v + 8, f"{v:.0f}", ha="center", fontsize=8)
    ax.text(mean.index[-1], 90, f"partial:\n{cnt.iloc[-1]} of 31\ndays", ha="center", fontsize=8, color=BLUE,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
    ttl(ax, f"Orders per day kept rising: October’s {mean.iloc[-1]:.0f}/day is the best month yet — "
            f"its total is low because only {cnt.iloc[-1]} days exist")
    src(fig, "Hatched bar = incomplete month (1–11 Oct). Rate, not sum, because the periods are unequal.")
    save(fig, "case06_redesign.png")


# ===================================================== 7  stacked area
def case07():
    print("\nCASE 7  stacked products / the column nobody isolates")
    d = pd.read_csv(DATA / "case07_stacked_products.csv")
    d["m"] = pd.to_datetime(d.month, format="%Y-%m")
    d = d.set_index("m").drop(columns="month")
    tot = d.sum(axis=1)
    check("envelope ~548 .. ~709", abs(tot.min() - 548) < 1 and abs(tot.max() - 709) < 1,
          f"{tot.min():.1f} .. {tot.max():.1f}")
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    cols = [BLUE, ORANGE, GREEN, PINK]
    ax.stackplot(d.index, *[d[c] for c in d.columns], colors=cols, alpha=0.9,
                 labels=["Product A", "Product B", "Product C", "Product D (top)"])
    ax.set_ylim(0, 760)
    ax.set_ylabel("Revenue per month (PKR million)")
    ax.legend(loc="lower left", fontsize=7.5, ncol=4)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ttl(ax, "Claim: “Product D has been erratic since mid-2024”")
    src(fig)
    save(fig, "case07_rebuild.png")

    cv = (d.std() / d.mean() * 100)
    dsd = d.diff().std()
    base_d = d[["product_a", "product_b", "product_c"]].sum(axis=1)
    N["c7"] = dict(cv={c: float(v) for c, v in cv.items()}, dsd={c: float(v) for c, v in dsd.items()},
                   base_sd=float(base_d.diff().std()), d_first=float(d.product_d.iloc[0]),
                   d_last=float(d.product_d.iloc[-1]), d_min=float(d.product_d.min()),
                   d_max=float(d.product_d.max()), b_min=float(d.product_b.min()),
                   b_max=float(d.product_b.max()),
                   corr_b_base=float(np.corrcoef(d.product_b.diff().dropna(), base_d.diff().dropna())[0, 1]),
                   ratio=float(base_d.diff().std() / d.product_d.diff().std()),
                   d_2h_sd=float(d.product_d["2024-07":].diff().std()),
                   d_max_abs_change=float(d.product_d.diff().abs().max()),
                   tot_min=float(tot.min()), tot_max=float(tot.max()),
                   b_share_of_baseline_var=float(d.product_b.diff().var() / base_d.diff().var() * 100))
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 5.6), sharex=True, sharey=True)
    fig.subplots_adjust(hspace=0.5, wspace=0.12)
    names = {"product_a": "A", "product_b": "B", "product_c": "C", "product_d": "D"}
    notes = {"product_a": f"A: steady climb, CV {cv['product_a']:.1f}%",
             "product_b": f"B: the erratic one, ±{dsd['product_b']:.0f} a month (CV {cv['product_b']:.0f}%)",
             "product_c": f"C: flat, CV {cv['product_c']:.1f}%",
             "product_d": f"D: steadiest of all, CV {cv['product_d']:.1f}%"}
    for ax, (c, col) in zip(axes.ravel(), zip(d.columns, cols)):
        ax.plot(d.index, d[c], color=col, marker="o", markersize=2.5)
        ax.set_ylim(0, 300)
        ax.set_title(notes[c], loc="left", fontsize=9.5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%y"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    for ax in axes[:, 0]:
        ax.set_ylabel("PKR million / month")
    fig.suptitle("Product D is the calmest line of the four — the wobble belongs to B, which sits underneath it",
                 x=0.07, ha="left", fontsize=10.5, fontweight="bold", y=0.99)
    src(fig, "Same y-axis (0–300) in all four panels, so the swings are comparable.")
    save(fig, "case07_redesign.png")


# ===================================================== 8  channel pie
def case08():
    print("\nCASE 8  channel attribution / non-exclusive")
    d = pd.read_csv(DATA / "case08_channel_attrib.csv")
    cols = ["touch_search", "touch_social", "touch_email", "touch_direct"]
    ex = exclusivity_check(d, cols)
    sh = ex["shares_pct"]
    check("search 42.6 social 32.3 email 27.5 direct 28.6",
          [round(sh[c], 1) for c in cols] == [42.6, 32.3, 27.5, 28.6], list(sh.values()))
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    vals = [sh[c] for c in cols]
    labs = [f"{c.split('_')[1].title()} {sh[c]:.1f}%" for c in cols]
    ax.pie(vals, labels=labs, colors=[BLUE, ORANGE, GREEN, PINK], startangle=90, counterclock=False,
           wedgeprops=dict(edgecolor="white"), textprops=dict(fontsize=9))
    ttl(ax, "Claim: “Paid search drives 43% of our customers”", 60)
    src(fig, f"Labels sum to {ex['sum_pct']:.1f}%; matplotlib silently rescales the wedges to 100%.")
    save(fig, "case08_rebuild.png")

    flags = d[cols].astype(bool)
    n = len(d)
    one = flags.sum(axis=1) == 1
    only = {c: float((flags[c] & one).sum()) for c in cols}
    reach = {c: float(flags[c].sum()) for c in cols}
    wedge = {c: sh[c] / ex["sum_pct"] * 100 for c in cols}
    tc = flags.sum(axis=1).value_counts().sort_index()
    rev = {c: float(d.loc[flags[c], "revenue_pkr"].sum()) for c in cols}
    N["c8"] = dict(n=n, shares=sh, sum_pct=ex["sum_pct"], n_multi=ex["n_multi"], pct_multi=ex["pct_multi"],
                   only_pct={c: only[c] / n * 100 for c in cols},
                   only_of_reach_pct={c: only[c] / reach[c] * 100 for c in cols},
                   wedge_pct={c: wedge[c] for c in cols}, touch_counts={int(k): int(v) for k, v in tc.items()},
                   n_zero=ex["n_zero"], single_total_pct=float(one.mean() * 100),
                   avg_touch=float(flags.sum(axis=1).mean()),
                   search_only_share_of_single=float(only["touch_search"] / one.sum() * 100))
    order = sorted(cols, key=lambda c: -reach[c])
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    y = np.arange(len(order))
    o = [only[c] / n * 100 for c in order]
    sharedv = [(reach[c] - only[c]) / n * 100 for c in order]
    ax.barh(y, o, color=BLUE, height=0.62, label="Only this channel touched them")
    ax.barh(y, sharedv, left=o, color=BLUE, alpha=0.35, height=0.62, label="Also touched by another channel")
    for yi, c in zip(y, order):
        ax.text(reach[c] / n * 100 + 0.8, yi, f"{reach[c] / n * 100:.1f}% reach", va="center", fontsize=9)
        ax.text(only[c] / n * 100 / 2, yi, f"{only[c] / n * 100:.0f}%", va="center", ha="center",
                fontsize=8.5, color="white")
    ax.set_yticks(y, [c.split("_")[1].title() for c in order])
    ax.invert_yaxis()
    ax.set_xlim(0, 75)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("% of the 4,000 customers (a customer can appear in several bars)")
    ax.legend(loc="lower right", fontsize=8)
    ttl(ax, f"Search touched {sh['touch_search']:.1f}% of customers but was their ONLY touch for "
            f"{only['touch_search'] / n * 100:.0f}%: channels overlap, shares total {ex['sum_pct']:.0f}%")
    src(fig, f"{ex['n_multi']:,} customers ({ex['pct_multi']:.1f}%) were touched by 2+ channels. Reach is not exclusive credit.")
    save(fig, "case08_redesign.png")


# ===================================================== 9  denominator
def case09():
    print("\nCASE 9  premium share / shrinking denominator")
    d = pd.read_csv(DATA / "case09_premium_share.csv")
    d["share"] = d.premium_revenue_pkr_m / d.total_revenue_pkr_m * 100
    d["other"] = d.total_revenue_pkr_m - d.premium_revenue_pkr_m
    check("share 24.0% -> 38.0%", round(d.share.iloc[0], 1) == 24.0 and round(d.share.iloc[-1], 1) == 38.0,
          f"{d.share.iloc[0]:.1f} -> {d.share.iloc[-1]:.1f}")
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(d.quarter, d.share, marker="o", color=BLUE)
    ax.set_ylim(0, 45)
    ax.set_ylabel("Premium share of revenue (%)")
    ax.set_xlabel("Quarter")
    ax.annotate(f"{d.share.iloc[-1]:.0f}% — a record", (7, d.share.iloc[-1]), xytext=(4.6, 41),
                fontsize=9, arrowprops=dict(arrowstyle="->", color=SOFT))
    ttl(ax, "Claim: “Premium is now 38% of revenue — a record”")
    src(fig)
    save(fig, "case09_rebuild.png")

    N["c9"] = dict(s0=float(d.share.iloc[0]), s1=float(d.share.iloc[-1]),
                   p0=float(d.premium_revenue_pkr_m.iloc[0]), p1=float(d.premium_revenue_pkr_m.iloc[-1]),
                   t0=float(d.total_revenue_pkr_m.iloc[0]), t1=float(d.total_revenue_pkr_m.iloc[-1]),
                   o0=float(d.other.iloc[0]), o1=float(d.other.iloc[-1]),
                   p_pct=float((d.premium_revenue_pkr_m.iloc[-1] / d.premium_revenue_pkr_m.iloc[0] - 1) * 100),
                   t_pct=float((d.total_revenue_pkr_m.iloc[-1] / d.total_revenue_pkr_m.iloc[0] - 1) * 100),
                   o_pct=float((d.other.iloc[-1] / d.other.iloc[0] - 1) * 100),
                   share_if_total_flat=float(d.premium_revenue_pkr_m.iloc[-1] / d.total_revenue_pkr_m.iloc[0] * 100),
                   share_if_prem_flat=float(d.premium_revenue_pkr_m.iloc[0] / d.total_revenue_pkr_m.iloc[-1] * 100),
                   p_peak=float(d.premium_revenue_pkr_m.max()), p_min=float(d.premium_revenue_pkr_m.min()),
                   recompute=float(228.0 / 600.0 * 100))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.9), gridspec_kw=dict(wspace=0.28))
    a1.plot(d.quarter, d.share, marker="o", color=BLUE)
    a1.set_ylim(0, 45)
    a1.set_ylabel("Premium share of revenue (%)")
    a1.set_title("Numerator ÷ denominator: the share", loc="left", fontsize=9.5)
    a1.tick_params(axis="x", rotation=60, labelsize=7.5)
    a2.plot(d.quarter, d.total_revenue_pkr_m, marker="o", color=GREY, label="Total revenue")
    a2.plot(d.quarter, d.other, marker="s", color=ORANGE, label="Non-premium revenue")
    a2.plot(d.quarter, d.premium_revenue_pkr_m, marker="^", color=BLUE, label="Premium revenue")
    a2.set_ylim(0, 1100)
    a2.set_ylabel("Revenue per quarter (PKR million)")
    a2.set_title("The two parts of that fraction, same axis", loc="left", fontsize=9.5)
    a2.tick_params(axis="x", rotation=60, labelsize=7.5)
    a2.legend(fontsize=7.5, loc="upper right")
    for q, v in (("2024Q1", d.premium_revenue_pkr_m.iloc[0]), ("2025Q4", d.premium_revenue_pkr_m.iloc[-1])):
        a2.text(q, v + 40, f"{v:.0f}", color=BLUE, fontsize=8, ha="center")
    fig.suptitle(f"Premium’s share rose {N['c9']['s0']:.0f}%→{N['c9']['s1']:.0f}% because the rest of the business\n"
                 f"shrank {abs(N['c9']['o_pct']):.0f}%; premium revenue itself slipped {abs(N['c9']['p_pct']):.0f}%",
                 x=0.07, y=1.04, ha="left", fontsize=10.5, fontweight="bold")
    src(fig, "Both panels use the same data; the redesign adds the numerator and denominator rather than replacing the chart.")
    save(fig, "case09_redesign.png")


def main():
    style_defaults()
    for f in (case01, case02, case03, case04, case05, case06, case07, case08, case09):
        f()
    (HERE / "partA_numbers.json").write_text(json.dumps(N, indent=1, default=str))
    print("\nall nine rebuilds hit their self-check numbers; 18 figures written to figs/")


if __name__ == "__main__":
    buf = io.StringIO()

    class Tee:
        def write(self, s):
            sys.__stdout__.write(s)
            buf.write(s)

        def flush(self):
            sys.__stdout__.flush()

    with redirect_stdout(Tee()):
        main()
    (HERE / "partA_output.txt").write_text(buf.getvalue())

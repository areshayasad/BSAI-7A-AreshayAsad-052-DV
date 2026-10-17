#!/usr/bin/env python3
"""
Part D - the e-commerce review figure (2 x 2, exported at 300 dpi).

Run:  python3 partD_figure.py
Out:  partD_figure.png   partD_log.txt   partD_numbers.json

The script is also the cleaning module for Part B (`from partD_figure import
load_sessions`), so nothing is cleaned twice and nothing is cleaned two ways.

Everything here is SYNTHETIC course data (CDB601220, Week 4).

What is wrong with sessions_hourly.csv, in the order it is found
-----------------------------------------------------------------
 visible from  df.info / df.describe / df.device.value_counts / df.ts.head
   1. two timestamp formats  (ISO and DD/MM/YYYY) - and the second is day-first
   2. sessions == -1 used as a "no reading" sentinel
   3. device written six ways (Mobile / mobile / 'mobile ' / MOBILE ...)
   4. rows are not in time order
 visible only once the index is a real DatetimeIndex
   5. exact duplicate rows (many of them written in the OTHER format)
   6. whole days that were never recorded
 plus a fact about the extract: it stops part-way through September 2025.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import squarify
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter

from tslib import PALETTE, audit_index, rollup_other, save_fig, style_defaults
from vizlib import delta_e, simulate_cvd, worst_pair

DATA = HERE / "data"
WINDOW = 7            # days. Fixed BEFORE plotting: the cycle removed is weekly.
EXPECTED_START, EXPECTED_END = "2024-04-01 00:00", "2025-09-11 23:00"


# =========================================================================
#                          1.  SESSIONS: CLEAN IT
# =========================================================================
def parse_timestamps(ts: pd.Series, log: list) -> pd.Series:
    """Parse two formats, resolving the ambiguous one with evidence not a guess."""
    iso = ts.str.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
    sl = ts.str.match(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$")
    assert (iso | sl).all(), "a third timestamp format exists"

    p = ts[sl].str.extract(r"^(\d{2})/(\d{2})/")
    first, second = p[0].astype(int), p[1].astype(int)
    n_first_gt12 = int((first > 12).sum())
    n_second_gt12 = int((second > 12).sum())
    n_ambiguous = int(((first <= 12) & (second <= 12)).sum())
    n_same = int((first == second).sum())
    # A field above 12 cannot be a month. 'first' exceeds 12 on thousands of
    # rows and 'second' never does, so the slash format is DAY first.
    assert n_first_gt12 > 0 and n_second_gt12 == 0

    out = pd.Series(pd.NaT, index=ts.index, dtype="datetime64[us]")
    out[iso] = pd.to_datetime(ts[iso], format="%Y-%m-%d %H:%M:%S")
    out[sl] = pd.to_datetime(ts[sl], format="%d/%m/%Y %H:%M")
    assert out.notna().all()

    # the trap, measured: format="mixed" parses all rows and loses none
    mixed = pd.to_datetime(ts, format="mixed")
    moved = int((mixed != out).sum())
    log.append(dict(
        step="timestamp parse",
        rule=("ISO rows parsed as YYYY-MM-DD HH:MM:SS; slash rows parsed as "
              f"DD/MM/YYYY (day first - proved: first field >12 on {n_first_gt12} rows, "
              f"second field >12 on {n_second_gt12} rows)"),
        n=int(sl.sum()),
        detail=(f"{int(sl.sum())} slash rows; {n_ambiguous} of them have both "
                f"fields <=12 and are only resolved by that evidence "
                f"({n_same} have day==month and are safe either way). "
                f"pd.to_datetime(format='mixed') would put {moved} rows on the "
                f"wrong date and stretch the index to "
                f"{mixed.min():%Y-%m-%d} .. {mixed.max():%Y-%m-%d} "
                f"instead of {out.min():%Y-%m-%d} .. {out.max():%Y-%m-%d}"),
        mixed_range=[str(mixed.min()), str(mixed.max())],
        rows_moved_by_mixed=moved,
        n_slash=int(sl.sum()), n_iso=int(iso.sum()),
        n_ambiguous=n_ambiguous, n_same=n_same,
        n_first_gt12=n_first_gt12, n_second_gt12=n_second_gt12))
    return out


def load_sessions(data_dir: Path = DATA) -> dict:
    """Return every cleaned form of the sessions series, plus the audit log."""
    log: list[dict] = []
    raw = pd.read_csv(data_dir / "sessions_hourly.csv")
    n_raw = len(raw)
    raw_mean_hourly = float(raw.sessions.mean())
    raw_total = int(raw.sessions.sum())

    # ---- 1 parse ----------------------------------------------------------
    raw["dt"] = parse_timestamps(raw.ts, log)
    audit_before = audit_index(raw.set_index("dt"), "h")

    # ---- 3 device ---------------------------------------------------------
    dev_before = raw.device.nunique()
    norm = raw.device.str.strip().str.lower().str.title()
    n_dev_changed = int((norm != raw.device).sum())
    raw["device"] = norm
    log.append(dict(step="device labels", rule="strip, lower-case, Title-case",
                    n=n_dev_changed,
                    detail=f"{dev_before} spellings -> {raw.device.nunique()} "
                           f"({', '.join(sorted(raw.device.unique()))}); "
                           f"{n_dev_changed} rows relabelled, none removed"))

    # ---- 5 duplicates -----------------------------------------------------
    key = ["dt", "sessions", "orders", "revenue_pkr", "device"]
    dup = raw.duplicated(key, keep="first")
    n_dup = int(dup.sum())
    before_total = int(raw.sessions.clip(lower=0).sum())
    raw = raw[~dup].copy()
    after_total = int(raw.sessions.clip(lower=0).sum())
    assert not raw.dt.duplicated().any()
    log.append(dict(
        step="exact duplicates",
        rule="drop a row whose timestamp AND every value repeat an earlier row (keep first)",
        n=n_dup,
        detail=(f"{n_raw:,} -> {len(raw):,} rows; total valid sessions "
                f"{before_total:,} -> {after_total:,} "
                f"({(after_total / before_total - 1) * 100:+.2f}%)"),
        rows_before=n_raw, rows_after=len(raw),
        total_before=before_total, total_after=after_total))

    # ---- 4 sort / index ---------------------------------------------------
    was_sorted = bool(raw.dt.is_monotonic_increasing)
    raw = raw.sort_values("dt").set_index("dt")
    raw.index.name = "ts"
    log.append(dict(step="sort", rule="sort_values on the parsed timestamp",
                    n=0, detail=f"file was in time order: {was_sorted}; "
                                f"now monotonic: {raw.index.is_monotonic_increasing}"))

    # ---- 2 sentinel -------------------------------------------------------
    n_sent = int((raw.sessions < 0).sum())
    mean_before = float(raw.sessions.mean())
    sess = raw.sessions.where(raw.sessions >= 0)       # -1 -> NaN, never 0
    mean_after = float(sess.mean())
    log.append(dict(
        step="sessions sentinel",
        rule="sessions == -1 is 'no reading': set to NaN (not 0, not dropped); "
             "orders and revenue on that row are kept",
        n=n_sent,
        detail=f"mean sessions/hour {mean_before:,.1f} -> {mean_after:,.1f}",
        mean_before=mean_before, mean_after=mean_after))

    # ---- 6 gaps: counted on the HOURLY index, before any resample ----------
    full_h = pd.date_range(raw.index.min(), raw.index.max(), freq="h")
    audit_after = audit_index(raw, "h")
    missing_hours = full_h.difference(raw.index)
    hourly = sess.reindex(full_h)
    day_of_missing = pd.DatetimeIndex(missing_hours.normalize().unique())
    whole = [d for d in day_of_missing
             if (missing_hours.normalize() == d).sum() == 24]
    log.append(dict(
        step="missing periods",
        rule="reindex onto the complete hourly calendar; never fill, never zero",
        n=int(len(missing_hours)),
        detail=(f"{len(missing_hours)} missing hours = {len(whole)} whole days "
                f"(every gap is a multiple of 24 h; no partial days). Days: "
                + ", ".join(f"{d:%d %b %Y}" for d in whole)),
        missing_days=[str(d.date()) for d in whole]))

    # ---- partial tail -------------------------------------------------------
    last = raw.index.max()
    days_in_last = int(last.days_in_month)
    days_seen = int(last.day)
    log.append(dict(step="partial final month",
                    rule="kept, shaded and labelled; never compared as a month",
                    n=0, detail=f"{last:%B %Y}: {days_seen} of {days_in_last} days "
                                f"(extract ends {last:%d %b %Y %H:%M})"))

    # ---- hourly -> daily: a FLOW, so sum() ---------------------------------
    valid = hourly.notna()
    day = hourly.index.normalize()
    nvalid = valid.groupby(day).sum()
    complete = nvalid[nvalid == 24].index
    tmp = hourly[day.isin(complete)]
    share = tmp / tmp.groupby(tmp.index.normalize()).transform("sum")
    prof = share.groupby([share.index.dayofweek, share.index.hour]).mean()
    key_idx = pd.MultiIndex.from_arrays([hourly.index.dayofweek, hourly.index.hour])
    p_hour = pd.Series(prof.reindex(key_idx).to_numpy(), index=hourly.index)
    obs_share = p_hour.where(valid).groupby(day).sum(min_count=1)
    obs_sum = hourly.groupby(day).sum(min_count=1)
    daily = (obs_sum / obs_share).rename("sessions_per_day")
    daily.index.name = None
    topped = (nvalid < 24) & (nvalid > 0)
    adj_pct = (daily / obs_sum - 1)[topped] * 100
    daily_plain = obs_sum.rename("sessions_plain_sum")
    log.append(dict(
        step="daily aggregation",
        rule=("flow -> sum() of the 24 hourly counts. On a day with sentinel "
              "hours the observed sum is divided by the share of a typical "
              "(same weekday) day that those hours carry, so a missing evening "
              "hour does not look like a dip. Days with no data stay NaN."),
        n=int(topped.sum()),
        detail=(f"{int(topped.sum())} days topped up (mean {adj_pct.mean():+.1f}%, "
                f"max {adj_pct.max():+.1f}%); {int(daily.isna().sum())} days NaN; "
                f"{int(daily.notna().sum())} days observed"),
        n_topped=int(topped.sum()), adj_mean=float(adj_pct.mean()),
        adj_max=float(adj_pct.max())))

    daily_filled = daily.interpolate(method="time")
    interp_days = daily.index[daily.isna()]

    return dict(raw_n=n_raw, hourly=hourly, daily=daily, daily_plain=daily_plain,
                daily_filled=daily_filled, interp_days=interp_days,
                device=raw.device, rows=raw, log=log, audit_before=audit_before,
                audit_after=audit_after, partial=(days_seen, days_in_last, last),
                missing_days=whole, topped=topped, nvalid=nvalid,
                raw_mean_hourly=raw_mean_hourly, raw_total=raw_total)


# =========================================================================
#                         2.  CATALOGUE: A TREE
# =========================================================================
def load_catalogue(data_dir: Path = DATA):
    log = []
    c = pd.read_csv(data_dir / "revenue_catalogue.csv")
    shares8 = pd.read_csv(data_dir / "shares_eight.csv")
    n0 = len(c)
    # a tree needs one parent per child
    parents_per_sku = c.groupby("sku")[["category", "subcategory"]].nunique().max(axis=1)
    dup_sku = parents_per_sku[parents_per_sku > 1].index.tolist()
    first = c.sku.duplicated(keep="first")
    n_dup = int(first.sum())
    wear_before = c.groupby("subcategory").net_revenue_pkr_m.sum()
    wear_before = wear_before / wear_before.sum() * 100
    removed = c[first]
    c = c[~first].copy()
    wear_after = c.groupby("subcategory").net_revenue_pkr_m.sum()
    wear_after = wear_after / wear_after.sum() * 100
    log.append(dict(
        step="duplicate SKU", n=n_dup,
        rule=("a SKU may have one parent. SKU-0127 (name AUDI-04) is listed under "
              "Audio and again under Lifestyle > Wearables; the name prefix says "
              "Audio, so the second listing (last row of the file) is removed"),
        detail=(f"{n0} -> {len(c)} rows; Wearables share "
                f"{wear_before['Wearables']:.2f}% -> {wear_after['Wearables']:.2f}%; "
                f"removed SKU(s): {', '.join(removed.sku)} "
                f"({removed.net_revenue_pkr_m.sum():.2f} PKR m)")))
    neg = c.net_revenue_pkr_m < 0
    neg_tot = float(c.loc[neg, "net_revenue_pkr_m"].sum())
    neg_rows = c.loc[neg, ["sku", "sku_name", "net_revenue_pkr_m"]].copy()
    before_tot = float(c.net_revenue_pkr_m.sum())
    c_pos = c[~neg].copy()
    log.append(dict(
        step="negative net revenue", n=int(neg.sum()),
        rule="negatives have no area: removed from the area encoding, reported separately",
        detail=(f"{int(neg.sum())} SKUs, {neg_tot:.2f} PKR m in total "
                f"({neg_tot / before_tot * 100:.3f}% of net); catalogue net "
                f"{before_tot:,.1f} -> {c_pos.net_revenue_pkr_m.sum():,.1f} PKR m")))
    return dict(cat=c_pos, full=c, neg_rows=neg_rows, neg_total=neg_tot,
                log=log, shares8=shares8, n_raw=n0, wear_before=wear_before,
                wear_after=wear_after)


# =========================================================================
#                          3.  DRAWING HELPERS
# =========================================================================
PARENT_HUE = {            # one hue per parent. Okabe-Ito: 3 validated + the 4th
    "Mobile": PALETTE["series"][0],
    "Audio & Imaging": PALETTE["series"][1],
    "Lifestyle": PALETTE["series"][2],
    "Computing": PALETTE["series_4th"],
}


def _mix(hex_colour: str, t: float) -> str:
    """Blend a hex colour toward white by t (0 = unchanged, 1 = white)."""
    h = hex_colour.lstrip("#")
    rgb = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)
    rgb = rgb + (255 - rgb) * t
    return "#{:02X}{:02X}{:02X}".format(*rgb.round().astype(int))


def _lum(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    v = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    v = np.where(v <= 0.03928, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2])


def _text_on(hex_colour: str) -> str:
    """White or ink, whichever gives the better contrast on this fill."""
    l = _lum(hex_colour)
    white = 1.05 / (l + 0.05)
    ink = (l + 0.05) / (_lum(PALETTE["ink"]) + 0.05)
    return "white" if white >= ink else PALETTE["ink"]


def nested_treemap(ax, df, W, H, parent="category", child="subcategory",
                   value="net", header=5.2, pad=0.45):
    """Category -> sub-category treemap. One hue per parent, tints inside it."""
    totals = df.groupby(parent)[value].sum().sort_values(ascending=False)
    grand = totals.sum()
    outer = squarify.squarify(squarify.normalize_sizes(totals.values, W, H), 0, 0, W, H)
    for (cat, tot), r in zip(totals.items(), outer):
        x, y, dx, dy = r["x"], r["y"], r["dx"], r["dy"]
        base = PARENT_HUE[cat]
        ax.add_patch(Rectangle((x, y), dx - pad, header, facecolor=base,
                               edgecolor=PALETTE["surface"], linewidth=0.8))
        ax.text(x + 1.0, y + header / 2, f"{cat}  ·  {tot / grand * 100:.1f}%",
                ha="left", va="center", fontsize=9 if dx > 28 else 8,
                fontweight="bold", color=_text_on(base))
        kids = df[df[parent] == cat].groupby(child)[value].sum().sort_values(ascending=False)
        ix, iy, iw, ih = x, y + header, dx, dy - header
        inner = squarify.squarify(squarify.normalize_sizes(kids.values, iw, ih),
                                  ix, iy, iw, ih)
        tints = np.linspace(0.30, 0.62, max(len(kids), 2))
        for i, ((name, v), k) in enumerate(zip(kids.items(), inner)):
            fill = _mix(base, tints[i])
            ax.add_patch(Rectangle((k["x"], k["y"]), k["dx"] - pad, k["dy"] - pad,
                                   facecolor=fill, edgecolor=PALETTE["surface"],
                                   linewidth=0.8))
            w_in, h_in = k["dx"] - pad, k["dy"] - pad
            label = f"{name}\n{v:,.0f}"
            fs = 8.5
            if w_in < 15 or h_in < 12:
                label, fs = name, 7
            if w_in < 9:
                continue
            ax.text(k["x"] + (k["dx"] - pad) / 2, k["y"] + (k["dy"] - pad) / 2,
                    label, ha="center", va="center", fontsize=fs,
                    color=_text_on(fill), linespacing=1.25)
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")


def k_fmt(x, _pos=None):
    return f"{x / 1000:.0f}k"


# =========================================================================
#                              4.  THE FIGURE
# =========================================================================
def main():
    style_defaults()
    S = load_sessions()
    C = load_catalogue()
    daily, hourly = S["daily"], S["hourly"]
    log_lines: list[str] = []
    P = lambda *a: (print(*a), log_lines.append(" ".join(str(x) for x in a)))

    # -------------------------------------------------------- audit output
    P("=" * 76)
    P("AUDIT - sessions_hourly.csv  (tslib.audit_index on the hourly index)")
    P("=" * 76)
    ab, aa = S["audit_before"], S["audit_after"]
    P(f"  before cleaning: rows={ab['n_rows']:,} dtype_ok={ab['dtype_ok']} "
      f"monotonic={ab['monotonic']} duplicated={ab['n_duplicated']} "
      f"missing_hours={ab['n_missing']} span={ab['span'][0]} .. {ab['span'][1]}")
    P(f"  after  cleaning: rows={aa['n_rows']:,} dtype_ok={aa['dtype_ok']} "
      f"monotonic={aa['monotonic']} duplicated={aa['n_duplicated']} "
      f"missing_hours={aa['n_missing']} partial_tail={aa['partial_tail']} "
      f"({aa['tail_period']}: {aa['tail_count']} hourly rows)")
    P(f"  index min/max: {S['rows'].index.min()} .. {S['rows'].index.max()}  "
      f"(expected {EXPECTED_START} .. {EXPECTED_END})")
    assert str(S["rows"].index.min()) == EXPECTED_START + ":00"
    assert str(S["rows"].index.max()) == EXPECTED_END + ":00"
    P()
    P("DATA PROBLEMS HANDLED - each with its rule")
    for L in S["log"] + C["log"]:
        P(f"  [{L['step']}]  n={L['n']}")
        P(f"      rule  : {L['rule']}")
        P(f"      effect: {L['detail']}")

    # ----------------------------------------------------- numbers we quote
    smooth = daily.rolling(WINDOW, center=True, min_periods=4).mean().where(daily.notna())
    yoy = (daily["2025-09-01":"2025-09-11"].mean()
           / daily["2024-09-01":"2024-09-11"].mean() - 1) * 100
    trough = smooth["2024-04-01":"2024-07-31"].idxmin()
    trough2 = smooth["2025-03-01":"2025-07-31"].idxmin()
    bf = pd.Timestamp("2024-11-29")
    bf_val = float(daily[bf])

    hh = hourly.dropna()
    heat = (hh.groupby([hh.index.dayofweek, hh.index.hour]).mean()
              .unstack().reindex(range(7)))
    wk = hh[hh.index.dayofweek >= 5].mean()
    wd = hh[hh.index.dayofweek < 5].mean()
    wk_gap = (wk / wd - 1) * 100
    peak_dow, peak_hour = np.unravel_index(np.nanargmax(heat.to_numpy()), heat.shape)
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_means = hh.groupby(hh.index.dayofweek).mean()

    cat = C["cat"].rename(columns={"net_revenue_pkr_m": "net"})
    sub = cat.groupby(["category", "subcategory"]).net.sum().reset_index()
    sub["share"] = sub.net / sub.net.sum() * 100
    assert abs(sub.share.sum() - 100) < 1e-6
    # tree test: every child has one parent, children sum to the parent
    assert (cat.groupby("subcategory").category.nunique() == 1).all()
    assert abs(sub.net.sum() - cat.net.sum()) < 1e-9
    other, other_note = rollup_other(sub.set_index("subcategory").net, 1.0)
    sub = sub.sort_values("net", ascending=False).reset_index(drop=True)
    top_cat = cat.groupby("category").net.sum().sort_values(ascending=False)
    top_cat_share = top_cat / top_cat.sum() * 100

    # self-check against the answer key supplied with the data
    s8 = C["shares8"].set_index("subcategory").share_pct
    mine = sub.set_index("subcategory").share
    diff = (mine - s8).abs()
    P()
    P("HIERARCHY SELF-CHECK vs shares_eight.csv  (limit: 0.3 percentage points)")
    for n in sub.subcategory:
        P(f"   {n:<12} mine {mine[n]:6.2f}%  file {s8[n]:6.2f}%  diff {mine[n] - s8[n]:+.2f}")
    P(f"   max |diff| = {diff.max():.2f} pp  ->  "
      f"{'PASS' if diff.max() <= 0.3 else 'FAIL'}")
    assert diff.max() <= 0.3
    P(f"   Other bucket: {other_note}")
    P(f"   negatives not drawn: {len(C['neg_rows'])} SKUs, {C['neg_total']:.2f} PKR m")

    # palette: proved, not claimed
    hues = list(PARENT_HUE.values())
    P()
    P("PALETTE PROOF (vizlib.worst_pair, every pair, OKLab dE x100)")
    pal_proof = {}
    for kind in (None, "deutan", "protan", "tritan"):
        i, j, a, b, d = worst_pair(hues, kind)
        P(f"   {kind or 'normal':<7} closest pair: slots {i}&{j} {a} / {b}  dE={d:.1f}")
        pal_proof[kind or "normal"] = round(d, 1)
    P("   4th hue (#CC79A7) is below 3:1 contrast and has a thin CVD margin, so "
      "every parent is also named in text on the treemap and in the bar legend.")

    # -------------------------------------------------------------- figure
    FW, FH = 16, 11.6
    fig, axes = plt.subplots(2, 2, figsize=(FW, FH))
    fig.subplots_adjust(left=0.065, right=0.975, top=0.875, bottom=0.085,
                        wspace=0.17, hspace=0.38)
    ax1, ax2, ax3, ax4 = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

    def wrap(t, n=64):
        return "\n".join(textwrap.wrap(t, n))

    # ---- panel 1: daily series, raw grey, 7-day centred mean on top -------
    ax1.plot(daily.index, daily.values, color=PALETTE["muted"], alpha=0.55,
             linewidth=0.9, label="Daily sessions (raw)")
    ax1.plot(smooth.index, smooth.values, color=PALETTE["series"][0], linewidth=2.2,
             label=f"{WINDOW}-day centred rolling mean")
    miss = pd.DatetimeIndex(S["interp_days"])
    ax1.plot(miss, np.full(len(miss), 1400), linestyle="none", marker="|",
             markersize=9, markeredgewidth=1.6, color=PALETTE["highlight"],
             label=f"{len(miss)} missing days (no data - not zero)", clip_on=False)
    ylim_top = 62000
    ax1.set_ylim(0, ylim_top)
    ax1.annotate(f"Black Friday 29 Nov 2024: {bf_val:,.0f}\n(off scale; it lifts the 7-day\nmean for the 7 days around it)",
                 xy=(bf, ylim_top - 800), xytext=(pd.Timestamp("2025-01-12"), 50000),
                 fontsize=8.5, color=PALETTE["ink"], ha="left", va="center",
                 arrowprops=dict(arrowstyle="->", color=PALETTE["ink_soft"], lw=1))
    last = S["rows"].index.max()
    ax1.axvspan(pd.Timestamp(last.year, last.month, 1), last + pd.Timedelta(hours=1),
                color=PALETTE["muted"], alpha=0.25, linewidth=0)
    ax1.text(pd.Timestamp(last.year, last.month, 1) - pd.Timedelta(days=4), 58500,
             f"partial month\n({S['partial'][0]} of {S['partial'][1]} days)",
             fontsize=7.5, ha="right", va="top", color=PALETTE["ink_soft"])
    ax1.set_title(wrap(f"{WINDOW}-day centred mean: traffic follows an annual wave "
                       f"(spring trough, late May–Jun in 2025); 1–11 Sep 2025 is {yoy:+.0f}% on the same days of 2024",
                       60), loc="left", fontsize=11)
    ax1.set_ylabel("Sessions per day (sum of 24 hourly counts)")
    ax1.set_xlabel("Date (daily; the extract ends 11 Sep 2025)")
    ax1.yaxis.set_major_formatter(FuncFormatter(k_fmt))
    loc = mdates.AutoDateLocator(minticks=4, maxticks=8)
    ax1.xaxis.set_major_locator(loc)
    ax1.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
    ax1.legend(loc="upper left", bbox_to_anchor=(0.0, 0.98), fontsize=8)

    # ---- panel 2: dow x hour heatmap --------------------------------------
    im = ax2.imshow(heat.to_numpy(), aspect="auto", cmap=PALETTE["sequential"],
                    origin="upper")
    ax2.grid(False)
    ax2.set_yticks(range(7), dow_names)
    ax2.set_xticks(range(0, 24, 3), [f"{h:02d}:00" for h in range(0, 24, 3)])
    for s in ax2.spines.values():
        s.set_visible(False)
    ax2.set_title(wrap(f"Weekends run {wk_gap:.0f}% above weekdays, and every day peaks "
                       f"in the evening ({dow_names[peak_dow]} {peak_hour:02d}:00 is the "
                       f"busiest hour)"), loc="left", fontsize=11)
    ax2.set_xlabel("Hour of day (local)")
    ax2.set_ylabel("Day of week")
    cb = fig.colorbar(im, ax=ax2, fraction=0.04, pad=0.02)
    cb.set_label("Mean sessions per hour (mean of hourly counts)")
    cb.outline.set_visible(False)
    cb.ax.yaxis.set_major_formatter(FuncFormatter(k_fmt if heat.max().max() > 4000
                                                  else (lambda x, p: f"{x:,.0f}")))
    ax2.tick_params(length=0)

    # ---- panel 3: nested treemap ------------------------------------------
    pos = ax3.get_position()
    W = 100.0
    H = W * (pos.height * FH) / (pos.width * FW)
    nested_treemap(ax3, cat, W, H)
    ph = sub.set_index("subcategory")
    ax3.set_title(wrap(f"{top_cat.index[0]} holds {top_cat_share.iloc[0]:.0f}% of net revenue; "
                       f"the mass sits in Phones, Laptops and Audio "
                       f"({ph.share[['Phones', 'Laptops', 'Audio']].sum():.0f}% together)"),
                  loc="left", fontsize=11)
    ax3.annotate("Area = net revenue, PKR m (printed on each block). Hue = parent category; "
                 "tints separate its sub-categories.",
                 xy=(0, 0), xycoords="axes fraction", xytext=(0, -6),
                 textcoords="offset points", ha="left", va="top", fontsize=8.5,
                 color=PALETTE["ink_soft"])

    # ---- panel 4: sorted bars, values printed ------------------------------
    y = np.arange(len(sub))
    colours = [PARENT_HUE[c] for c in sub.category]
    ax4.barh(y, sub.net, color=colours, height=0.68)
    ax4.set_yticks(y, sub.subcategory)
    ax4.invert_yaxis()
    xmax = sub.net.max() * 1.30
    ax4.set_xlim(0, xmax)
    for yi, (v, s) in enumerate(zip(sub.net, sub.share)):
        ax4.text(v + xmax * 0.012, yi, f"{v:,.1f}  ({s:.1f}%)", va="center",
                 ha="left", fontsize=9, color=PALETTE["ink"])
    ax4.grid(axis="y", visible=False)
    ax4.spines["left"].set_visible(False)
    ax4.tick_params(axis="y", length=0)
    gap = sub.net.iloc[0] - sub.net.iloc[1]
    ax4.set_title(wrap(f"{sub.subcategory[0]} lead {sub.subcategory[1]} by "
                       f"{sub.share[0] - sub.share[1]:.1f} points; the bottom four "
                       f"sub-categories together are {sub.share.iloc[-4:].sum():.0f}%"),
                  loc="left", fontsize=11)
    ax4.set_xlabel(f"Net revenue, PKR m (sum over {len(cat)} SKUs; "
                   f"net = revenue − returns)")
    ax4.legend(handles=[Patch(color=PARENT_HUE[c], label=c) for c in top_cat.index],
               title="Parent category", loc="lower right", fontsize=8.5,
               title_fontsize=8.5)

    fig.suptitle("Monday review: traffic trajectory, weekly rhythm and the revenue catalogue",
                 x=0.065, y=0.985, ha="left", fontsize=15, fontweight="bold",
                 color=PALETTE["ink"])

    neg = C["neg_rows"]
    note = (
        f"Source: sessions_hourly.csv, revenue_catalogue.csv - SYNTHETIC course data, CDB601220 Week 4.  "
        f"Sessions: {S['raw_n']:,} rows -> {S['raw_n'] - [l for l in S['log'] if l['step']=='exact duplicates'][0]['n']:,} "
        f"after removing 286 exact duplicates; 287 sessions=-1 sentinels set to missing "
        f"({int(S['topped'].sum())} days topped up for the lost hours);\n"
        f"13 never-recorded days left as gaps (not interpolated); day-first DD/MM/YYYY dates resolved from rows with day > 12; "
        f"daily aggregation = sum (flow); smoothing = {WINDOW}-day centred mean, min 4 of 7 days, fixed before plotting; "
        f"no start date selected.  Catalogue: {C['n_raw']} rows -> {len(C['full'])} unique SKUs "
        f"(SKU-0127 listed twice, removed from Wearables) -> {len(cat)} with net > 0 "
        f"({len(neg)} negative SKUs, {C['neg_total']:.2f} PKR m, not drawn). Other bucket: none - smallest "
        f"sub-category is {sub.share.min():.1f}% (rollup_other at 1%: no categories below 1%). "
        f"Aspect ratio of panel 1: {ax1.get_position().width * FW / (ax1.get_position().height * FH):.2f}:1 (width:height).")
    out = HERE / "partD_figure.png"
    note = "\n".join(textwrap.fill(par, 215) for par in note.split("\n"))
    save_fig(fig, out, note=note)           # savefig BEFORE any show()
    plt.close(fig)
    P()
    P(f"saved {out.name}")

    nums = dict(
        yoy_sep=float(yoy), bf=bf_val, weekend_gap_pct=float(wk_gap),
        peak=f"{dow_names[peak_dow]} {peak_hour:02d}:00",
        shares=sub.set_index("subcategory").share.round(2).to_dict(),
        top_cat_share=top_cat_share.round(2).to_dict(),
        max_diff_vs_file=float(diff.max()), palette_proof=pal_proof,
        n_missing_days=len(miss), n_topped=int(S["topped"].sum()),
        trough_1=str(trough.date()), trough_2=str(trough2.date()),
        other_note=other_note,
        neg=dict(n=len(neg), total=C["neg_total"]),
        wearables=dict(before=float(C["wear_before"]["Wearables"]),
                       after=float(C["wear_after"]["Wearables"])),
        log=[{k: v for k, v in l.items()} for l in S["log"] + C["log"]],
        audit_before={k: v for k, v in ab.items()},
        audit_after={k: v for k, v in aa.items()},
        day_means=day_means.round(1).tolist())
    (HERE / "partD_numbers.json").write_text(json.dumps(nums, indent=1, default=str))
    (HERE / "partD_log.txt").write_text("\n".join(log_lines))


if __name__ == "__main__":
    main()

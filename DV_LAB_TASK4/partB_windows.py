#!/usr/bin/env python3
"""
Part B - smoothing, windows and panel shape, COMPUTED.

Run:  python3 partB_windows.py          (prints everything; also writes
                                          partB_output.txt and partB_windows.png)

Works on the cleaned daily session series from Part D (parsed with the
day-first rule, de-duplicated, sentinels removed, gaps counted, partial
September reported). SYNTHETIC course data, CDB601220 Week 4.

Two versions of that series are used, and which one is stated every time:
  daily         529 calendar days, 13 NaN (never recorded). Used wherever
                pandas can cope with NaN.
  daily_filled  the same 13 days linearly interpolated. Used ONLY where the
                function cannot take NaN (seasonal_decompose, lag_at_turn).
                Interpolated days are never plotted as data.
"""
from __future__ import annotations

import io
import sys
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
from matplotlib.colors import ListedColormap
from matplotlib.ticker import FuncFormatter
from statsmodels.tsa.seasonal import seasonal_decompose

from partD_figure import load_sessions
from tslib import PALETTE, banked_figsize, lag_at_turn, save_fig, style_defaults, window_report

BF = pd.Timestamp("2024-11-29")


def run() -> dict:
    S = load_sessions()
    daily, filled = S["daily"], S["daily_filled"]
    R: dict = {}
    print("=" * 78)
    print("PART B - computed on the cleaned DAILY session series (sum of hourly flow)")
    print(f"  {daily.index.min():%Y-%m-%d} .. {daily.index.max():%Y-%m-%d}   "
          f"{len(daily)} calendar days, {int(daily.isna().sum())} missing (NaN), "
          f"{int(daily.notna().sum())} observed;  mean {daily.mean():,.0f}/day")
    print("=" * 78)

    # ------------------------------------------------------------------ B1
    print("\nB1  THE WINDOW IS A HYPOTHESIS  (tslib.window_report, centred)")
    wr = window_report(daily, (7, 28, 91), center=True)
    # extra columns: how much of the WEEKLY cycle survives, and how much of
    # the slower annual wave (the thing the board wants to see) survives
    def weekly_swing(x: pd.Series) -> float:
        dev = x - x.rolling(7, center=True, min_periods=4).mean()
        prof = dev.groupby(dev.index.dayofweek).mean()
        return float(prof.max() - prof.min())
    raw_sw = weekly_swing(daily)
    wave_7 = None
    rows = []
    for w in wr.window:
        w = int(w)
        sm = daily.rolling(w, center=True, min_periods=max(2, w // 2)).mean()
        interior = sm.iloc[w // 2: len(sm) - w // 2]
        wave = float(interior.max() - interior.min())
        if w == 7:
            wave_7 = wave
        rows.append(dict(weekly_swing_left_pct=round(weekly_swing(sm) / raw_sw * 100, 1),
                         wave_range=round(wave, 0)))
    wr = pd.concat([wr, pd.DataFrame(rows)], axis=1)
    wr["wave_kept_vs_7d_pct"] = (wr.wave_range / wave_7 * 100).round(1)
    wr["pct_of_series_lost_at_ends"] = (wr.periods_lost_each_end * 2
                                        / len(daily) * 100).round(1)
    print(wr.to_string(index=False))
    print(f"\n  raw weekly swing (Sat/Sun vs Mon-Thu, peak-to-trough of the day-of-week "
          f"profile) = {raw_sw:,.0f} sessions/day")
    print("  cycle each window removes:")
    print("    7  : the weekly cycle, exactly (7 is one full period) - and nothing slower.")
    print("    28 : the weekly cycle (4 whole weeks) plus about one calendar month of")
    print("         wobble. Slower waves survive.")
    print("    91 : the weekly cycle and the month, and it also begins to eat the annual")
    print(f"         wave itself: only {wr.wave_kept_vs_7d_pct.iloc[2]:.0f}% of the 7-day wave range")
    print(f"         survives, and {wr.periods_lost_each_end.iloc[2]} days are lost at EACH end")
    print(f"         ({wr.pct_of_series_lost_at_ends.iloc[2]:.0f}% of a 529-day series).")
    wk_gap = (daily[daily.index.dayofweek >= 5].mean()
              / daily[daily.index.dayofweek < 5].mean() - 1) * 100
    print("  CHOICE for Part D: 7 days. The cycle I am cancelling is weekly (Sat/Sun daily")
    print(f"  totals run {wk_gap:.0f}% above Mon-Fri), and 7 is the shortest window that cancels it exactly.")
    print("  A window that is not a multiple of 7 would leave a weekday-dependent ripple;")
    print("  anything longer than 28 starts to cancel the seasonal turn the board keeps")
    print("  missing. 'Variation removed' rises with the window by construction, so it")
    print("  cannot pick the window - the cycle does. (Fixed before plotting.)")
    R["window_report"] = wr.to_dict("records")

    # ------------------------------------------------------------------ B2
    print("\nB2  THREE SMOOTHERS AGAINST ONE SPIKE  (29 Nov 2024, Black Friday)")
    raw_bf = float(daily[BF])
    med14 = float(filled["2024-11-22":"2024-12-05"].median())
    c_mean = float(filled.rolling(14, center=True).mean()[BF])
    c_med = float(filled.rolling(14, center=True).median()[BF])
    ewma = float(filled.ewm(span=14, adjust=False).mean()[BF])
    print(f"  raw value                       {raw_bf:>10,.0f}")
    print(f"  fortnight median (22 Nov-5 Dec) {med14:>10,.0f}   <- 'normal'")
    print(f"  14-day centred MEAN             {c_mean:>10,.0f}   ({c_mean / med14:.2f}x normal)")
    print(f"  14-day centred MEDIAN           {c_med:>10,.0f}   ({c_med / med14:.2f}x normal)")
    print(f"  EWMA (span 14, trailing)        {ewma:>10,.0f}   ({ewma / med14:.2f}x normal)")
    print("  -> the mean and the EWMA smear one day's 113,710 across the neighbours and")
    print(f"     make the BASELINE look {(c_mean / med14 - 1) * 100:.0f}% and {(ewma / med14 - 1) * 100:.0f}% higher; the median ignores it.")
    print("  Monitoring dashboard : EWMA. It needs no future data, reacts the day the")
    print("     spike arrives (so an alert can fire), then decays instead of leaving a")
    print("     14-day plateau. Plot the raw spike beside it - it is the thing to see.")
    print("  Quarterly report    : centred 14-day MEDIAN. A one-day event should not")
    print("     move the trajectory; the report states the event separately")
    print("     ('Black Friday: 113,710') rather than letting a mean spread it.")
    R["smoothers"] = dict(raw=raw_bf, median14=med14, mean=c_mean, median=c_med, ewma=ewma)

    # ------------------------------------------------------------------ B3
    print("\nB3  DECOMPOSE IT  (statsmodels seasonal_decompose on the gap-filled series)")
    dec = seasonal_decompose(filled, model="additive", period=7)
    seas = dec.seasonal
    amp = float(seas.max() - seas.min())
    prof = seas.iloc[:7]
    lo_d, hi_d = prof.idxmin().day_name(), prof.idxmax().day_name()
    big = dec.resid.abs().idxmax()
    print(f"  weekly seasonal component: peak-to-trough = {amp:,.0f} sessions/day "
          f"({hi_d} {prof.max():+,.0f}, {lo_d} {prof.min():+,.0f})")
    print(f"  largest residual: {big:%d %b %Y}  = {dec.resid[big]:+,.0f} sessions "
          f"(next largest: {dec.resid.drop(big).abs().max():,.0f})")
    print("  Everything explainable (trend + weekly rhythm) is gone; what is left on")
    print("  29 Nov 2024 is Black Friday - the event worth investigating.")
    try:
        seasonal_decompose(filled, model="additive", period=365)
        p365 = "ran"
    except ValueError as e:
        p365 = str(e)
    print(f"  period=365: statsmodels refuses - \"{p365}\".")
    print("  (a year-long period needs 2 full cycles = 730 daily points; there are 529.)")
    print("  In one sentence: with a 365-day period, anything that recurs on the same")
    print("  calendar day each year (Black Friday, an Eid sale) would move out of `resid`")
    print("  and into `seasonal` - but with 1.45 years of data a once-a-year event and a")
    print("  one-off are indistinguishable, which is exactly why it cannot be run here.")
    R["decompose"] = dict(amp=amp, big=str(big.date()), resid=float(dec.resid[big]),
                          p365=p365)

    # ------------------------------------------------------------------ B4
    print("\nB4  TRAILING OR CENTRED  (tslib.lag_at_turn, 31-day window)")
    seg = filled["2025-01-01":]          # after Black Friday has left every window
    lg = lag_at_turn(seg, 31, how="min")
    print(f"  turn = the spring-2025 trough, searched in {seg.index.min():%d %b %Y} onward")
    print(f"  centred  window finds the minimum on {lg['centred_turn']:%d %b %Y}")
    print(f"  trailing window finds the minimum on {lg['trailing_turn']:%d %b %Y}")
    print(f"  lag = {lg['lag_periods']} days   vs   half-window = {lg['half_window']} days")
    print("  The lag is arithmetic, not a bug: a trailing mean cannot know about a turn")
    print("  until the window has filled with post-turn days, i.e. about half a window.")
    print("  A live dashboard refreshes every morning and has no future data, so it MUST")
    print("  show the trailing mean. Its caption must say: '31-day trailing mean - turning")
    print(f"  points show up about {lg['half_window']} days after they happen'.")
    R["lag"] = dict(trailing=str(lg["trailing_turn"].date()),
                    centred=str(lg["centred_turn"].date()),
                    lag=lg["lag_periods"], half=lg["half_window"])

    # ------------------------------------------------------------------ B5
    print("\nB5  THE WINDOW IS A CLAIM  (12 start months x 5 window lengths = 60 fits)")
    starts = pd.date_range("2024-04-01", periods=12, freq="MS")   # first 12 month-starts
    wins = [7, 14, 28, 56, 91]
    grid = np.zeros((len(starts), len(wins)))
    for i, st in enumerate(starts):
        for j, w in enumerate(wins):
            seg = daily[st: st + pd.Timedelta(days=w - 1)].dropna()
            x = (seg.index - st).days.to_numpy(float)
            grid[i, j] = np.polyfit(x, seg.to_numpy(float), 1)[0]
    rising = int((grid > 0).sum())
    falling = int((grid < 0).sum())
    full_slope = np.polyfit((daily.dropna().index - daily.index[0]).days.to_numpy(float),
                            daily.dropna().to_numpy(float), 1)[0]
    print(f"  start months: {starts[0]:%b %Y} .. {starts[-1]:%b %Y} (the first 12 month-starts "
          f"of the series - chosen BEFORE looking)")
    print(f"  RISING trends : {rising}   FALLING trends : {falling}   (of {grid.size})")
    by_w = pd.DataFrame({"window_days": wins,
                         "rising": (grid > 0).sum(axis=0),
                         "falling": (grid < 0).sum(axis=0)})
    print(by_w.to_string(index=False))
    print(f"  the whole series (no window chosen) rises {full_slope:+,.1f} sessions/day per day")
    print("  Lie Factor = (effect shown) / (effect in the data). It presumes the data")
    print("  HAS one effect to divide by. For a cherry-picked window there is no such")
    print("  denominator: the same unchanged series contains rising AND falling 'effects'")
    print("  depending on where you start and how long you look, so every window is its")
    print("  own numerator with nothing agreed to put underneath it. (And the 'ink' is")
    print("  not wrong - the slope IS that in that window; the framing is.)")
    print("  The honest substitute: report the sensitivity itself - the share of")
    print("  start/window choices that agree with the one shown (here "
          f"{max(rising, falling)}/{grid.size}), show the full-range line, and")
    print("  state how the window was chosen (a specification curve).")
    R["sweep"] = dict(rising=rising, falling=falling, total=int(grid.size),
                      full_slope=float(full_slope), by_window=by_w.to_dict("records"))

    # ----------------------------------------------------------- sensitivity
    print("\nSENSITIVITY - does the treatment of the 287 sentinel hours change any answer?")
    print("  A = series used above (sentinel hours topped up from the same-weekday profile)")
    print("  B = plain sum of the hours that were recorded (the brief quotes a fortnight")
    print("      median of 'about 24,600' - B is the closer match)")
    plain = S["daily_plain"].reindex(daily.index)
    plain_f = plain.interpolate(method="time")

    def key(d, f):
        out = {}
        out["fortnight median"] = float(f["2024-11-22":"2024-12-05"].median())
        out["14d centred mean"] = float(f.rolling(14, center=True).mean()[BF])
        out["14d centred median"] = float(f.rolling(14, center=True).median()[BF])
        out["EWMA span 14"] = float(f.ewm(span=14, adjust=False).mean()[BF])
        dd = seasonal_decompose(f, model="additive", period=7)
        out["weekly p2p"] = float(dd.seasonal.max() - dd.seasonal.min())
        out["largest resid date"] = str(dd.resid.abs().idxmax().date())
        l2 = lag_at_turn(f["2025-01-01":], 31, how="min")
        out["lag (days)"] = l2["lag_periods"]
        up = dn = 0
        for st in starts:
            for w in wins:
                sg = d[st: st + pd.Timedelta(days=w - 1)].dropna()
                sl = np.polyfit((sg.index - st).days.to_numpy(float), sg.to_numpy(float), 1)[0]
                up += sl > 0
                dn += sl < 0
        out["rising / falling of 60"] = f"{up} / {dn}"
        return out

    ka, kb = key(daily, filled), key(plain, plain_f)
    print(f"  {'quantity':<24}{'A (topped up)':>16}{'B (plain sum)':>16}")
    for k in ka:
        va, vb = ka[k], kb[k]
        fa = f"{va:,.0f}" if isinstance(va, float) else str(va)
        fb = f"{vb:,.0f}" if isinstance(vb, float) else str(vb)
        print(f"  {k:<24}{fa:>16}{fb:>16}")
    print("  Same spike date, same lag, same ordering of the three smoothers, and the")
    print("  window sweep forks under both (34/26 vs 32/28): the sentinel treatment moves")
    print("  levels by under ~3% and changes no conclusion. Series A is used throughout.")
    R["sensitivity"] = dict(A=ka, B=kb)

    R["_plot"] = dict(daily=daily, filled=filled, grid=grid, starts=starts, wins=wins,
                      lg=lg, dec=dec)
    return R


def make_figure(R: dict):
    style_defaults()
    P = R["_plot"]
    daily, filled, lg = P["daily"], P["filled"], P["lg"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    fig.subplots_adjust(left=0.05, right=0.985, top=0.80, bottom=0.17, wspace=0.28)
    a, b, c = axes

    z = filled["2024-11-12":"2024-12-16"]
    a.plot(z.index, z.values, color=PALETTE["muted"], alpha=0.7, label="Raw daily sessions")
    a.plot(z.index, filled.rolling(14, center=True).mean()[z.index], color=PALETTE["series"][0],
           label="14-day centred mean")
    a.plot(z.index, filled.rolling(14, center=True).median()[z.index], color=PALETTE["series"][2],
           label="14-day centred median")
    a.plot(z.index, filled.ewm(span=14, adjust=False).mean()[z.index], color=PALETTE["series"][1],
           linestyle="--", label="EWMA, span 14 (trailing)")
    a.set_ylim(0, 120000)
    a.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{x/1000:.0f}k"))
    a.set_title("One spike, three answers: the median ignores Black Friday,\nthe mean and EWMA smear it",
                loc="left", fontsize=10)
    a.set_ylabel("Sessions per day (sum)")
    loc = mdates.AutoDateLocator(minticks=3, maxticks=5)
    a.xaxis.set_major_locator(mdates.DayLocator(interval=8))
    a.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    a.set_xlabel("Date (Nov-Dec 2024)")
    a.legend(fontsize=7.5, loc="upper right")

    seg = filled["2025-01-01":]
    b.plot(seg.index, seg.values, color=PALETTE["muted"], alpha=0.5, linewidth=0.9,
           label="Raw daily sessions")
    b.plot(seg.index, seg.rolling(31, center=True).mean(), color=PALETTE["series"][0],
           label="31-day centred mean")
    b.plot(seg.index, seg.rolling(31).mean(), color=PALETTE["series"][1], linestyle="--",
           label="31-day trailing mean")
    b.axvline(lg["centred_turn"], color=PALETTE["series"][0], linewidth=1, alpha=0.7)
    b.axvline(lg["trailing_turn"], color=PALETTE["series"][1], linewidth=1, alpha=0.7)
    b.set_ylim(0, None)
    b.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{x/1000:.0f}k"))
    b.set_title(f"Trailing mean finds the spring trough {lg['lag_periods']} days late\n"
                f"(half-window = {lg['half_window']})", loc="left", fontsize=10)
    b.set_ylabel("Sessions per day (sum)")
    b.xaxis.set_major_locator(loc)
    b.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
    b.legend(fontsize=7.5, loc="upper left")

    g = P["grid"]
    cmap = ListedColormap([PALETTE["highlight"], PALETTE["series"][0]])
    c.imshow((g > 0).astype(int), cmap=cmap, aspect="auto", vmin=0, vmax=1)
    c.grid(False)
    for i in range(g.shape[0]):
        for j in range(g.shape[1]):
            c.text(j, i, "▲" if g[i, j] > 0 else "▼", ha="center", va="center",
                   color="white", fontsize=9)
    c.set_xticks(range(len(P["wins"])), [f"{w} d" for w in P["wins"]])
    c.set_yticks(range(len(P["starts"])), [f"{s:%b %Y}" for s in P["starts"]])
    for s in c.spines.values():
        s.set_visible(False)
    c.tick_params(length=0)
    c.set_xlabel("Window length (days from the 1st of the start month)")
    c.set_ylabel("Start month")
    r = R["sweep"]
    c.set_title(f"Same series, 60 windows: {r['rising']} rising (blue ▲),\n{r['falling']} falling "
                f"(orange ▼). The window is a claim", loc="left", fontsize=10)
    fig.suptitle("Part B - what the window, the smoother and the alignment decide",
                 x=0.05, y=0.97, ha="left", fontsize=13, fontweight="bold")
    save_fig(fig, HERE / "partB_windows.png",
             note="Source: sessions_hourly.csv - SYNTHETIC course data, CDB601220 Week 4. Daily series = sum of hourly "
                  "flow; 13 never-recorded days interpolated in the smoother panels only (not shown as data).")
    plt.close(fig)


if __name__ == "__main__":
    buf = io.StringIO()

    class Tee:
        def write(self, s):
            sys.__stdout__.write(s)
            buf.write(s)

        def flush(self):
            sys.__stdout__.flush()

    with redirect_stdout(Tee()):
        res = run()
    make_figure(res)
    (HERE / "partB_output.txt").write_text(buf.getvalue())
    import json
    res.pop("_plot")
    (HERE / "partB_numbers.json").write_text(json.dumps(res, indent=1, default=str))

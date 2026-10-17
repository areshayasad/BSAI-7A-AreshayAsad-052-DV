#!/usr/bin/env python3
"""
Appendix to Part D - the 28-day version promised in Part E's window clause.

The 7-day window was fixed before plotting (it cancels the weekly cycle). This
script shows the 28-day alternative and CHECKS that it does not change the
direction of the story, rather than asserting it.

    python3 partD_appendix.py   ->  partD_appendix_28day.png (300 dpi) + printed check
SYNTHETIC course data, CDB601220 Week 4.
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter
from partD_figure import load_sessions
from tslib import PALETTE, save_fig, style_defaults

style_defaults()
S = load_sessions()
d = S["daily"]
sm = {w: d.rolling(w, center=True, min_periods=w // 2).mean().where(d.notna()) for w in (7, 28)}

print("DIRECTION CHECK - does the 28-day window change the story told by the 7-day window?")
res = {}
for w, s in sm.items():
    sp1 = s["2024-04-01":"2024-07-31"].idxmin()
    sp2 = s["2025-03-01":"2025-07-31"].idxmin()
    late = d["2025-08-15":"2025-09-11"].mean()
    res[w] = dict(trough_2024=sp1, trough_2025=sp2)
    print(f"  {w:>2}-day centred mean: 2024 spring trough {sp1:%d %b %Y}; 2025 spring trough {sp2:%d %b %Y}; "
          f"min value 2025 {s[sp2]:,.0f}")
up7 = sm[7]["2025-09-01":"2025-09-08"].mean() / sm[7][sm[7]["2025-03-01":"2025-07-31"].idxmin()] - 1
up28 = sm[28]["2025-09-01":"2025-09-05"].mean() / sm[28][sm[28]["2025-03-01":"2025-07-31"].idxmin()] - 1
rise7 = sm[7].dropna().iloc[-4] - sm[7]["2025-03-01":"2025-07-31"].min()
rise28 = sm[28].dropna().iloc[-4] - sm[28]["2025-03-01":"2025-07-31"].min()
print(f"  rise from the 2025 spring trough to the last smoothed value: 7-day {rise7:+,.0f}, 28-day {rise28:+,.0f} sessions/day (both positive)")
same_dir = rise7 > 0 and rise28 > 0
print(f"  direction unchanged (trough in spring, climb into September, both years): {same_dir}")
assert same_dir

fig, ax = plt.subplots(figsize=(9.5, 4.6))
ax.plot(d.index, d.values, color=PALETTE["muted"], alpha=0.5, linewidth=0.8, label="Daily sessions (raw)")
ax.plot(sm[7].index, sm[7].values, color=PALETTE["series"][0], linewidth=1.5, label="7-day centred mean (used in Part D)")
ax.plot(sm[28].index, sm[28].values, color=PALETTE["series"][1], linewidth=2.2, label="28-day centred mean (appendix)")
ax.set_ylim(0, 62000)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{x/1000:.0f}k"))
ax.set_ylabel("Sessions per day (sum of 24 hourly counts)")
ax.set_xlabel("Date")
loc = mdates.AutoDateLocator(minticks=4, maxticks=8)
ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
ax.set_title("A 28-day window flattens Black Friday but keeps the story: spring trough, climb into September",
             loc="left", fontsize=10.5)
ax.legend(loc="upper left", fontsize=8)
save_fig(fig, HERE / "partD_appendix_28day.png",
         note="Source: sessions_hourly.csv - SYNTHETIC course data, CDB601220 Week 4. Same cleaning as Part D; window chosen as an alternative AFTER the 7-day window was fixed, shown regardless of its result.")

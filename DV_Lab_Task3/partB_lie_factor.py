"""
Part B - Lie Factor audit, computed with vizlib.lie_factor().

    python3 partB_lie_factor.py

Reads data/case07_lie_factor.csv (five graphics, measured ink) and
data/case07_dual_axis_series.csv (chart F). Data are synthetic, generated for
CDB601220.
"""
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from vizlib import lie_factor, lie_verdict   # noqa: E402

pd.set_option("display.width", 200)
d = pd.read_csv(os.path.join(ROOT, "data", "case07_lie_factor.csv"))

# ------------------------------------------------------------------ Q1
rows = []
for _, r in d.iterrows():
    lf, de, ge = lie_factor(r.value_start, r.value_end, r.ink_start, r.ink_end, int(r.ink_dimension))
    # what you would (wrongly) get if you forgot ink_dimension
    lf1, _, ge1 = lie_factor(r.value_start, r.value_end, r.ink_start, r.ink_end, 1)
    rows.append(dict(chart=r.chart_id, subject=r.subject, dim=int(r.ink_dimension),
                     data_effect=de, graphic_effect=ge, lie_factor=lf, verdict=lie_verdict(lf),
                     LF_if_dim_left_at_1=lf1))
t = pd.DataFrame(rows)

print("PART B - Q1: the audit table\n")
show = t.copy()
show["data_effect"] = show.data_effect.map("{:+.1%}".format)
show["graphic_effect"] = show.graphic_effect.map("{:+.1%}".format)
show["lie_factor"] = show.lie_factor.map("{:.2f}".format)
show["LF_if_dim_left_at_1"] = show.LF_if_dim_left_at_1.map("{:.2f}".format)
print(show.to_string(index=False))

honest = t[t.verdict == "honest"].chart.tolist()
print(f"\nQ2: the honest one is chart {honest}.")
print("    A  bars start at a 29.6 baseline, so only the tips show: a 6.7% rise is drawn as a 500% rise.")
print("    B  a coin icon scaled 1.5x in height AND width: the ink is the area, which grew 2.25x.")
print("    D  bars 8 -> 9 cm for a 100 -> 150 rise: the ink barely moves, the rise is squeezed.")
print("    E  bubble RADIUS set proportional to value: radius x4 means AREA x16.")

print("\nQ3: ink_dimension = 2 for", t[t.dim == 2].chart.tolist())
print("    Leave it at 1 and you measure the side or radius, not the ink the eye reads as size;")
print("    B and E would both print LF = 1.00 and be passed as honest when they are 2.5x and 5x.")

under = t[t.lie_factor < 0.95]
print(f"\nQ4: understated chart(s): {under.chart.tolist()}  (LF = {under.lie_factor.iloc[0]:.2f})")
print("    Subject: air-pollution index, up 50%, drawn as up 12.5%. The file does not say WHY the ink")
print("    barely moves (a compressed or offset scale would do it), only that it does. It is still a")
print("    distortion: a reader sees a calm change where the data show a 50% rise, and has no way to")
print("    know. Who benefits is an inference, not something the data say: whoever would rather the")
print("    pollution rise looked small - an agency or an industry, depending on who published it.")

# ------------------------------------------------------------------ Q5
f = pd.read_csv(os.path.join(ROOT, "data", "case07_dual_axis_series.csv"))
print("\nQ5: chart F (the dual-axis chart from Part A, case 7)")
# ink = height of the point above the bottom of ITS OWN axis, as a fraction of that axis
rev_ink = (f.revenue_pkr_m - 50) / (80 - 50)
cost_ink = (f.cost_pkr_m - 40) / (56 - 40)
lf_rev, de_rev, ge_rev = lie_factor(f.revenue_pkr_m.iloc[0], f.revenue_pkr_m.iloc[-1], rev_ink.iloc[0], rev_ink.iloc[-1])
lf_cost, de_cost, ge_cost = lie_factor(f.cost_pkr_m.iloc[0], f.cost_pkr_m.iloc[-1], cost_ink.iloc[0], cost_ink.iloc[-1])
print(f"    revenue line: data {de_rev:+.1%}, ink {ge_rev:+.0%}, LF {lf_rev:.1f}")
print(f"    cost line:    data {de_cost:+.1%}, ink {ge_cost:+.0%}, LF {lf_cost:.1f}")
print("    One chart, two Lie Factors (26.0 and 11.0), because each line has its own axis. The formula")
print("    assumes ONE rule turning data into ink. With twin axes there are two rules, so there is no")
print("    single LF for the chart. And the claim ('cost was higher until May') is about the GAP between")
print("    the lines, which depends only on the two limits the analyst picked. I cannot compute an honest")
print("    number for that, and the reason is the point: the picture is not measuring anything shared.")
profit = (f.revenue_pkr_m - f.cost_pkr_m).tolist()
print(f"    Data: revenue above cost in all 6 months; surplus {profit} PKR m. Never a loss.")

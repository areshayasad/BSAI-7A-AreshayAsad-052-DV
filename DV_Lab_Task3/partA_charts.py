"""
Part A - rebuild the nine published charts from their recipes, then plot the
honest version of each.

    python3 partA_charts.py

Writes figs/caseNN_rebuild.png and figs/caseNN_redesign.png, and prints every
number the diagnosis relies on. Data: synthetic, generated for CDB601220.

Rule check: every figure starts with fig, ax = plt.subplots(). No plt.plot().
The ONLY dual-axis chart in this file is the case 7 rebuild, because the recipe
asks for exactly that - it is the thing being taken apart. Its redesign has none.
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scipy.signal import find_peaks

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from vizlib import MARKERS, PALETTE, save_fig, style_defaults   # noqa: E402

style_defaults()
C = PALETTE["series"]            # blue, vermilion, green
INK, SOFT, MUTED = PALETTE["ink"], PALETTE["ink_soft"], PALETTE["muted"]
FIGS = os.path.join(ROOT, "figs")
os.makedirs(FIGS, exist_ok=True)
SYN = "Synthetic data generated for CDB601220."
NUMBERS: dict[str, dict] = {}


def D(name):
    return pd.read_csv(os.path.join(ROOT, "data", name))


def out(fig, name, note):
    save_fig(fig, os.path.join(FIGS, name), note)
    plt.close(fig)


# =============================================================== 1  helmets
def case1():
    d = D("case01_helmet_rickshaw.csv")
    g = d.groupby("helmet_grade")[["head_injuries", "trips"]].sum()
    rate = (g.head_injuries / g.trips * 1000)[["Standard", "Premium"]]
    assert round(rate["Standard"], 2) == 2.15 and round(rate["Premium"], 2) == 5.40

    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    ax.bar(rate.index, rate.values, color=[C[0], C[1]], width=0.55)
    for i, v in enumerate(rate.values):
        ax.text(i, v + 0.12, f"{v:.2f}", ha="center", fontweight="bold")
    ax.set_ylim(0, 6.5)
    ax.set_ylabel("Head injuries per 1,000 trips")
    ax.set_title("\u201cPremium helmets have 2.5x the head-injury rate\u201d")
    out(fig, "case01_rebuild.png", f"n = 1,000 riders, 100,000 trips. y-axis from zero. {SYN}")

    # ---- the diagnosis numbers
    sp = d.groupby("helmet_grade")[["avg_speed_kph", "months_experience"]].mean()
    ct = pd.crosstab(d.road_type, d.helmet_grade)
    r = d.groupby(["road_type", "helmet_grade"])[["head_injuries", "trips"]].sum()
    r["rate"] = r.head_injuries / r.trips * 1000
    NUMBERS["c1"] = dict(speed=sp.avg_speed_kph.round(1).to_dict(),
                         exp=sp.months_experience.round(1).to_dict(),
                         share_motorway=(ct.loc["Motorway"] / ct.sum()).round(3).to_dict(),
                         strata=r.rate.round(2).to_dict())

    order = ["Inner-city lanes", "City arterial", "Motorway"]
    speed = d.groupby("road_type").avg_speed_kph.mean()
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    w = 0.36
    for k, (grade, col) in enumerate([("Standard", C[0]), ("Premium", C[1])]):
        for i, rt in enumerate(order):
            row = r.loc[(rt, grade)]
            x = i + (k - 0.5) * w
            ax.bar(x, row.rate, w * 0.94, color=col)
            ax.text(x, row.rate + 0.15, f"{row.rate:.1f}", ha="center", fontweight="bold", fontsize=9)
            ax.text(x, row.rate + 0.62, f"{int(row.head_injuries)} / {int(row.trips):,}", ha="center",
                    fontsize=6.5, color=SOFT)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{rt}\n(riders average {speed[rt]:.0f} km/h)" for rt in order])
    ax.set_ylim(0, 9.3)
    ax.set_ylabel("Head injuries per 1,000 trips")
    ax.text(-0.42, 8.9, "Standard", color=C[0], fontweight="bold")
    ax.text(0.0, 8.9, "Premium", color=C[1], fontweight="bold")
    ax.set_title("On every road type, Premium riders are injured less \u2013 they just ride faster roads")
    out(fig, "case01_redesign.png",
        "Grey labels: injuries / trips in each cell (Inner-city Premium rests on 1 injury). "
        f"n = 1,000 riders. {SYN}")


# =============================================================== 2  chai
def case2():
    d = D("case02_chai_quizzes.csv")
    x, y = d.cups_doodh_patti_sold, d.quiz_failures
    r = x.corr(y)
    assert round(r, 2) == 0.98
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    ax.scatter(x, y, color=C[0], s=28)
    m, b = np.polyfit(x, y, 1)
    xs = np.array([x.min(), x.max()])
    ax.plot(xs, m * xs + b, color=C[1])
    ax.text(0.04, 0.92, f"Pearson r = {r:.2f}", transform=ax.transAxes, fontweight="bold")
    ax.set_xlabel("Cups of doodh patti sold per month")
    ax.set_ylabel("Quiz failures per month")
    ax.set_title("\u201cChai sales predict quiz failures\u201d")
    out(fig, "case02_rebuild.png", f"n = 24 months. {SYN}")

    d["cups_pc"] = d.cups_doodh_patti_sold / d.students_enrolled
    d["fail_pc"] = d.quiz_failures / d.students_enrolled * 100
    pc = d.cups_pc.corr(d.fail_pc)
    NUMBERS["c2"] = dict(r_raw=round(r, 3),
                         r_cups_enrol=round(d.cups_doodh_patti_sold.corr(d.students_enrolled), 3),
                         r_fail_enrol=round(d.quiz_failures.corr(d.students_enrolled), 3),
                         r_cups_exam=round(d.cups_doodh_patti_sold.corr(d.is_exam_month), 3),
                         r_within_exam=round(d[d.is_exam_month == 1].cups_doodh_patti_sold.corr(d[d.is_exam_month == 1].quiz_failures), 3),
                         r_within_nonexam=round(d[d.is_exam_month == 0].cups_doodh_patti_sold.corr(d[d.is_exam_month == 0].quiz_failures), 3),
                         r_per_student=round(pc, 3),
                         r_pc_nonexam=round(d[d.is_exam_month == 0].cups_pc.corr(d[d.is_exam_month == 0].fail_pc), 3),
                         r_pc_exam=round(d[d.is_exam_month == 1].cups_pc.corr(d[d.is_exam_month == 1].fail_pc), 3),
                         fail_pc_exam=round(d[d.is_exam_month == 1].fail_pc.mean(), 2),
                         fail_pc_nonexam=round(d[d.is_exam_month == 0].fail_pc.mean(), 2),
                         growth_enrol=round(d.students_enrolled.iloc[-1] / d.students_enrolled.iloc[0], 2))

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    a = ax[0]
    idx = d.copy()
    for col, lab, c, mk in [("students_enrolled", "Students enrolled", C[2], "^"),
                            ("cups_doodh_patti_sold", "Cups sold", C[1], "s"),
                            ("quiz_failures", "Quiz failures", C[0], "o")]:
        v = idx[col] / idx[col].iloc[0] * 100
        a.plot(range(24), v, color=c, marker=mk, markevery=3, label=lab)
        a.text(23.3, v.iloc[-1] + {"Students enrolled": -14, "Cups sold": 14, "Quiz failures": 0}[lab], lab,
               color=c, va="center", fontsize=8, fontweight="bold")
    a.set_xticks(range(0, 24, 3))
    a.set_xticklabels(d.month.iloc[::3], rotation=0, fontsize=7)
    a.set_xlim(-0.5, 29)
    a.set_ylabel("Index (Sep 2024 = 100)")
    a.set_title("Enrolment, chai and failures all grow together")
    b = ax[1]
    for ex, mk, lab in [(0, "o", "regular month"), (1, "s", "exam month")]:
        s = d[d.is_exam_month == ex]
        b.scatter(s.cups_pc, s.fail_pc, marker=mk, color=C[0] if ex == 0 else C[1], s=34, label=lab)
    b.set_xlabel("Cups sold per enrolled student")
    b.set_ylabel("Quiz failures per 100 students")
    b.set_title(f"Per student the link mostly vanishes (r = {pc:.2f})")
    b.legend(loc="upper left")
    fig.tight_layout()
    out(fig, "case02_redesign.png", f"n = 24 months. Rates divide by students_enrolled. {SYN}")


# =============================================================== 3  AQI
def case3():
    d = D("case03_aqi_monitors.csv")
    d["day"] = (pd.to_datetime(d.date) - pd.to_datetime(d.date).min()).dt.days + 1
    daily = d.groupby("day").aqi.mean()
    before, after = daily.loc[:60].mean(), daily.loc[61:].mean()
    # the recipe says "mean of the daily means" for each horizontal line
    assert round(before) == 202 and round(after) == 137
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(daily.index, daily.values, color=C[0], lw=1.6)
    ax.axvline(61, color=INK, ls="--", lw=1)
    ax.hlines(before, 1, 60, color=C[1], lw=2)
    ax.hlines(after, 61, 120, color=C[1], lw=2)
    ax.text(30, before + 9, f"{before:.0f}", ha="center", color=C[1], fontweight="bold")
    ax.text(90, after + 9, f"{after:.0f}", ha="center", color=C[1], fontweight="bold")
    ax.text(61.8, 8, "Smog Action Plan, day 61", fontsize=8)
    ax.set_ylim(0, 260)
    ax.set_xlabel("Day (1 = 1 Jan 2026)")
    ax.set_ylabel("Mean AQI across stations")
    ax.set_title(f"\u201cThe Smog Action Plan cut AQI by a third\u201d ({(after / before - 1) * 100:.0f}%)")
    out(fig, "case03_rebuild.png", f"y-axis from zero. Mean over whichever stations reported. {SYN}")

    rep = d.dropna(subset=["aqi"])
    full = d.groupby("station_id").aqi.count()
    keep = full[full == 120].index
    kd = d[d.station_id.isin(keep)].groupby("day").aqi.mean()
    off = d[d.aqi.isna()]
    NUMBERS["c3"] = dict(before=round(before, 1), after=round(after, 1),
                         stations_before=int(rep[rep.day <= 60].station_id.nunique()),
                         stations_after=int(rep[rep.day > 60].station_id.nunique()),
                         offline_zones=off.groupby("zone").station_id.nunique().to_dict(),
                         industrial_mean=round(rep[rep.zone == "Industrial"].aqi.mean(), 1),
                         const_n=len(keep), const_before=round(kd.loc[:60].mean(), 1),
                         const_after=round(kd.loc[61:].mean(), 1),
                         first_offline_day=int(off.day.min()),
                         zone_means=rep.groupby("zone").aqi.mean().round(1).to_dict())

    zc = {"Industrial": C[1], "Arterial": C[0], "Residential": C[2], "Peri-urban": MUTED}
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    a = ax[0]
    for z, col in zc.items():
        s = d[d.zone == z].groupby("day").aqi.mean()
        a.plot(s.index, s.values, color=col, lw=1.5)
        a.text(121, s.dropna().iloc[-1], z, color=col, va="center", fontsize=8, fontweight="bold")
    a.axvline(61, color=INK, ls="--", lw=1)
    a.set_xlim(0, 135)
    a.set_ylim(0, 380)
    a.set_xlabel("Day")
    a.set_ylabel("Mean AQI of reporting stations")
    a.set_title("Industrial stations (AQI \u2248 322) go dark on day 61")
    b = ax[1]
    b.plot(daily.index, daily.values, color=MUTED, lw=1.4)
    b.plot(kd.index, kd.values, color=C[0], lw=1.8)
    b.axvline(61, color=INK, ls="--", lw=1)
    b.text(3, 232, "All reporting stations", color=SOFT, fontsize=8, fontweight="bold")
    b.text(3, 110, f"The {len(keep)} stations that report every day", color=C[0], fontsize=8, fontweight="bold")
    b.set_ylim(0, 260)
    b.set_xlabel("Day")
    b.set_ylabel("Mean AQI")
    b.set_title(f"Same stations: {kd.loc[:60].mean():.0f} before, {kd.loc[61:].mean():.0f} after")
    fig.tight_layout()
    out(fig, "case03_redesign.png", f"22 stations x 120 days; 540 station-days blank. y-axes from zero. {SYN}")


# =============================================================== 4 and 5 tables
def stat_table(df, key, x, y):
    cols = {}
    for k, g in df.groupby(key, sort=False):
        s = stats.linregress(g[x], g[y])
        cols[k] = {"n": len(g), "mean x": g[x].mean(), "mean y": g[y].mean(),
                   "SD x": g[x].std(ddof=0), "SD y": g[y].std(ddof=0),
                   "Pearson r": g[x].corr(g[y]), "slope": s.slope}
    return pd.DataFrame(cols)


def table_fig(tab, title, note, figsize):
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    cells = [[f"{v:.0f}" if i == 0 else f"{v:.2f}" if i < 5 else f"{v:.3f}" for i, v in enumerate(tab[c])]
             for c in tab.columns]
    cells = list(map(list, zip(*cells)))
    t = ax.table(cellText=cells, rowLabels=list(tab.index), colLabels=[c.replace(" ", "\n", 1) if len(c) > 14 else c for c in tab.columns],
                 loc="center", cellLoc="center")
    t.auto_set_font_size(False)
    t.set_fontsize(9)
    t.scale(1, 1.6)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor(PALETTE["grid"])
        if r == 0:
            cell.set_text_props(fontweight="bold")
    ax.set_title(title)
    return fig


def case4():
    d = D("case04_quartet_depts.csv")
    t = stat_table(d, "department", "study_hours_per_week", "final_score_out_of_20")
    print("\nCase 4 table\n", t.round(3).to_string())
    assert (t.loc["mean x"].round(2) == 18.00).all() and (t.loc["mean y"].round(2) == 14.50).all()
    assert (t.loc["Pearson r"].round(2).between(0.81, 0.82)).all()
    fig = table_fig(t, "\u201cFour departments behave identically, so fund them equally\u201d",
                    "", (9.5, 3.4))
    out(fig, "case04_rebuild.png", f"11 students per department, n = 44. {SYN}")

    a = d[d.department == "Architecture"]
    ee = d[d.department == "Electrical Engineering"]
    ee2 = ee.drop(ee.final_score_out_of_20.idxmax())
    bu = d[d.department == "Business Administration"]
    cq = np.polyfit(bu.study_hours_per_week, bu.final_score_out_of_20, 2)
    r2q = 1 - ((bu.final_score_out_of_20 - np.polyval(cq, bu.study_hours_per_week)) ** 2).sum() / \
        ((bu.final_score_out_of_20 - bu.final_score_out_of_20.mean()) ** 2).sum()
    NUMBERS["c4"] = dict(arch_hours=sorted(a.study_hours_per_week.unique().tolist()),
                         arch_sd_without=float(a[a.study_hours_per_week < 30].study_hours_per_week.std()),
                         ee_r_without=round(ee2.study_hours_per_week.corr(ee2.final_score_out_of_20), 4),
                         ee_slope_without=round(stats.linregress(ee2.study_hours_per_week, ee2.final_score_out_of_20).slope, 3),
                         bus_r2_linear=round(bu.study_hours_per_week.corr(bu.final_score_out_of_20) ** 2, 3),
                         bus_r2_quadratic=round(r2q, 4),
                         cohort_is_department=bool((d.groupby("department").cohort_group.nunique() == 1).all()))
    fig, ax = plt.subplots(2, 2, figsize=(9.6, 7.2), sharex=True, sharey=True)
    notes = {"Computer Science": "Roughly linear with scatter: the only one the line describes",
             "Business Administration": "A clean curve; scores peak near 22 h, then fall",
             "Electrical Engineering": "A perfect line plus one outlier tilting the fit",
             "Architecture": "Ten students at 16 h, one at 38 h: one point makes r"}
    for p, (k, g) in zip(ax.flat, d.groupby("department", sort=False)):
        s = stats.linregress(g.study_hours_per_week, g.final_score_out_of_20)
        xs = np.array([6, 40])
        p.plot(xs, s.intercept + s.slope * xs, color=MUTED, lw=1.5)
        p.scatter(g.study_hours_per_week, g.final_score_out_of_20, color=C[0], s=36, zorder=3)
        p.set_title(k, fontsize=10)
        p.text(0.03, 0.04, notes[k], transform=p.transAxes, fontsize=7.5, color=SOFT)
        p.set_xlim(6, 40)
        p.set_ylim(9, 21)
    for p in ax[1]:
        p.set_xlabel("Study hours per week")
    for p in ax[:, 0]:
        p.set_ylabel("Final score (out of 20)")
    fig.suptitle("Same mean, SD, r and slope \u2013 four different stories", x=0.01, ha="left",
                 fontweight="bold", fontsize=12)
    fig.tight_layout()
    out(fig, "case04_redesign.png", f"Grey line = least-squares fit (identical in all four). n = 11 each. {SYN}")


def case5():
    d = D("case05_same_stats_shapes.csv")
    t = stat_table(d, "shape_name", "hours_on_platform", "assessment_score")
    print("\nCase 5 table\n", t.round(3).to_string())
    assert (t.loc["mean x"].round(2) == 48).all() and (t.loc["Pearson r"].round(3) == 0.42).all()
    fig = table_fig(t, "\u201cFive cohorts, one set of statistics\u201d", "", (10.5, 3.4))
    out(fig, "case05_rebuild.png", f"180 students per cohort, n = 900. {SYN}")
    NUMBERS["c5"] = dict(identical_to_2dp=True)

    fig, ax = plt.subplots(2, 3, figsize=(11, 6.6), sharex=True, sharey=True)
    for p, (k, g) in zip(ax.flat, d.groupby("shape_name", sort=False)):
        p.scatter(g.hours_on_platform, g.assessment_score, s=9, color=C[0], alpha=0.65)
        m, b = np.polyfit(g.hours_on_platform, g.assessment_score, 1)
        xs = np.array([g.hours_on_platform.min(), g.hours_on_platform.max()])
        p.plot(xs, m * xs + b, color=C[1], lw=1.5)
        p.set_title(k, fontsize=10)
    last = ax.flat[-1]
    last.axis("off")
    last.text(0.0, 0.62, "Every panel:\nmean 48.0 / 63.0\nSD 12.0 / 15.0\nr = 0.420\nsame line (orange)",
              fontsize=10, va="center", color=INK)
    for p in ax[1, :2]:
        p.set_xlabel("Hours on platform")
    for p in ax[:, 0]:
        p.set_ylabel("Assessment score")
    fig.suptitle("Five shapes, one set of summary numbers \u2013 plot before you trust a mean", x=0.01,
                 ha="left", fontweight="bold", fontsize=12)
    fig.tight_layout()
    out(fig, "case05_redesign.png", f"n = 180 per cohort, 900 in all. {SYN}")


# =============================================================== 6 heatmap
def case6():
    d = D("case06_sensor_matrix.csv")
    num = d.drop(columns=["age_band", "study_site", "hr_device_model"]).select_dtypes("number")
    assert num.shape[1] == 20
    cm = num.corr()
    assert round(cm.loc["creatinine", "hba1c"], 2) == 0.77 and round(cm.loc["systolic", "map_mmhg"], 2) == 0.96
    fig, ax = plt.subplots(figsize=(10, 8.6))
    sns.heatmap(cm, annot=True, fmt=".2f", cmap="Reds", annot_kws={"size": 5.5}, ax=ax, linewidths=0.3)
    ax.set_title("\u201cCreatinine tracks HbA1c \u2013 a finding\u201d", fontsize=12)
    ax.grid(False)
    out(fig, "case06_rebuild.png", f"n = 180 participants, 190 pairs. cmap=Reds, vmin/vmax left at default. {SYN}")

    r, p = stats.pearsonr(d.hba1c, d.creatinine)
    rho = stats.spearmanr(d.hba1c, d.creatinine)[0]
    rest = d.drop(d.creatinine.idxmax())
    iu = np.triu_indices(20, 1)
    c = cm.values[iu]
    n = len(num)
    pv = 2 * stats.t.sf(abs(c * np.sqrt((n - 2) / (1 - c ** 2))), n - 2)
    NUMBERS["c6"] = dict(r_all=round(r, 3), spearman_all=round(rho, 3),
                         r_without=round(rest.hba1c.corr(rest.creatinine), 3),
                         spearman_without=round(stats.spearmanr(rest.hba1c, rest.creatinine)[0], 3),
                         outlier=d.loc[d.creatinine.idxmax(), ["hba1c", "creatinine"]].tolist(),
                         creat_median=round(d.creatinine.median(), 1), hba1c_median=round(d.hba1c.median(), 2),
                         min_r=round(c.min(), 3), n_p05=int((pv < .05).sum()), expected=round(0.05 * len(pv), 1),
                         site_r=d.groupby("study_site").apply(lambda g: g.hba1c.corr(g.creatinine)).round(2).to_dict(),
                         outlier_site=d.loc[d.creatinine.idxmax(), "study_site"])

    fig, ax = plt.subplots(1, 3, figsize=(18, 6.4), gridspec_kw={"width_ratios": [1.5, 1, 1]})
    mask = np.triu(np.ones_like(cm, dtype=bool), k=1)
    lab = np.where(abs(cm.values) >= 0.5, np.vectorize(lambda v: f"{v:.2f}")(cm.values), "")
    sns.heatmap(cm, mask=mask, cmap="RdBu_r", vmin=-1, vmax=1, center=0, annot=lab, fmt="", annot_kws={"size": 7},
                ax=ax[0], linewidths=0.3, cbar_kws={"label": "Pearson r", "shrink": 0.8})
    ax[0].set_title("Drawn properly it still says 0.77", fontsize=11)
    ax[0].grid(False)
    ax[0].tick_params(labelsize=7.5)
    a = ax[1]
    out_i = d.creatinine.idxmax()
    a.scatter(rest.hba1c, rest.creatinine, color=C[0], s=14, alpha=0.7)
    a.scatter(d.hba1c[out_i], d.creatinine[out_i], color=C[1], s=60, marker="D", zorder=3)
    a.annotate("one participant\nHbA1c 15.8, creatinine 1,050", (d.hba1c[out_i], d.creatinine[out_i]),
               xytext=(7.2, 780), fontsize=8, color=C[1], arrowprops=dict(arrowstyle="-", color=C[1]))
    m, b = np.polyfit(d.hba1c, d.creatinine, 1)
    xs = np.array([4, 16])
    a.plot(xs, m * xs + b, color=MUTED, lw=1.3)
    a.set_xlabel("HbA1c (%)")
    a.set_ylabel("Creatinine (\u00b5mol/L)")
    a.set_title(f"All 180: r = {r:.2f}", fontsize=11)
    z = ax[2]
    z.scatter(rest.hba1c, rest.creatinine, color=C[0], s=14, alpha=0.7)
    z.set_xlabel("HbA1c (%)")
    z.set_ylabel("Creatinine (\u00b5mol/L)")
    z.set_title(f"Without that one row (n = 179): r = {rest.hba1c.corr(rest.creatinine):.3f}", fontsize=11)
    fig.tight_layout()
    out(fig, "case06_redesign.png",
        "Heatmap: diverging RdBu_r pinned to -1..+1, upper triangle masked, |r| >= 0.5 annotated (declared). "
        f"n = 180. {SYN}")


# =============================================================== 7 dual axis
def case7():
    d = D("case07_dual_axis_series.csv")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(d.month, d.revenue_pkr_m, color=C[0], marker="o")
    ax.set_ylim(50, 80)
    ax.set_ylabel("Revenue (PKR m)", color=C[0])
    ax2 = ax.twinx()                      # the thing being dismantled
    ax2.plot(d.month, d.cost_pkr_m, color=C[1], marker="s")
    ax2.set_ylim(40, 56)
    ax2.set_ylabel("Cost (PKR m)", color=C[1])
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax.set_title("\u201cShaheenGo ran at a loss until May\u201d")
    # self-check: where do the two LINES sit on screen?
    rev_pos = (d.revenue_pkr_m - 50) / 30
    cost_pos = (d.cost_pkr_m - 40) / 16
    above = (cost_pos > rev_pos).tolist()
    assert above[:4] == [True] * 4 and not any(above[4:])
    out(fig, "case07_rebuild.png", f"Two y-axes with hand-picked limits (50-80 and 40-56). n = 6 months. {SYN}")

    d["profit"] = d.revenue_pkr_m - d.cost_pkr_m
    NUMBERS["c7"] = dict(profit=d.profit.tolist(), rev_growth=round(d.revenue_pkr_m.iloc[-1] / d.revenue_pkr_m.iloc[0] - 1, 3),
                         cost_growth=round(d.cost_pkr_m.iloc[-1] / d.cost_pkr_m.iloc[0] - 1, 3),
                         months_cost_looks_higher=int(sum(above)))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    a = ax[0]
    a.plot(d.month, d.revenue_pkr_m, color=C[0], marker="o")
    a.plot(d.month, d.cost_pkr_m, color=C[1], marker="s")
    a.fill_between(range(6), d.cost_pkr_m, d.revenue_pkr_m, color=C[0], alpha=0.12)
    a.text(5.1, d.revenue_pkr_m.iloc[-1], "Revenue", color=C[0], fontweight="bold", va="center")
    a.text(5.1, d.cost_pkr_m.iloc[-1], "Cost", color=C[1], fontweight="bold", va="center")
    a.set_xlim(-0.3, 6.1)
    a.set_ylim(0, 90)
    a.set_ylabel("PKR millions (one shared axis)")
    a.set_title("Revenue was above cost in every month")
    b = ax[1]
    b.bar(d.month, d.profit, color=C[2], width=0.6)
    for i, v in enumerate(d.profit):
        b.text(i, v + 0.5, f"{v}", ha="center", fontweight="bold")
    b.set_ylim(0, 30)
    b.set_ylabel("Revenue minus cost (PKR m)")
    b.set_title("Monthly surplus tripled, 8 to 25")
    fig.tight_layout()
    out(fig, "case07_redesign.png", f"Both series are PKR millions, so they share one axis. n = 6 months. {SYN}")


# =============================================================== 8 bins
def case8():
    d = D("vitals_10k.csv")
    s = d.systolic
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.9))
    for p, b in zip(ax, [3, 45, 400]):
        h, e = np.histogram(s, bins=b)
        assert h.sum() == 10000
        p.bar(e[:-1], h, width=np.diff(e), align="edge", color=C[0])
        p.set_title(f"bins = {b}", fontsize=10)
        p.set_xlabel("Systolic (mmHg)")
        p.text(0.97, 0.93, f"n = {h.sum():,}", transform=p.transAxes, ha="right", fontsize=8, color=SOFT)
    ax[0].set_ylabel("Patients")
    fig.suptitle("\u201cThree bin widths, three different distributions\u201d", x=0.01, ha="left",
                 fontweight="bold", fontsize=12)
    fig.tight_layout()
    out(fig, "case08_rebuild.png", f"Same 10,000 raw systolic values in every panel. {SYN}")

    # integer-aligned bin widths: on whole-number data a width like 2.38 aliases
    # (some bins hold 2 integers, some 3) and invents a comb of fake peaks
    nb = {}
    for w in [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 40, 60]:
        h, _ = np.histogram(s, bins=np.arange(90, 200 + w + 1, w))
        nb[w] = len(find_peaks(h, prominence=0.05 * h.max())[0])
    h400, _ = np.histogram(s, bins=400)
    iqr = np.subtract(*np.percentile(s, [75, 25]))
    NUMBERS["c8"] = dict(distinct=int(s.nunique()), empty_400=int((h400 == 0).sum()),
                         width3=round((s.max() - s.min()) / 3, 1), width45=round((s.max() - s.min()) / 45, 2),
                         width400=round((s.max() - s.min()) / 400, 3), fd=round(2 * iqr / len(s) ** (1 / 3), 2),
                         peaks=nb, mode_lo=int(s[s < 140].mode()[0]), mode_hi=int(s[s >= 140].mode()[0]))

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4), gridspec_kw={"width_ratios": [1.5, 1]})
    a = ax[0]
    edges = np.arange(90, 204, 4)
    h, e = np.histogram(s, bins=edges)
    a.bar(e[:-1], h, width=4, align="edge", color=C[0], edgecolor="white", lw=0.5)
    a.set_xlabel("Systolic blood pressure (mmHg)")
    a.set_ylabel("Patients")
    a.text(0.98, 0.93, "bin width = 4 mmHg\n(Freedman-Diaconis \u2248 3.8, rounded to whole mmHg)\nn = 10,000",
           transform=a.transAxes, ha="right", va="top", fontsize=8, color=SOFT)
    a.set_title("Two populations: modes near 120 and 160 mmHg")
    b = ax[1]
    ks = list(nb)
    b.plot(ks, [nb[k] for k in ks], color=C[0], marker="o")
    b.axhline(2, color=MUTED, lw=1, ls=":")
    b.set_xscale("log")
    b.set_xticks([1, 2, 4, 10, 20, 60])
    b.set_xticklabels(["1", "2", "4", "10", "20", "60"])
    b.set_ylim(-0.3, 7)
    b.set_xlabel("Bin width (mmHg, log scale)")
    b.set_ylabel("Peaks found")
    b.set_title("Two peaks for every width from 2 to 20 mmHg", fontsize=10)
    fig.tight_layout()
    out(fig, "case08_redesign.png", "Peaks: scipy.signal.find_peaks, prominence 5% of tallest bin; bins aligned to whole mmHg. n = 10,000. " + SYN)


# =============================================================== 9 KDE
def case9():
    d = D("vitals_10k.csv")
    s = d.spo2.values.astype(float)
    assert s.max() == 100
    k = stats.gaussian_kde(s)             # Scott's rule = seaborn/scipy default
    xs = np.linspace(75, 108, 3000)
    y = k(xs)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(xs, y, color=C[0])
    ax.fill_between(xs, y, where=xs > 100, color=C[1], alpha=0.6)
    ax.axvline(100, color=INK, ls="--", lw=1)
    ax.text(100.3, y.max() * 0.7, "100 % = physical ceiling", fontsize=8, color=INK)
    ax.set_xlim(75, 108)
    ax.set_xlabel("SpO\u2082 (%)")
    ax.set_ylabel("Density")
    ax.set_title("\u201c4.4% of the density sits above 100% saturation\u201d")
    out(fig, "case09_rebuild.png", "Gaussian KDE, default bandwidth (Scott). Data maximum = 100. n = 10,000. " + SYN)

    above = k.integrate_box_1d(100, np.inf)
    NUMBERS["c9"] = dict(max=int(s.max()), kde_above_100=round(above, 4), kde_above_99_5=round(k.integrate_box_1d(99.5, np.inf), 4),
                         bw_sd=round(k.factor * s.std(ddof=1), 2), n100=int((s == 100).sum()),
                         pct100=round((s == 100).mean() * 100, 1), n_above=int((s > 100).sum()))
    vc = pd.Series(s).astype(int).value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    cols = [C[1] if v == 100 else C[0] for v in vc.index]
    ax.bar(vc.index, vc.values, color=cols, width=0.85)
    ax.text(100, vc.loc[100] + 60, f"{vc.loc[100]} patients\n({(s == 100).mean() * 100:.1f}%)", ha="center", fontsize=8,
            color=C[1], fontweight="bold")
    ax.set_xlim(79.5, 103)
    ax.set_xticks(range(80, 101, 2))
    ax.set_xlabel("SpO\u2082 (%), whole-number readings")
    ax.set_ylabel("Patients")
    ax.set_title("No reading exceeds 100 %; the data pile up against the ceiling")
    out(fig, "case09_redesign.png", "One bar per recorded integer value, so nothing can be smoothed past 100. n = 10,000. " + SYN)


def main():
    for f in (case1, case2, case3, case4, case5, case6, case7, case8, case9):
        f()
    print("\nNUMBERS used in the diagnosis")
    for k, v in NUMBERS.items():
        print(k, v)


if __name__ == "__main__":
    main()

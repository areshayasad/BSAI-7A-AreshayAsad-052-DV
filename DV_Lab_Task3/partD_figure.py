"""
Part D - the clinical review figure.

    python3 partD_figure.py

Writes partD_figure.png (cleaned, 300 dpi) and partD_figure_appendix.png (the
same figure with the heart-rate / BMI / length-of-stay exclusions switched off,
as the ethics clause in Part E asks), and prints the cleaning log that Part E
quotes. Data: synthetic, generated for CDB601220. Needs only pandas, numpy,
matplotlib, seaborn.

Design rule that governs every cleaning step below: an exclusion rule must be
one I would also apply if it made my conclusion weaker. Each rule is set by
physiology or by an impossible value, never by what the figure looks like.
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

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from vizlib import PALETTE, save_fig, style_defaults   # noqa: E402

style_defaults()
C = PALETTE["series"]
SOFT, MUTED = PALETTE["ink_soft"], PALETTE["muted"]

LOG: dict[str, str] = {}
COUNTS: dict[str, int] = {}

WARD_MAP = {"general medicine": "General Medicine", "gen medicine": "General Medicine",
            "cardiology": "Cardiology", "cardio": "Cardiology",
            "day surgery": "Day Surgery", "day-surgery": "Day Surgery",
            "intensive care": "ICU", "icu": "ICU", "i.c.u": "ICU"}

HR_LO, HR_HI = 30, 250        # bpm; outside this is a sensor fault, not a patient
LOS_MAX = 100                 # days; the data jump from 24 to 140, nothing between
BIN_W = 4                     # mmHg, panel 1 (Freedman-Diaconis gives 3.8)
HEAT_COLS = ["age", "systolic", "diastolic", "heart_rate", "spo2", "bmi",
             "chol_mmol_l", "glucose_mmol_l", "los_days"]     # map_mmhg deliberately absent


# --------------------------------------------------------------------------- 0
def inspect(df):
    """Run once to read the problems; kept here so the audit is reproducible."""
    df.info()
    print(df.describe().T)
    print(df.ward.value_counts())
    print(df.admit_date.head(20).tolist())


# --------------------------------------------------------------------------- 1
def clean(raw: pd.DataFrame, apply_exclusions: bool = True) -> pd.DataFrame:
    df = raw.copy()
    log = LOG if apply_exclusions else {}
    log["rows loaded"] = f"{len(df):,}"

    # 1. ward: twelve spellings, four wards. Conform before any groupby.
    df["ward_clean"] = df.ward.str.strip().str.lower().map(WARD_MAP)
    assert df.ward_clean.isna().sum() == 0 and df.ward_clean.nunique() == 4
    log["ward spellings conformed"] = f"{df.ward.nunique()} spellings -> 4 wards, 0 rows dropped"

    # 2. dates: three source formats. The slash dates are day-first: the first field
    #    reaches 31 and the second never exceeds 4, and the result spans exactly
    #    1 Jan - 30 Apr 2026.
    iso = pd.to_datetime(df.admit_date, format="%Y-%m-%d", errors="coerce")
    dmy = pd.to_datetime(df.admit_date, format="%d/%m/%Y", errors="coerce")
    mon = pd.to_datetime(df.admit_date, format="%d-%b-%Y", errors="coerce")
    df["admit_dt"] = iso.fillna(dmy).fillna(mon)
    assert df.admit_dt.isna().sum() == 0
    log["dates parsed"] = (f"3 formats (ISO, DD/MM/YYYY, DD-Mon-YYYY), 0 unparsed, "
                           f"{df.admit_dt.min():%d %b} to {df.admit_dt.max():%d %b %Y}")

    # 3. bmi sentinels: 0 and 999 mean "not recorded". Set to NaN, keep the row.
    sent = df.bmi.isin([0, 999])
    COUNTS["bmi"] = int(sent.sum())
    before = df.bmi.mean()
    if apply_exclusions:
        df.loc[sent, "bmi"] = np.nan
    log["bmi sentinels (0 and 999) -> NaN"] = (
        f"n = {int(sent.sum())} (0: {int((raw.bmi == 0).sum())}, 999: {int((raw.bmi == 999).sum())}); "
        f"mean {before:.2f} -> {df.bmi.mean():.2f}")

    # 4. heart rate: below 30 or above 250 bpm is a device fault. The reading is
    #    blanked, the patient's other vitals are kept.
    bad_hr = (df.heart_rate < HR_LO) | (df.heart_rate > HR_HI)
    COUNTS["hr"] = int(bad_hr.sum())
    hr_before = df.heart_rate.mean()
    if apply_exclusions:
        df.loc[bad_hr, "heart_rate"] = np.nan
    log["heart-rate faults (<30 or >250 bpm) -> NaN"] = (
        f"n = {int(bad_hr.sum())} ({int((raw.heart_rate == 0).sum())} readings of 0, "
        f"{int((raw.heart_rate > HR_HI).sum())} readings of {raw.heart_rate[raw.heart_rate > HR_HI].min()}-"
        f"{raw.heart_rate.max()}); mean {hr_before:.2f} -> {df.heart_rate.mean():.2f} bpm")

    # 5. length of stay: 18 values of 140-274 days sit after a clean gap from 24.
    #    No ward admits for that long and Day Surgery is same-day by definition.
    far = df.los_days > LOS_MAX
    COUNTS["los"] = int(far.sum())
    los_before = df.los_days.mean()
    if apply_exclusions:
        df.loc[far, "los_days"] = np.nan
    log[f"length of stay > {LOS_MAX} days -> NaN"] = (
        f"n = {int(far.sum())} (smallest {raw.los_days[far].min():.0f}, largest {raw.los_days.max():.0f}; "
        f"next-highest value is {raw.los_days[~far].max():.0f}); mean {los_before:.2f} -> {df.los_days.mean():.2f} days")

    # 6. map_mmhg = (systolic + 2*diastolic)/3, so its correlation with them is arithmetic.
    chk = ((df.systolic + 2 * df.diastolic) / 3 - df.map_mmhg).abs().max()
    log["derived column kept out of the heatmap"] = f"map_mmhg (max |formula - column| = {chk:.2f} mmHg)"
    log["risk_score not averaged"] = "it is a ratio (events/day); not aggregated by ward, so no mean-of-ratios is shown"
    return df


# --------------------------------------------------------------------------- 2
def build_figure(df: pd.DataFrame, cleaned: bool = True):
    fig, ax = plt.subplots(2, 2, figsize=(12.6, 8.8))
    n = len(df)

    # ---------------- panel 1: systolic BP is two populations, not one
    a = ax[0, 0]
    s = df.systolic
    edges = np.arange(88, 204, BIN_W)
    h, e = np.histogram(s, bins=edges)
    a.bar(e[:-1], h, width=BIN_W, align="edge", color=C[0], edgecolor="white", linewidth=0.5)
    lo, hi = (s < 140), (s >= 140)
    a.text(121, h.max() * 1.02, f"{lo.mean():.0%} near 120", color=C[0], ha="center", fontsize=9, fontweight="bold")
    a.text(162, h[(e[:-1] >= 150)].max() * 1.12, f"{hi.mean():.0%} near 160", color=C[0], ha="center", fontsize=9,
           fontweight="bold")
    a.set_ylim(0, h.max() * 1.15)
    a.set_xlabel("Systolic blood pressure (mmHg)")
    a.set_ylabel("Patients")
    a.text(0.98, 0.58, f"bin width = {BIN_W} mmHg\nsplit at 140 mmHg\nn = {n:,}", transform=a.transAxes,
           ha="right", va="top", fontsize=8, color=SOFT)
    a.set_title("Systolic pressure is two groups, centred near 120 and 160 mmHg")

    # ---------------- panel 2: length of stay by ward (median order, log axis)
    b = ax[0, 1]
    los = df.dropna(subset=["los_days"])
    los = los[los.los_days > 0]                      # zero cannot sit on a log axis
    order = los.groupby("ward_clean").los_days.median().sort_values().index.tolist()
    med = los.groupby("ward_clean").los_days.median()
    pal = {w: (C[1] if w == "ICU" else C[0]) for w in order}
    sns.boxplot(data=los, x="ward_clean", y="los_days", order=order, hue="ward_clean", palette=pal,
                legend=False, ax=b, width=0.55, flierprops=dict(marker="o", markersize=2.5, alpha=0.35,
                                                                 markerfacecolor=MUTED, markeredgecolor="none"),
                linewidth=1.2)
    b.set_yscale("log")
    b.set_yticks([0.1, 1, 10, 100])
    b.set_yticklabels(["0.1", "1", "10", "100"])
    b.set_xlabel("")
    b.set_ylabel("Length of stay (days, log scale)")
    for i, w in enumerate(order):
        b.text(i, 0.0045, f"median {med[w]:.2f}", ha="center", fontsize=8, color=SOFT)
    b.set_ylim(0.003, 300 if not cleaned else 60)
    ratio = med["ICU"] / med["Day Surgery"]
    b.set_title(f"ICU stays are about {ratio:.0f}x as long as day surgery")

    # ---------------- panel 3: the one pair worth plotting
    c = ax[1, 0]
    pr = df.dropna(subset=["age", "chol_mmol_l"])
    c.scatter(pr.age, pr.chol_mmol_l, s=5, alpha=0.18, color=C[0], edgecolors="none")
    m, k = np.polyfit(pr.age, pr.chol_mmol_l, 1)
    xs = np.array([pr.age.min(), pr.age.max()])
    c.plot(xs, m * xs + k, color=C[1], lw=2)
    rho = pr.age.corr(pr.chol_mmol_l, method="spearman")
    c.text(0.03, 0.95, f"Spearman \u03c1 = {rho:.2f}\nslope {m * 10:+.2f} mmol/L per decade\nn = {len(pr):,}",
           transform=c.transAxes, va="top", fontsize=9, fontweight="bold")
    c.set_xlabel("Age (years)")
    c.set_ylabel("Total cholesterol (mmol/L)")
    c.set_title(f"Cholesterol rises about {m * 10:.1f} mmol/L per decade of age")

    # ---------------- panel 4: the screen that picked panel 3
    d = ax[1, 1]
    cm = df[HEAT_COLS].corr(method="spearman")
    mask = np.triu(np.ones_like(cm, dtype=bool), k=1)
    sns.heatmap(cm, mask=mask, cmap=PALETTE["diverging"], vmin=-1, vmax=1, center=0, annot=True, fmt=".2f",
                annot_kws={"size": 7.5}, linewidths=0.4, ax=d, cbar_kws={"label": "Spearman \u03c1", "shrink": 0.8})
    d.grid(False)
    d.tick_params(labelsize=8)
    d.set_title("Blood-pressure pair aside, only age and cholesterol move together")

    for p in ax.flat:
        for sp in ("top", "right"):
            p.spines[sp].set_visible(False)
    fig.suptitle("10,000 admissions: two blood-pressure groups, ICU stays far longer than day surgery, "
                 "and cholesterol that climbs with age" if cleaned else
                 "APPENDIX \u2013 same figure with the heart-rate, BMI and length-of-stay exclusions switched OFF",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    return fig


# --------------------------------------------------------------------------- 3
def main():
    raw = pd.read_csv(os.path.join(ROOT, "data", "vitals_10k.csv"))
    # inspect(raw)       # read once, then leave commented
    df = clean(raw, apply_exclusions=True)
    fig = build_figure(df, cleaned=True)
    note = (f"n = {len(df):,} admissions, 1 Jan-30 Apr 2026. Blanked, not dropped: {COUNTS['hr']} heart-rate faults (<30 or >250 bpm), "
            f"{COUNTS['bmi']} BMI sentinels (0, 999), {COUNTS['los']} stays >100 days.\n"
            f"map_mmhg excluded (derived). Systolic bin width {BIN_W} mmHg; log-scale LOS (2 zero-day stays cannot be drawn there); "
            "Spearman correlations. Synthetic data generated for CDB601220.")
    save_fig(fig, os.path.join(ROOT, "partD_figure.png"), note)     # save BEFORE any show
    plt.close(fig)
    print("wrote partD_figure.png")

    # appendix: the same figure without the exclusions (the ethics clause)
    LOG_BAK = dict(LOG)
    df2 = clean(raw, apply_exclusions=False)
    fig2 = build_figure(df2, cleaned=False)
    save_fig(fig2, os.path.join(ROOT, "partD_figure_appendix.png"),
             "Ward spellings and dates conformed; NO value exclusions. Synthetic data, CDB601220.")
    plt.close(fig2)
    print("wrote partD_figure_appendix.png")

    print("\nCleaning log (Part E item 3):\n")
    for k, v in LOG_BAK.items():
        print(f"  {k:<48} {v}")
    los = df.dropna(subset=["los_days"])
    print("\nWard medians (days):", los.groupby("ward_clean").los_days.median().round(2).to_dict())
    pr = df[["age", "chol_mmol_l"]].dropna()
    print("age-cholesterol: Spearman", round(pr.age.corr(pr.chol_mmol_l, method='spearman'), 3),
          "Pearson", round(pr.age.corr(pr.chol_mmol_l), 3))
    print("systolic split at 140:", round((df.systolic < 140).mean(), 3), round((df.systolic >= 140).mean(), 3))


if __name__ == "__main__":
    main()

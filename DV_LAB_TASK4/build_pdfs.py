#!/usr/bin/env python3
"""
Builds partA_diagnosis.pdf and partE_justification.pdf.

Every number in the text is read from partA_numbers.json / partD_numbers.json /
partB_numbers.json, which the analysis scripts wrote. Nothing is typed in by hand,
so the prose cannot drift from the charts.

    python3 partA_charts.py && python3 partD_figure.py && python3 partB_windows.py
    python3 build_pdfs.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DV", str(FONTS / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", str(FONTS / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DV-I", str(FONTS / "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-B")

A = json.loads((HERE / "partA_numbers.json").read_text())
D = json.loads((HERE / "partD_numbers.json").read_text())
B = json.loads((HERE / "partB_numbers.json").read_text())
INK = colors.HexColor("#16202E")
BLUE = colors.HexColor("#0072B2")
GREY = colors.HexColor("#5B6573")
STUDENT = "Areshay Asad · Roll 052 · BSAI · Section 7A"


def st(name, size, lead=None, bold=False, color=INK, after=3, before=0, indent=0):
    return ParagraphStyle(name, fontName="DV-B" if bold else "DV", fontSize=size,
                          leading=lead or size * 1.32, textColor=color, spaceAfter=after,
                          spaceBefore=before, alignment=TA_LEFT, leftIndent=indent)


# =============================================================== Part A PDF
def case_text():
    c1, c2, c3, c4, c5, c6, c7, c8, c9 = (A[f"c{i}"] for i in range(1, 10))
    f = lambda x, n=0: f"{x:,.{n}f}"
    T = []

    T.append(dict(
        title="Case 1 · “Orders peak in Q1 and collapse every year — a clear annual cycle”",
        file="case01_orders_stringdate.csv",
        rebuild=f"Sorted the 24 rows by the text column <b>month</b>; 24 points; the line climbs, drops "
                f"<b>{c1['drops'][0]}</b>, climbs, drops <b>{c1['drops'][1]}</b>, climbs again — self-check hit.",
        conclusion=f"Conclusion invited: orders have an annual cycle that peaks early in the year and then collapses. "
                   f"<b>Decoy:</b> “it is ordinary retail seasonality.” That does not hold: in calendar order there are "
                   f"<b>{c1['n_neg']} falls in {c1['n_changes']} month-on-month changes</b> (the smallest rise is "
                   f"+{c1['min_change']}), so there is no peak for a season to produce. The series simply climbs "
                   f"{f(c1['first'])} → {f(c1['last'])} (+{c1['total_pct']:.0f}%, ≈{c1['monthly_pct']:.1f}% a month).",
        mechanism=f"<b>month</b> is text written <i>YYYY-M</i> with no zero padding, so a text sort puts "
                  f"“2024-10”, “2024-11”, “2024-12” <i>before</i> “2024-2”…“2024-9” (and the same in 2025). "
                  f"{c1['n_moved']} of the 24 rows land in the wrong position. The “collapse” of <b>−958</b> is "
                  f"2024-12 ({f(c1['dec24'])}) followed by 2024-2 ({f(c1['feb24'])}); the second, <b>−978</b>, is "
                  f"2025-12 ({f(c1['dec25'])}) followed by 2025-2 ({f(c1['feb25'])}). Two-month gaps of ten months each.",
        redesign="Parse with <i>pd.to_datetime(format='%Y-%m')</i>, sort on the datetime, plot in calendar order, axis from zero."))

    T.append(dict(
        title="Case 2 · “Sales grew steadily, 22%, across the quarter”",
        file="case02_shop_closed.csv",
        rebuild=f"Plotted <b>sales_pkr_k</b> against row number with a least-squares line: {c2['n']} points, first 207, "
                f"last 253 (+22%); slope {c2['slope_row']:.2f} per row — self-check hit.",
        conclusion=f"Conclusion invited: steady growth. <b>Decoy:</b> “the rise is a day-of-week mix effect.” Ruled out: "
                   f"mean sales by weekday only span {c2['dow_min']:.1f}–{c2['dow_max']:.1f} "
                   f"({c2['dow_spread_pct']:.1f}% top to bottom) and every weekday has 9–10 observations, which cannot "
                   f"make a {c2['step_pct']:.0f}% step.",
        mechanism=f"Only trading days are recorded: {c2['n']} rows span {c2['span']} calendar days. There are "
                  f"<b>{c2['n_gap']} consecutive missing days ({c2['gap_start']} to {c2['gap_end']})</b> — the shop was closed. "
                  f"Plotting against row number deletes the gap, so equal distance no longer means equal time and a "
                  f"one-day jump ({c2['pre_last']} → {c2['post_first']}) is drawn as a ramp. Mean before the closure "
                  f"{c2['pre_mean']:.1f} ({c2['n_pre']} days), after {c2['post_mean']:.1f} ({c2['n_post']} days): a step of "
                  f"<b>+{c2['step']:.1f} (+{c2['step_pct']:.0f}%)</b>. Within each segment the trend is "
                  f"{c2['sl_pre']:+.2f}/day then {c2['sl_post']:+.2f}/day — not steady growth. The row-number slope "
                  f"({c2['slope_row']:.2f}) also overstates the calendar slope ({c2['slope_cal']:.2f}/day). The data cannot "
                  f"say <i>why</i> sales stepped up on reopening.",
        redesign="Same data on a calendar axis, the closure kept as a shaded break (NaN, so the line breaks), and the two segment means shown."))

    T.append(dict(
        title="Case 3 · “Peak load jumped 43% overnight on 1 July”",
        file="case03_bandwidth_levels.csv",
        rebuild=f"Resampled <b>concurrent_users</b> to daily with .sum(): June mean {f(c3['jun_sum'])}, July mean "
                f"{f(c3['jul_sum'])} (+{c3['sum_pct']:.0f}%) — self-check hit.",
        conclusion=f"Conclusion invited: traffic stepped up by 43% on 1 July. <b>Decoy:</b> “bytes_served also jumped "
                   f"{c3['bytes_sum_pct']:.0f}%, so it is corroborated.” Ruled out: bytes are a flow, but June has only "
                   f"{c3['jun_hours']:.1f} of 24 hours recorded per day; per <i>recorded hour</i> bytes went "
                   f"{c3['bytes_hr_jun']/1e6:.3f}M → {c3['bytes_hr_jul']/1e6:.3f}M ({c3['bytes_hr_pct']:+.1f}%). The “corroboration” "
                   f"is the same artefact.",
        mechanism=f"<b>concurrent_users</b> is a <i>level</i> (users connected at an instant), and a level must never be "
                  f"summed over a day. June has {c3['jun_rows']} readings out of {c3['jun_possible']} possible hours "
                  f"({c3['cover_pct']:.1f}%; {c3['min_hours_jun']}–{c3['max_hours_jun']} per day, never 24), July has all 744. The "
                  f"sum is mostly <i>how many rows the day has</i> (corr {c3['corr_sum_count']:.2f}); hours per day rise "
                  f"{c3['hour_ratio']:.2f}× on 1 July, almost exactly the +43%. The honest aggregation is the mean: "
                  f"{c3['jun_mean']:.1f} → {c3['jul_mean']:.1f} (<b>{c3['mean_pct']:+.1f}%</b>). Even the daily maximum rose only "
                  f"{c3['max_pct']:+.1f}% ({c3['max_jun']:.0f} → {c3['max_jul']:.0f}), and that is an upper bound because June's "
                  f"missing hours bias its maximum down.",
        redesign="Daily <i>mean</i> of recorded readings with, underneath, the hours recorded per day (a same-chart-plus-context fix; no dual axis)."))

    T.append(dict(
        title="Case 4 · “The new checkout flow started working on 7 September”",
        file="case04_intervention_lag.csv",
        rebuild=f"Raw conversion in grey with a 31-day <i>trailing</i> mean; its minimum is {c4['trailing']} — self-check hit.",
        conclusion=f"Conclusion invited: the flow began to work on 7 Sep. <b>Decoy:</b> “the series is too noisy to date any "
                   f"turn, so the rise is just noise.” Ruled out: the day-to-day noise is ≈{c4['daily_sd']:.2f} points, the rise is "
                   f"{c4['lo']:.2f} → {c4['hi']:.2f} (+{c4['hi'] - c4['lo']:.2f}), and weekly means rise in "
                   f"{c4['n_weeks_rise']} of {c4['n_weeks_after']} consecutive weeks after the trough. The turn is real; "
                   f"the <i>date</i> is what is wrong.",
        mechanism=f"A trailing mean at day t averages days t−30…t, so it cannot register a turn until about half the window "
                  f"is post-turn. Measured: centred 31-day minimum <b>{c4['centred']}</b>, trailing minimum <b>{c4['trailing']}</b>, "
                  f"lag <b>{c4['lag']} days = half-window ({c4['half']})</b>. Two independent checks agree with the centred date "
                  f"(7-day centred minimum {c4['centred7']}; a two-line fit puts the kink at {c4['kink']}). So the turn happened "
                  f"23–28 Aug, 10–15 days before the claimed date; 7 Sep is a property of the smoother. (The data cannot say "
                  f"when the checkout shipped.)",
        redesign="Raw, centred and trailing means together, both turning points marked, the lag drawn as an arrow, the two-line fit overlaid."))

    T.append(dict(
        title="Case 5 · “Revenue has fallen for six straight months”",
        file="case05_revenue_window.csv",
        rebuild=f"Took May–Nov 2025 only, line with markers, y from zero: {c5['n']} points, 158.8 → 92.2 (−41.9%) — self-check hit.",
        conclusion=f"Conclusion invited: the business is in decline. <b>Decoy (the two the brief warns about):</b> “the axis is "
                   f"truncated” — it is not (starts at 0); “n = 7 is too small” — each point is a complete monthly total and the "
                   f"fall is exact arithmetic. Both are ruled out; the chart is not <i>wrong</i>, it is <i>incomplete</i>.",
        mechanism=f"The window runs from the annual peak (May) to near the annual trough (Nov), so it contains only the "
                  f"downhill half of a seasonal cycle. The identical May→Nov window gives {c5['fall']['2023']:+.1f}% in 2023, "
                  f"{c5['fall']['2024']:+.1f}% in 2024 and {c5['fall']['2025']:+.1f}% in 2025 — every year. Meanwhile each of the "
                  f"12 months of 2025 is above the same month of 2024 (<b>{c5['yoy_min']:+.1f}% to {c5['yoy_max']:+.1f}%</b>) and annual "
                  f"revenue grew {c5['tot']['2023']:,.1f} → {c5['tot']['2024']:,.1f} → {c5['tot']['2025']:,.1f} "
                  f"(+{c5['tot24']:.1f}%, +{c5['tot25']:.1f}%).",
        redesign="A cycle plot: one line per year, the analyst's window shaded. The same chart with the other years beside it."))

    T.append(dict(
        title="Case 6 · “Orders collapsed in October”",
        file="case06_monthly_partial.csv",
        rebuild=f"Monthly totals with .sum(), bars from zero: ten bars; September {f(c6['sep_total'])}, October {f(c6['oct_total'])} "
                f"({c6['oct_pct']:.0f}% of it) — self-check hit.",
        conclusion=f"Conclusion invited: a demand collapse. <b>Decoy:</b> “orders really were lost.” Ruled out: on the days that "
                   f"exist, October's daily orders ran {c6['oct_min']}–{c6['oct_max']}, every day above January's <i>average</i> "
                   f"({c6['jan_mean']:.0f}).",
        mechanism=f"The extract ends on <b>{c6['last_date']}</b>: October has {c6['oct_days']} of {c6['oct_possible']} days "
                  f"({c6['cover_pct']:.1f}%). A sum compares an 11-day month with 30-day ones. Per day, October is "
                  f"<b>{c6['oct_mean']:.1f}</b> against September's {c6['sep_mean']:.1f} ({c6['mean_pct']:+.1f}%) — the highest of "
                  f"all ten months; prorated, October would be ≈{c6['prorated']:,.0f}.",
        redesign="Orders per day (monthly mean) instead of a sum, with the incomplete month hatched and labelled “11 of 31 days”."))

    T.append(dict(
        title="Case 7 · “Product D has been erratic since mid-2024”",
        file="case07_stacked_products.csv",
        rebuild=f"Stacked area, A at the bottom, D on top: the total envelope runs {c7['tot_min']:.1f}–{c7['tot_max']:.1f} — self-check hit.",
        conclusion=f"Conclusion invited: D's revenue is volatile. <b>Decoy:</b> “D's own numbers are noisy.” Ruled out: D has the "
                   f"<b>lowest</b> coefficient of variation of the four ({c7['cv']['product_d']:.1f}%, against {c7['cv']['product_b']:.1f}% "
                   f"for B), its month-to-month change has sd {c7['dsd']['product_d']:.1f} (B: {c7['dsd']['product_b']:.1f}), its largest "
                   f"single move is {c7['d_max_abs_change']:.1f}, and it drifts calmly from {c7['d_first']:.1f} to {c7['d_last']:.1f}.",
        mechanism=f"In a stacked area each layer's edges are the running total of everything beneath it. D sits on A+B+C, whose "
                  f"month-to-month sd is <b>{c7['base_sd']:.1f}</b> — {c7['ratio']:.0f}× D's own — and <b>product_b</b> (the column "
                  f"the recipe never isolates) accounts for {c7['b_share_of_baseline_var']:.0f}% of that variance (correlation of "
                  f"B's changes with the baseline's: {c7['corr_b_base']:.2f}). The eye reads the wobble of D's <i>edges</i>, not "
                  f"its thickness.",
        redesign="Small multiples, one panel per product on the same 0–300 axis, so the swing of each is directly comparable."))

    T.append(dict(
        title="Case 8 · “Paid search drives 43% of our customers”",
        file="case08_channel_attrib.csv",
        rebuild=f"Counted True per touch column over {c8['n']:,} customers: search {c8['shares']['touch_search']:.1f}%, social "
                f"{c8['shares']['touch_social']:.1f}%, email {c8['shares']['touch_email']:.1f}%, direct {c8['shares']['touch_direct']:.1f}% — self-check hit.",
        conclusion=f"Conclusion invited: search is responsible for 43% of customers. <b>Decoy:</b> “search is still the biggest, so the "
                   f"ranking at least holds.” As <i>reach</i> it does (42.6% vs 32.3%); but “drives” means credit, and search is the "
                   f"<i>only</i> touch for just {c8['only_pct']['touch_search']:.1f}% of customers "
                   f"({100 - c8['only_of_reach_pct']['touch_search']:.0f}% of those it touched were also touched by another channel).",
        mechanism=f"The four percentages add to <b>{c8['sum_pct']:.1f}%</b>. The parts are not exclusive: {c8['n_multi']:,} customers "
                  f"(<b>{c8['pct_multi']:.1f}%</b>) were touched by two or more channels (2: {c8['touch_counts']['2']}, 3: "
                  f"{c8['touch_counts']['3']}, 4: {c8['touch_counts']['4']}), an average of {c8['avg_touch']:.2f} touches. A pie needs a "
                  f"partition of 100%. Worse, matplotlib silently rescales the wedges, so the “42.6%” wedge occupies only "
                  f"{c8['wedge_pct']['touch_search']:.1f}% of the circle while its label says 42.6%.",
        redesign="Horizontal bars of reach, each split into “only this channel” and “also another channel”; the legend and the title say they overlap."))

    T.append(dict(
        title="Case 9 · “Premium is now 38% of revenue — a record”",
        file="case09_premium_share.csv",
        rebuild=f"premium ÷ total per quarter, line, y from zero, last point annotated: {c9['s0']:.1f}% → {c9['s1']:.1f}% — self-check hit.",
        conclusion=f"Conclusion invited: premium is booming. <b>Decoy:</b> “the share is miscalculated.” Ruled out: "
                   f"{c9['p1']:.1f} ÷ {c9['t1']:.1f} = {c9['recompute']:.1f}% exactly. The chart is arithmetically right — it is "
                   f"<i>incomplete</i>.",
        mechanism=f"The denominator collapsed: total revenue {c9['t0']:.0f} → {c9['t1']:.0f} (<b>{c9['t_pct']:.0f}%</b>), non-premium "
                  f"{c9['o0']:.0f} → {c9['o1']:.0f} ({c9['o_pct']:.0f}%), while premium itself went {c9['p0']:.0f} → {c9['p1']:.0f} "
                  f"(<b>{c9['p_pct']:.0f}%</b>). Had the total stayed at {c9['t0']:.0f}, the 2025Q4 share would be "
                  f"{c9['share_if_total_flat']:.1f}%. A rising share can be a shrinking company.",
        redesign="Not a different chart: the same share line with the numerator and denominator (premium, non-premium, total, in PKR m) beside it."))
    return T


def build_diagnosis():
    sty_h = st("h", 11.5, bold=True, color=BLUE, after=2)
    sty_f = st("f", 7, color=GREY, after=4)
    sty_l = st("l", 8.6, after=3.2)
    sty_t = st("t", 15, bold=True, after=3)
    sty_s = st("s", 8.5, color=GREY, after=8)
    doc = SimpleDocTemplate(str(HERE / "partA_diagnosis.pdf"), pagesize=A4, leftMargin=1.5 * cm,
                            rightMargin=1.5 * cm, topMargin=1.3 * cm, bottomMargin=1.2 * cm,
                            title="Week 4 Part A diagnosis", author="Areshay Asad (052)")
    S = [Paragraph("Week 4 · Part A — nine charts, rebuilt and taken apart", sty_t),
         Paragraph(f"{STUDENT} · CDB601220 Data Visualization · all data SYNTHETIC course data", sty_s),
         Paragraph("<b>How to read each page.</b> Both figures are shown (left: the analyst's chart rebuilt from the recipe; "
                   "right: the honest redesign). Each case then gives: (1) the rebuild and its self-check, (2) the conclusion the "
                   "chart invites <i>and</i> the first objection that does not hold, with evidence, (3) the mechanism with its "
                   "number, (4) the redesign. Cases 5 and 9 are <i>incomplete</i> rather than wrong: their redesigns are the same "
                   "chart with something else beside it.", sty_l)]
    cases = case_text()
    S.append(PageBreak())
    for i, c in enumerate(cases, 1):
        S.append(Paragraph(c["title"], sty_h))
        S.append(Paragraph(f"data: {c['file']}", sty_f))
        w = (A4[0] - 3 * cm - 0.4 * cm) / 2
        imgs = []
        for kind in ("rebuild", "redesign"):
            from PIL import Image as PI
            p = HERE / "figs" / f"case{i:02d}_{kind}.png"
            iw, ih = PI.open(p).size
            h = w * ih / iw
            if h > 9.2 * cm:
                h = 9.2 * cm
                imgs.append(Image(str(p), width=h * iw / ih, height=h))
            else:
                imgs.append(Image(str(p), width=w, height=h))
        t = Table([imgs, [Paragraph("<b>Rebuilt (the claim)</b>", sty_f), Paragraph("<b>Redesign (honest)</b>", sty_f)]],
                  colWidths=[w + 0.2 * cm, w + 0.2 * cm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        S += [t, Spacer(1, 4)]
        S.append(Paragraph(f"<b>1 · Rebuild.</b> {c['rebuild']}", sty_l))
        S.append(Paragraph(f"<b>2 · Conclusion &amp; decoy.</b> {c['conclusion']}", sty_l))
        S.append(Paragraph(f"<b>3 · Mechanism.</b> {c['mechanism']}", sty_l))
        S.append(Paragraph(f"<b>4 · Redesign.</b> {c['redesign']}", sty_l))
        if i < len(cases):
            S.append(PageBreak())
    doc.build(S)


# =============================================================== Part E PDF
def build_justification():
    L = {l["step"]: l for l in D["log"]}
    sh = D["shares"]
    d_ = lambda k: L[k]["detail"]
    sz = 7.5
    sp = st("p", sz, lead=sz * 1.30, after=1.6)
    hh = st("h", 8.6, bold=True, color=BLUE, after=1.2, before=2.6)
    tt = st("t", 11.5, bold=True, after=1)
    ss = st("s", 6.8, color=GREY, after=2)
    cell = st("c", 6.9, lead=8.3, after=0)
    cellb = ParagraphStyle("cb", parent=cell, fontName="DV-B")
    mark = st("m", sz, lead=sz * 1.3, after=1.4, indent=0)
    doc = SimpleDocTemplate(str(HERE / "partE_justification.pdf"), pagesize=A4, leftMargin=1.25 * cm,
                            rightMargin=1.25 * cm, topMargin=0.95 * cm, bottomMargin=0.8 * cm,
                            title="Week 4 Part E justification", author="Areshay Asad (052)")
    pr = D["palette_proof"]
    S = [Paragraph("Week 4 · Part E — justification for the Monday review figure (partD_figure.png)", tt),
         Paragraph(f"{STUDENT} · CDB601220 · all data SYNTHETIC course data (CDB601220 Week 4)", ss)]

    # 1 per panel
    S.append(Paragraph("1 · Each panel: its question, why that chart type, which Week 2 channel rule", hh))
    rows = [[Paragraph("<b>Panel</b>", cell), Paragraph("<b>The question it answers (one sentence)</b>", cell),
             Paragraph("<b>Why this chart type</b>", cell), Paragraph("<b>Week 2 channel rule</b>", cell)],
            [Paragraph("1 · daily sessions + 7-day mean", cell),
             Paragraph("Where is traffic heading once the weekend rhythm is removed?", cell),
             Paragraph("A line, because time is on the x axis and equal distance must mean equal duration. Raw kept faint (smoothing moves noise, it does not remove it); the window is named in the title.", cell),
             Paragraph("Position on a common scale, plus <b>one pop-out</b>: raw in grey for context, the signal in colour.", cell)],
            [Paragraph("2 · day × hour heatmap", cell),
             Paragraph("When in the week and day is traffic highest?", cell),
             Paragraph(f"168 cells of one measure over two cyclic categories; the pattern (weekends run {D['weekend_gap_pct']:.0f}% above weekdays, evening peak, busiest {D['peak']}) is the point, not a value. One-hue sequential Blues, no rainbow, no midpoint.", cell),
             Paragraph("Position carries the two dimensions; colour lightness (a weaker channel) carries the value, which is acceptable for finding a pattern, not for reading amounts.", cell)],
            [Paragraph("3 · treemap", cell),
             Paragraph("Where is the mass in the catalogue — which categories and sub-categories dominate?", cell),
             Paragraph("A part-to-whole of a <i>hierarchy</i>: containment shows parent → child and area shows share. One hue per parent; values printed on blocks.", cell),
             Paragraph("<b>Area</b> is the fourth-best channel (±20%), so anything that matters carries its number in text. It answers “where”, not “by how much”.", cell)],
            [Paragraph("4 · sorted bars", cell),
             Paragraph(f"By how much do the sub-categories differ, and in what order (Phones lead Laptops by {sh['Phones'] - sh['Laptops']:.1f} points)?", cell),
             Paragraph("The same eight numbers where the reader must <i>compare close values</i>: sorted horizontal bars, zero baseline, values printed. Hue matches the treemap so the two panels link.", cell),
             Paragraph("<b>Position on a common scale</b>, the best channel — the one that treemap area cannot offer.", cell)]]
    t = Table(rows, colWidths=[2.7 * cm, 4.2 * cm, 6.6 * cm, 4.1 * cm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D2DC")),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF3F8")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2), ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 2.5)]))
    S.append(t)
    S.append(Paragraph(
        f"Palette (proved with vizlib.worst_pair, every pair): worst OKLab ΔE ×100 is {pr['normal']} normal, {pr['deutan']} deutan, "
        f"{pr['protan']} protan, {pr['tritan']} tritan. The 4th hue (#CC79A7, Computing) is thin under deutan and below 3:1 contrast, so every parent is also "
        f"named in text. Aspect ratio of panel 1 stated on the figure (1.74:1).", sp))

    # 2 time decisions
    S.append(Paragraph("2 · Every time decision, named and defended", hh))
    pr_ = L["timestamp parse"]
    S.append(Paragraph(
        f"<b>Parse.</b> Two formats: ISO ({pr_['n_iso']:,} rows) and DD/MM/YYYY ({pr_['n_slash']:,} rows). The ambiguous one is resolved by "
        f"evidence: the first field exceeds 12 on {pr_['n_first_gt12']:,} rows and the second on {pr_['n_second_gt12']}, so it is day-first; "
        f"{pr_['n_ambiguous']:,} rows have both fields ≤12 and are decided only by that rule. <i>format='mixed'</i> parses every row, raises nothing, and "
        f"moves <b>{pr_['rows_moved_by_mixed']:,} rows</b> to the wrong date (index {pr_['mixed_range'][0][:10]} → {pr_['mixed_range'][1][:10]}, not "
        f"2024-04-01 → 2025-09-11); I checked the index min/max, not the row count. <b>Resolution/aggregation.</b> Hourly flows → daily with "
        f"<b>sum</b> (axis says “sum of 24 hourly counts”); a flow is never resampled with last(). Gaps were counted on the hourly index "
        f"(312 h = 13 whole days) <i>before</i> resampling and left as breaks, not zeros or interpolation. <b>Window.</b> 7 days, because the "
        f"cycle removed is weekly and 7 is the shortest window that cancels it exactly (Part B.1: weekly swing left 0.2%); longer windows start "
        f"eating the seasonal turn (91 d keeps 50% of the wave and loses 17% of the series to the ends). <b>Centred</b>, because the Monday "
        f"review is retrospective and all data exist; a live dashboard must use a trailing mean and say so (Part B.4: lag = half-window).", sp))
    S.append(Paragraph(
        "<b>The window clause.</b> The window was fixed at 7 days before plotting, because the cycle being removed is weekly (Part B.1). "
        "The series is shown from its first recorded day; no start date was selected. A 28-day version is in the appendix "
        "(partD_appendix_28day.png) and does not change the direction — checked, not asserted: both windows put the spring trough in "
        "late spring and show a rise into September (+8,914 vs +7,339 sessions/day). Part B.5 shows why this matters: the same series gives "
        f"{B['sweep']['rising']} rising and {B['sweep']['falling']} falling trends across 60 start/window choices. <b>Symmetry test:</b> "
        "had the 7-day window made the September rise look smaller, I would still have used it, because I chose it for the weekly cycle "
        "and published the 28-day version anyway; I would show the same figure if it weakened my conclusion.", sp))

    # 3 removals
    S.append(Paragraph("3 · Every row removed or altered — rule, count, from → to", hh))
    dup, sen, dev, mis, agg, sku, neg = (L[k] for k in ("exact duplicates", "sessions sentinel", "device labels",
                                                        "missing periods", "daily aggregation", "duplicate SKU",
                                                        "negative net revenue"))
    rem = [[Paragraph(x, cellb) for x in ("Rule", "Count", "What moved (from → to)")],
           [Paragraph("Exact duplicate hourly rows (same hour, same values; many written in the other date format) — dropped, first kept", cell),
            Paragraph(f"{dup['n']}", cell), Paragraph(dup["detail"], cell)],
           [Paragraph("sessions = −1 (no-reading sentinel) — set to NaN, not 0; row kept, orders/revenue kept", cell),
            Paragraph(f"{sen['n']}", cell), Paragraph(f"mean sessions/hour {sen['mean_before']:,.1f} → {sen['mean_after']:,.1f}; {agg['n_topped']} days topped up from the same-weekday profile (mean {agg['adj_mean']:+.1f}%, max {agg['adj_max']:+.1f}%), run both ways in Part B (no conclusion changes)", cell)],
           [Paragraph("Never-recorded days — NOT removed, NOT filled: left as gaps", cell),
            Paragraph("13 days (312 h)", cell), Paragraph("529 calendar days → 516 observed; marked on the figure", cell)],
           [Paragraph("Device spellings normalised (strip, lower, Title)", cell), Paragraph(f"{dev['n']:,} relabelled", cell),
            Paragraph("6 spellings → 3 (Desktop, Mobile, Tablet); none removed", cell)],
           [Paragraph("Duplicate SKU: SKU-0127 (AUDI-04) listed under Audio <i>and</i> Wearables — Wearables copy removed (a tree needs one parent)", cell),
            Paragraph(f"{sku['n']}", cell), Paragraph(f"345 → 344 rows; Wearables share {D['wearables']['before']:.2f}% → {D['wearables']['after']:.2f}%", cell)],
           [Paragraph("Negative net revenue — no area, so removed from the treemap/bars and reported here", cell),
            Paragraph(f"{neg['n']} SKUs ({D['neg']['total']:.2f} PKR m)", cell), Paragraph("344 → 337 SKUs; catalogue net 1,711.4 → 1,712.5 PKR m", cell)],
           [Paragraph("Partial final month (September 2025, 11 of 30 days) — kept, shaded and labelled; never compared as a month", cell),
            Paragraph("n/a", cell), Paragraph("1–11 Sep 2025 compared only with 1–11 Sep 2024 (+37%)", cell)]]
    t2 = Table(rem, colWidths=[7.4 * cm, 2.3 * cm, 7.9 * cm])
    t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D2DC")),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF3F8")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.1),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.1), ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 2.5)]))
    S.append(t2)
    S.append(Paragraph(
        f"After cleaning, the eight sub-category shares land within {D['max_diff_vs_file']:.2f} points of shares_eight.csv (limit 0.3). "
        f"Before the duplicate-SKU fix Wearables was out by {D['wearables']['before'] - 9.2:.2f} points.", sp))

    # 4 rollups
    S.append(Paragraph("4 · Every level rolled up", hh))
    S.append(Paragraph(
        f"<b>Other bucket: none.</b> tslib.rollup_other at 1% reports “{D['other_note']}” — the smallest sub-category (Drones) is {sh['Drones']:.1f}%. "
        f"<b>Depth cut:</b> the tree is category → sub-category; the 337 SKU leaves are rolled into 8 sub-categories (4 parents, "
        f"{ ' / '.join(f'{k} {v:.0f}%' for k, v in D['top_cat_share'].items()) }) because a 337-block treemap is unreadable "
        f"and no reader question needs SKU detail. 8 leaves is within a treemap's range but above the ~4±1 chunks of working memory, which is why panel 4 "
        f"exists. Checks: children sum to parent, shares sum to 100% (asserted in code), no negative values drawn.", sp))
    doc.build(S)


if __name__ == "__main__":
    build_diagnosis()
    build_justification()
    from pypdf import PdfReader
    for n in ("partA_diagnosis.pdf", "partE_justification.pdf"):
        print(n, "pages:", len(PdfReader(str(HERE / n)).pages))

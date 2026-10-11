"""
Builds partA_diagnosis.pdf (nine diagnoses, both figures per case) and
partE_justification.pdf (one page). Run partA_charts.py, partD_figure.py first.

    python3 build_pdfs.py

Every number in the text was computed by partA_charts.py / partD_figure.py.
All data are synthetic, generated for CDB601220.
"""
import os

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image as RLImage, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
_F = "/usr/share/fonts/truetype/dejavu/"
for _n, _f in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
               ("DV-BI", "DejaVuSans-BoldOblique.ttf")]:
    pdfmetrics.registerFont(TTFont(_n, _F + _f))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

ROOT = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(ROOT, "figs")
ss = getSampleStyleSheet()
INK = colors.HexColor("#16202E")
BLUE = colors.HexColor("#0072B2")
H = ParagraphStyle("H", parent=ss["Heading2"], fontName="DV-B", fontSize=13, textColor=INK, spaceAfter=2)
CLAIM = ParagraphStyle("C", parent=ss["Normal"], fontName="DV-I", fontSize=9.5, textColor=BLUE, spaceAfter=5)
B = ParagraphStyle("B", parent=ss["Normal"], fontName="DV", fontSize=8.1, leading=10.8, textColor=INK, spaceAfter=3,
                   alignment=TA_LEFT)
CAP = ParagraphStyle("CAP", parent=B, fontSize=7.5, textColor=colors.HexColor("#5B6573"), spaceAfter=2)


def fig(name, max_w, max_h):
    p = os.path.join(FIGS, name)
    w, h = Image.open(p).size
    s = min(max_w / w, max_h / h)
    return RLImage(p, width=w * s, height=h * s)


CASES = [
 ("1 \u00b7 Premium-certified helmets", "\u201cPremium-certified helmets have 2.5x the head-injury rate\u201d (5.40 vs 2.15 per 1,000 trips)",
  "Premium helmets are worse, perhaps even harmful; riders should stay on Standard.",
  "Premium riders are simply less experienced. Not so: mean experience is 31.4 months for Premium and 31.5 for Standard.",
  "<b>Simpson\u2019s paradox, with road type as the hidden variable.</b> 340 of the 400 Premium riders (85%) work the Motorway; only 20 of 600 Standard riders (3%) do. "
  "Motorway riders average 72 km/h against 24 km/h in the inner city, and the Motorway is where injuries happen (6.1 per 1,000 trips against 1.4 in the lanes). "
  "Split by road, Premium is lower every time: 1.0 vs 1.4 (lanes), 2.2 vs 3.0 (arterial), 6.0 vs 8.0 (Motorway). "
  "Caveat: Inner-city Premium rests on a single injury, and riders were not randomised, so this says \u201cthe 2.5x is not the helmet\u201d, not \u201cPremium works\u201d.",
  "Rate per 1,000 trips for each helmet grade within each road type, with injuries/trips printed so small cells are visible.",
  "case01"),
 ("2 \u00b7 Chai and quiz failures", "\u201cCanteen chai sales predict quiz failures\u201d (r = 0.98)",
  "Chai drives failures (or at least is a reliable warning sign); the canteen should rethink its menu.",
  "Exam months push both up. Not so: r between cups and exam month is only 0.06, and inside regular months r is still 0.996, inside exam months 0.996.",
  "<b>Enrolment growth.</b> Students enrolled grew 3.06x over 24 months (1,765 to 5,406). Enrolment correlates 0.997 with cups sold and 0.977 with failures: "
  "more students means more tea and more failed quizzes. Divide both by head-count and r falls from 0.98 to 0.29 (0.20 in regular months, \u22120.03 in exam months). "
  "Exam months do have a higher failure rate per student (3.86 vs 3.42 per 100), but that is a separate effect and unrelated to tea.",
  "Left: all three series indexed to Sep 2024 = 100 (a common base, not two axes). Right: per-student rates, circles regular months, squares exam months.",
  "case02"),
 ("3 \u00b7 The Smog Action Plan", "\u201cThe Smog Action Plan cut Lahore\u2019s AQI by a third\u201d (202 to 137, \u221232%)",
  "The plan worked, and by a lot.",
  "The axis exaggerates the fall. Not so: the recipe starts the axis at zero, and the series is flat on both sides with a single cliff at day 61, so it is not a trend or a seasonal slide.",
  "<b>Composition change: the stations that disappeared were the dirtiest ones.</b> All 6 Industrial stations (mean AQI 322) and 3 of the 6 Arterial stations go blank from day 61 "
  "(540 blank cells = 9 stations x 60 days). <code>pandas.mean()</code> skips blanks without warning, so the \u201cafter\u201d mean is just a cleaner set of stations. "
  "On the 13 stations that report all 120 days the mean is 137.1 before and 137.2 after: no change. Every zone mean is also flat (Arterial 244.7 to 245.9, Residential 121.6 to 120.8, Peri-urban 78.9 to 80.4).",
  "Left: AQI by zone (Industrial and half of Arterial vanish at the dashed line). Right: all-station mean (grey) against the 13 constant stations (blue).",
  "case03"),
 ("4 \u00b7 Four departments", "\u201cFour departments behave identically, so fund them equally\u201d",
  "The four departments have the same study-hours/score relationship (mean 18.0/14.5, r = 0.816, slope 0.25), so treat them alike.",
  "n = 11 is too small to tell them apart. It is not the issue: n is equal and identical in all four, and cohort_group maps one-to-one onto department, so there is no hidden intake split either. The sets differ in shape, not noise.",
  "<b>Identical summary statistics, four different shapes (Anscombe).</b> Computer Science is the only ordinary linear scatter. Business Administration is a curve: a quadratic fits at R\u00b2 = 1.000 against 0.666 for the line, and scores peak near 22 hours then fall. "
  "Electrical Engineering is a perfect line plus one outlier; without it r = 1.000 and the slope is 0.173, not 0.250. "
  "Architecture has ten students at exactly 16 hours and one at 38: without that student the SD of hours is 0 and r does not exist, so the whole 0.817 is one point.",
  "2x2 scatter with the identical fitted line in each panel, same axes.",
  "case04"),
 ("5 \u00b7 Five cohorts", "\u201cFive cohorts, one set of statistics\u201d",
  "The five cohorts are equivalent: each has r = 0.42 between platform hours and score.",
  "Sample size. Not so: every cohort has n = 180, which is plenty, and the statistics match to three decimals because they were forced to (vizlib.match_stats), not by chance.",
  "<b>Summary statistics do not constrain shape.</b> Mean 48.00/63.00, SD 12.00/15.00, r = 0.420 and slope 0.525 are identical, but the cohorts are a noisy line, a ring, a star, two clusters and an X. "
  "The sharpest case is the two clusters: inside each cluster the correlation is negative (\u22120.57 and \u22120.45); the overall +0.42 comes only from the gap between clusters. "
  "In the X, just 22% of points lie within 5 marks of the fitted line.",
  "Five scatter plots with the same fitted line; the table in the left figure shows the identical numbers.",
  "case05"),
 ("6 \u00b7 Creatinine and HbA1c", "\u201cCreatinine tracks HbA1c \u2013 a finding\u201d (r = 0.77)",
  "Kidney function (creatinine) and glycaemic control (HbA1c) move together across the cohort.",
  "With 190 pairs, something was bound to look significant. Not here: 20 pairs pass p < 0.05 against about 9.5 expected, but this one has p \u2248 7e-36, nowhere near a chance finding.",
  "<b>One participant.</b> Row 0 has HbA1c 15.8 and creatinine 1,050 (medians are 5.5 and 81.6). That single point is a leverage point: remove it and r = \u22120.004 (Spearman 0.015); "
  "even with it in, the rank correlation is only 0.03. It sits at Site C, the only site with a strong r (0.92). One row of 180 manufactures the headline. "
  "(Whether that participant is a real very sick patient or a data error cannot be told from this file.) "
  "<b>Two problems, only one of which the redraw fixes.</b> The drawing: Reds with no vmin/vmax runs from \u22120.23 to 1, so negative correlations are pale like zeros and sign is lost, "
  "and both triangles show everything twice. A diverging map pinned to \u22121\u2026+1 with the upper triangle masked fixes the drawing, but it still prints 0.77. Only looking at the scatter exposes the outlier.",
  "Left: the corrected heatmap (RdBu_r, \u22121 to +1, upper triangle masked). Middle: all 180 with the one row marked. Right: the other 179.",
  "case06"),
 ("7 \u00b7 ShaheenGo", "\u201cShaheenGo ran at a loss until May\u201d",
  "Cost exceeded revenue for the first four months; the company turned profitable in May.",
  "That the company really did lose money early. Not so: revenue exceeds cost in every one of the six months (surplus 8, 12, 14, 17, 20, 25 PKR m). Both columns are in PKR millions, so they can be compared directly.",
  "<b>Two y-axes with hand-picked limits.</b> Revenue is drawn on 50\u201380 and cost on 40\u201356, so the picture depends on the limits rather than the data. "
  "In January the cost point (44) lands at 25% of the plot height and the revenue point (52) at 7%, so cost appears above revenue for Jan\u2013Apr. "
  "Over the half-year revenue grew 50% and cost 20%, so the surplus tripled. Both measures share one unit, so there was never a reason for a second axis.",
  "Left: both lines on one shared PKR axis from zero. Right: the surplus itself.",
  "case07"),
 ("8 \u00b7 Bin widths", "\u201cThree bin widths, three different distributions\u201d (bins = 3, 45, 400)",
  "The shape of systolic pressure depends on who plots it: one block, a few peaks, or a spiky mess.",
  "Three different samples or too little data. Not so: it is the same 10,000 values in all three panels.",
  "<b>Bin width is the only thing that changed, and two of the three choices are bad.</b> bins = 3 gives bins 35.7 mmHg wide and hides both humps. bins = 400 gives bins 0.27 mmHg wide over whole-number data (104 distinct values), "
  "so 296 of the 400 bins are empty and the rest are a comb. bins = 45 gives a width of 2.38, not a whole number, so bars alternate between holding two and three integer values and invent spikes (7 peaks). "
  "The truth is steady: with bins aligned to whole mmHg, every width from 2 to 20 shows exactly two peaks (about 121 and 161).",
  "Left: width 4 mmHg (Freedman-Diaconis gives 3.8). Right: peaks found against bin width.",
  "case08"),
 ("9 \u00b7 SpO\u2082 density", "\u201c4.4% of the density sits above 100% saturation\u201d",
  "A material share of patients have impossible oxygen-saturation readings, so the monitors or the records are unreliable.",
  "Faulty readings above 100. Not so: the maximum in the data is exactly 100 and no row exceeds it. The curve exceeds it; the data do not.",
  "<b>Kernel smoothing across a hard boundary.</b> A KDE puts a Gaussian bump on every point, and a Gaussian has no edge, so mass spills past the physical ceiling. "
  "It is worst here because 304 patients (3.0%) sit exactly on 100: the data are piled against the wall. "
  "The default (Scott) bandwidth is 0.35 points, narrower than the 1-point spacing of whole-number readings, which also makes the curve lumpy. "
  "<b>Note:</b> with this recipe I measure 1.6% of the density above 100 (4.3% above 99.5), not 4.4%, so I could not reproduce the headline figure; the mechanism holds either way.",
  "One bar per recorded whole-number value, so nothing can be smoothed past 100.",
  "case09"),
]


def diagnosis():
    doc = SimpleDocTemplate(os.path.join(ROOT, "partA_diagnosis.pdf"), pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=13 * mm, bottomMargin=12 * mm, title="Part A diagnoses",
                            author="Week 3 submission")
    st = []
    st.append(Paragraph("Part A \u00b7 Nine charts, taken apart", ParagraphStyle("T", parent=H, fontSize=16, spaceAfter=3)))
    st.append(Paragraph("All data are synthetic, generated for CDB601220. Figures: left = rebuilt from the recipe, right = honest redesign.", CAP))
    st.append(Spacer(1, 3))
    for i, (title, claim, concl, decoy, mech, red, key) in enumerate(CASES):
        block = [Paragraph(title, H), Paragraph(claim, CLAIM),
                 Paragraph(f"<b>Conclusion it invites.</b> {concl}", B),
                 Paragraph(f"<b>The decoy.</b> {decoy}", B),
                 Paragraph(f"<b>The mechanism.</b> {mech}", B),
                 Paragraph(f"<b>The redesign.</b> {red}", B), Spacer(1, 3)]
        st.extend(block)
        a, b = f"{key}_rebuild.png", f"{key}_redesign.png"
        mh = 66 * mm if key == "case06" else 80 * mm
        st.append(fig(a, 175 * mm, mh))
        st.append(Spacer(1, 4))
        st.append(fig(b, 175 * mm, mh))
        if i < len(CASES) - 1:
            st.append(PageBreak())
    doc.build(st)


def justification():
    doc = SimpleDocTemplate(os.path.join(ROOT, "partE_justification.pdf"), pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=10 * mm, bottomMargin=9 * mm, title="Part E justification")
    s = ParagraphStyle("s", parent=B, fontSize=7.9, leading=10.2, spaceAfter=2.4)
    h = ParagraphStyle("h", parent=H, fontSize=9.5, spaceAfter=1, spaceBefore=3)
    t = [Paragraph("Part E \u00b7 Justification for the clinical review figure", ParagraphStyle("T", parent=H, fontSize=12, spaceAfter=2)),
         Paragraph("Data: vitals_10k.csv (10,000 admissions, 1 Jan\u201330 Apr 2026), synthetic, generated for CDB601220.", CAP),
         Paragraph("1 \u00b7 Each panel: question, chart type, Week 2 channel rule", h),
         Paragraph("<b>Panel 1, is systolic pressure one population? </b>A histogram, because one continuous variable is read by bar length from a shared zero baseline, the most accurate channel "
                   "(position/length on a common scale). It shows two humps, near 120 and 160 mmHg (58% / 42% split at the 140 valley); nothing else in the file (ward, sex, age) separates the groups, so I report it as unexplained.", s),
         Paragraph("<b>Panel 2, how do wards differ in length of stay? </b>A box plot, because it compares one distribution across four categories with median, spread and tail in one mark, "
                   "ordered by median so position carries the ranking. Log scale because the data are right-skewed. ICU median 3.47 days against 0.25 for day surgery (about 14x). One colour with a single highlighted category (ICU).", s),
         Paragraph("<b>Panel 3, how does cholesterol move with age? </b>A scatter, because two continuous variables need position on both axes. It is the one pair worth plotting: panel 4 shows age\u2013cholesterol (\u03c1 = 0.33) "
                   "as the only association that is neither arithmetic nor flat. Alpha 0.18 handles 10,000 overlapping points without hiding density; the line is OLS, slope +0.21 mmol/L per decade.", s),
         Paragraph("<b>Panel 4, which variables move together? </b>A heatmap, as a screening tool across 36 pairs. Colour is the weakest channel, so every cell is annotated; a diverging RdBu_r scale pinned to \u22121\u2026+1 "
                   "is used because a correlation has a sign, with the redundant upper triangle masked. Palette: the three-slot Okabe\u2013Ito set (worst CVD \u0394E 8.4, tritan); the 4th slot is not used.", s),
         Paragraph("2 \u00b7 Every parameter chosen, and why", h),
         Paragraph("<b>Panel 1: bin width 4 mmHg</b> (whole mmHg, so bins never alias; Freedman\u2013Diaconis gives 3.8; any width from 2 to 20 shows the same two peaks); split at 140 mmHg, the valley. "
                   "<b>Panel 2:</b> log y-axis (stays are skewed; 2 zero-day stays cannot be drawn on it and are left off that axis only); whiskers at the default 1.5 IQR; fliers shown (<i>showfliers</i> is left on). "
                   "<b>Panel 3:</b> alpha 0.18, marker size 5, no subsampling. <b>Panel 4:</b> Spearman, not Pearson, because glucose and stay length are skewed and, as case 6 showed, one extreme value can fake a Pearson r; "
                   "vmin \u22121, vmax +1, centre 0, annotation to two decimals; <i>map_mmhg</i> excluded because it is computed from systolic and diastolic. Export: 300 dpi, tight bbox, white facecolor.", s),
         Paragraph("3 \u00b7 Every row removed, with rule, count and effect", h)]
    rows = [["Rule", "Count", "Mean moves"],
            ["Ward: 12 spellings conformed to 4 (no rows lost)", "0 dropped", "n/a"],
            ["Dates: 3 formats parsed, day-first for slash dates (first field reaches 31)", "0 dropped", "n/a"],
            ["BMI sentinels 0 and 999 set to missing (row kept)", "486 (84 + 402)", "66.18 \u2192 27.35 kg/m\u00b2"],
            ["Heart rate < 30 or > 250 bpm set to missing: device faults (row kept)", "37 (8 zeros, 29 of 331\u2013415)", "78.83 \u2192 78.05 bpm"],
            ["Length of stay > 100 days set to missing (next-highest value is 24)", "18 (140\u2013274 days)", "2.31 \u2192 1.95 days"]]
    tb = Table([[Paragraph(c, s) for c in r] for r in rows], colWidths=[112 * mm, 40 * mm, 30 * mm])
    tb.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DFE6EE")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF3F8")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    t.append(tb)
    t.append(Spacer(1, 3))
    t.append(Paragraph("<b>Ethics clause.</b> Readings above 250 bpm, and readings of 0 bpm, were removed as device faults (n = 37). Mean heart rate moves from 78.83 to 78.05 bpm. "
                       "The figure was also produced without the exclusions (heart rate, BMI and stay length); it is in the appendix (partD_figure_appendix.png) and its four messages are the same, "
                       "because panel 4 uses rank correlations. Fault readings are blanked rather than deleted, so no patient is lost.", s))
    t.append(Paragraph("<b>Symmetry test.</b> The thresholds come from physiology and from visible gaps in the data (stays jump from 24 to 140 days; heart rates run 38\u2013135 bpm, then jump to 331+, with a block of zeros), not from the figure. "
                       "I would have applied the same rules if they had weakened my conclusion; here they happen not to change it. "
                       "<b>Not done:</b> <i>risk_score</i> is a ratio (events/day) and is not averaged by ward, because a mean of ratios is not a rate.", s))
    doc.build(t)


if __name__ == "__main__":
    diagnosis()
    justification()
    print("wrote partA_diagnosis.pdf and partE_justification.pdf")

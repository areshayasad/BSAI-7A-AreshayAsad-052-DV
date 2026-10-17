# Week 4 — Time-Series, Proportions & Hierarchies
**CDB601220 Data Visualization · Superior University Lahore**

| | |
|---|---|
| **Name** | Areshay Asad |
| **Roll no.** | 052 |
| **Programme / section** | BSAI · 7A |
| **Submission file** | `DV_LAB_TASK4` |

All data in `data/` is **synthetic** course data generated for CDB601220 Week 4. The one exception is Part F, which uses **real** BLS data (cited below).

---

## 1. Tasks attempted

| Part | Task | Marks | Status |
|---|---|---|---|
| **A** | Rebuild nine charts, diagnose them, plot nine redesigns | 36 | Done. All 9 self-checks pass |
| **B** | Windows, smoothers, decomposition, trailing vs centred, window sweep, all computed | 15 | Done |
| **C** | Part-to-whole legality (C.1), pie-ranking experiment (C.2/C.3), rule (C.4) | 9 | C.1 and C.4 done. **C.2/C.3 need one real reader (section 2)** |
| **D** | 2×2 e-commerce review figure, 300 dpi | 25 | Done |
| **E** | One-page written justification | 15 | Done (exactly 1 page) |
| **F** | *Bonus.* Week 1 flights question on data I found | 5 (separate) | Done |

---

## 2. Action needed before you submit: Part C experiment

The brief requires the pie-ranking experiment to be run on **a real reader**, and says invented results score zero. So `pie_ranking_results.csv` is deliberately **not included**. Nothing was fabricated.

Done already: the three-condition tests, both stimulus PNGs, the scoring code, and the C.4 rule.

To finish (about 2 minutes), with a classmate or friend who has **not** seen the shares:

```bash
python3 partC_shares.py --run
```

It shows the pie, then the sorted bars, times each with `time.perf_counter()`, writes `pie_ranking_results.csv`, and prints the C.3 scoring (letters misplaced, where the errors fell, whether C/H/G were the confusion, and the limits of a sample of one). Then save the output and submit it with the CSV:

```bash
python3 partC_shares.py > partC_output.txt
```

---

## 3. What is in the folder

```
partA_charts.py            rebuilds all nine and plots the nine redesigns
figs/case01..09_rebuild.png, case01..09_redesign.png      the 18 Part A figures (300 dpi)
partA_diagnosis.pdf        nine diagnoses, both figures per case
partA_output.txt           the nine self-checks, printed

partB_windows.py           windows, smoothers, decomposition, lag, window sweep
partB_output.txt           its printed output          partB_windows.png   three supporting panels

partC_shares.py            legality tests, stimuli, experiment runner, scoring
partC_output.txt           printed output              pie_stimulus.png, bars_stimulus.png
(pie_ranking_results.csv   created by --run; see section 2)

partD_figure.py            cleaning pipeline + the figure (Part B imports its cleaning)
partD_figure.png           the exported 300 dpi 2×2 figure
partD_log.txt              proof the script ran, with every data-problem rule and count
partD_appendix.py, partD_appendix_28day.png     the 28-day window version cited in Part E

partE_justification.pdf    one page

partF_cycle.py, partF_cycle.png, partF_output.txt     bonus
partF_data/                the source file and SOURCE.md (citation + download date)

data/  tslib.py  vizlib.py     supplied data and toolkit, bundled so it runs from a clean checkout
build_pdfs.py              builds both PDFs from the JSON the scripts wrote
run_all.sh  requirements.txt  README.md
```

---

## 4. How to run

```bash
pip install -r requirements.txt     # Python 3.9+
bash run_all.sh                     # rebuilds every output from data/ (no downloads, about 1 minute)
```

Tested from a fresh copy with all outputs deleted: exit 0, 18 Part A figures, every export at 300 dpi.

---

## 5. Results by part

### Part A: nine charts (conclusion, decoy, mechanism, redesign)

| # | Published claim | Mechanism (the number that proves it) | Redesign |
|---|---|---|---|
| 1 | Orders peak in Q1 and collapse every year | `month` is text `YYYY-M`, so a text sort puts 2024-10…12 before 2024-2. 22 of 24 rows misplaced. In calendar order there are **0 falls in 23 changes**; orders rise 4,200 → 6,405 (+52%) | Calendar-ordered line |
| 2 | Sales grew steadily, 22% | **21 consecutive missing days** (3–23 Feb, shop closed). Row-number axis deletes the gap. Step of **+56.1 (+28.6%)**, 196.2 → 252.3 | Calendar axis, gap shaded, segment means |
| 3 | Peak load jumped 43% on 1 July | A level (`concurrent_users`) was summed. June has **16.4 of 24 hours** per day recorded, July 24. Mean is flat (**−2.5%**) | Daily mean plus hours recorded per day |
| 4 | New flow started working 7 Sep | Trailing mean lags by half the window: centred minimum **23 Aug**, trailing **7 Sep**, lag **15 days = half-window** | Centred + trailing + raw, lag marked |
| 5 | Revenue fell six straight months | Window runs peak to trough. The same May→Nov fall is **−42.4%, −42.8%, −41.9%** in 2023/24/25, while every 2025 month is above 2024 (+5.9% to +12.9%). Chart is incomplete, not wrong | Cycle plot, one line per year |
| 6 | Orders collapsed in October | Data ends **11 Oct**: 11 of 31 days summed. Per day, October is **367.4 vs 360.2** in September | Orders per day, partial month hatched |
| 7 | Product D is erratic | Stacking: D rides on A+B+C. Product B (CV 23%) drives 93% of the baseline variance. D's own CV is **3.5%**, the lowest of the four | Small multiples, shared axis |
| 8 | Search drives 43% of customers | Touches are not exclusive: shares sum to **131.0%**, 1,105 customers (27.6%) touched by 2+ channels. Search is the only touch for 25.9% | Reach bars split "only" / "also another channel" |
| 9 | Premium is 38%, a record | Denominator fell 40% (1000 → 600). Premium revenue itself fell **5%** (240 → 228). Chart is incomplete, not wrong | Share beside numerator and denominator |

### Part B: computed on the cleaned daily series

| Question | Result |
|---|---|
| B1 window report (7 / 28 / 91) | variation removed 30.8% / 33.8% / 38.1%; periods lost each end 3 / 14 / 45. **Chosen: 7 days**, the cycle removed is weekly |
| B2 smoothers at Black Friday (raw 113,710) | centred mean **33,480**, centred median **24,780**, EWMA **38,050**. Monitoring: EWMA. Quarterly report: median |
| B3 decomposition | weekly seasonal peak-to-trough **7,578**; largest residual **29 Nov 2024** (+74,597). `period=365` is refused by statsmodels (needs 730 points, have 529) and this is reported |
| B4 trailing vs centred (31 d) | centred 27 May 2025, trailing 11 Jun 2025: lag **15 = half-window**. A live dashboard must show trailing and say so |
| B5 window sweep (12 starts × 5 windows) | **34 rising, 26 falling** on one unchanged series. Lie Factor is undefined because there is no single "effect in the data" to divide by |
| Sensitivity | all key numbers re-run with and without topping up sentinel hours; no conclusion changes |

### Part C: legality (done), experiment (pending a reader)

| Table | Verdict |
|---|---|
| `touch_*` columns | **Neither** as parts of a whole: sum 131%, not exclusive |
| `shares_eight.csv` | Legal on conditions 1–2, but **sorted bars**: eight slices, middle gaps of only 1.9–2.0 points |
| Premium vs other, 2025Q4 | Two-slice pie is legal; not enough for the "record" claim |

**C.4 rule:** I will draw a pie only when there are two or three exclusive parts of a meaningful whole, the share itself is the question, and nobody needs to rank close slices; otherwise a sorted bar chart.

### Part D: the figure

**Faults found and handled** (rule and count for each in `partD_log.txt` and in Part E):
1. Two timestamp formats. The slash format is day-first (2,151 rows have a first field above 12, none a second). `format="mixed"` would silently move 1,382 rows.
2. `sessions = -1` sentinels: 287, set to missing.
3. Device spelled six ways: 1,447 rows relabelled.
4. Rows not in time order.
5. 286 exact duplicates, only visible once the index is a real `DatetimeIndex`.
6. 13 never-recorded days, counted on the hourly index and left as gaps.
7. Partial final month (11 Sep 2025), shaded and labelled.

**Catalogue:** SKU-0127 was listed under two parents, and the Wearables copy was removed (that was the ~0.9-point error). 7 negative-net SKUs are reported but not drawn. Final shares are within **0.23 points** of `shares_eight.csv`.

**Panels:** (1) daily sessions, raw grey plus 7-day centred mean; (2) day × hour heatmap, sequential Blues; (3) category → sub-category treemap, one hue per parent; (4) sorted bars with values printed. Palette proved with `vizlib.worst_pair`, and the 4th hue is always directly labelled.

### Part E: justification
One page: per-panel question, chart type and Week 2 rule; every time decision; every row removed (rule, count, from → to); roll-up declaration (no `Other` bucket, smallest sub-category 2.4%); and the window-choice clause. The 7-day window was fixed before plotting, no start date was selected, and the 28-day alternative is in `partD_appendix_28day.png`.

### Part F: bonus (real data)
- **Source:** U.S. Bureau of Labor Statistics, unemployed persons by industry, monthly Jan 2000 – Feb 2010, via vega-datasets. Downloaded 2026-10-18. Full citation in `partF_data/SOURCE.md`.
- **Series:** Construction.
- **Audit:** 122 months, 0 duplicates, 0 missing, partial tail (2010 has 2 months, excluded from per-year statistics).
- **Answer:** The level rose **×3.5** (2000–2009) but the absolute seasonal swing only **×1.2**. The swing fell from 83% to 28% of the level (correlation −0.83). So the seasonality is not growing in proportion to the series.
- **Caveat:** The residual test is weak for both models (|ρ| 0.13 additive, 0.03 multiplicative), so it does not overturn this. This is one series in one recession and disagrees with the airline textbook case; it is reported as found.

---

## 6. Decisions to know before marking
- **Sentinel hours:** days containing a `-1` hour are topped up from the same-weekday profile so a missing evening hour does not look like a dip (222 days, mean +5.8%). Part B reports every key number both ways.
- **Fixed before plotting:** the 7-day window, the 12 start months in B5 (the first 12 month-starts of the series) and the day-first date rule. None was chosen after seeing a result.
- **Honest limits:** `period=365` cannot run on 529 days; Part C results exist only if a real reader is run.

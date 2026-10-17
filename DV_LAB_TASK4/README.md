# Week 4 — Time-Series, Proportions & Hierarchies (CDB601220 Data Visualization)

| | |
|---|---|
| **Name** | Areshay Asad |
| **Roll no.** | 052 |
| **Programme / section** | BSAI · 7A |
| **Submission** | `W4_052.zip` (this folder, zipped) |

## Tasks attempted

| Part | What | Status |
|---|---|---|
| **A** (36) | Nine charts rebuilt, diagnosed (conclusion, decoy, mechanism, redesign), redesigns plotted | Done — all 9 self-checks pass |
| **B** (15) | Windows, three smoothers, decomposition, trailing vs centred, 60-window sweep — all computed | Done |
| **C** (9) | Legality tests (C.1) and rule (C.4) done. **C.2/C.3 need one real reader — see below** | **Action needed** |
| **D** (25) | 2×2 review figure, 300 dpi, every data fault handled with a stated rule | Done |
| **E** (15) | One-page justification incl. the window-choice clause | Done (1 page) |
| **F** (bonus) | Week 1's flights question, settled on real BLS data | Done |

## ⚠ Part C: one step only a human can do

The brief requires the pie-ranking experiment to be run on **a real reader** with real timings, and states that
invented results score zero. So `pie_ranking_results.csv` is **deliberately not in this folder** — nothing has
been fabricated. Everything else for Part C (the three-condition tests, both stimulus PNGs, the scoring code and
the C.4 rule) is done. To finish it (~2 minutes):

```bash
python3 partC_shares.py --run     # a classmate/friend who has NOT seen the shares; it times them
```

It shows the pie (`pie_stimulus.png`), then the sorted bars (`bars_stimulus.png`), times each with
`time.perf_counter()`, writes `pie_ranking_results.csv`, and prints the C.3 scoring (letters misplaced, where the
errors fell, whether C/H/G were the confusion) and the honest limits of a sample of one. Re-run
`python3 partC_shares.py > partC_output.txt` and submit that output with the CSV.

## What is in the folder (matches the brief's hand-in list)

```
partA_charts.py            rebuilds all nine and plots the nine redesigns  (+ figs/case01..09_{rebuild,redesign}.png)
partA_diagnosis.pdf        nine diagnoses, both figures per case
partB_windows.py           + partB_output.txt (printed output) + partB_windows.png
partC_shares.py            + partC_output.txt, pie_stimulus.png, bars_stimulus.png   (pie_ranking_results.csv: see above)
partD_figure.py            the script (also the cleaning module Part B imports)
partD_figure.png           300 dpi, 4 panels      partD_log.txt = proof it ran      partD_appendix_28day.png (+ partD_appendix.py)
partE_justification.pdf    one page               (built by build_pdfs.py from the JSON the scripts wrote)
partF_cycle.py             + partF_cycle.png + partF_data/ (source file and SOURCE.md citation)
data/  tslib.py  vizlib.py the supplied data and toolkit, bundled so everything runs from a clean checkout
```

## Run it

```bash
pip install -r requirements.txt     # Python 3.9+
bash run_all.sh                     # rebuilds every output from data/ (no downloads, ~1 min)
```

Tested from a fresh copy of this folder with all outputs deleted: exit 0, 18 Part A figures, every export at 300 dpi.

## Decisions worth knowing before you mark

* **Timestamps.** `sessions_hourly.csv` mixes ISO and `DD/MM/YYYY`. The slash format is day-first (proved: 2,151 rows
  have a first field > 12, none a second). `pd.to_datetime(format="mixed")` would silently move 1,382 rows.
* **Six faults + the tail:** two date formats · `sessions = −1` sentinels (287) · device spelled six ways · rows unsorted ·
  286 exact duplicates (only visible once the index is a `DatetimeIndex`) · 13 never-recorded days (counted on the *hourly*
  index) · extract ends 11 Sep 2025 (partial month, shaded).
* **Catalogue.** SKU-0127 is listed under two parents (Audio and Wearables) — the Wearables copy is removed (that was the
  ~0.9-point error); 7 negative-net SKUs are not drawn but reported. Final shares are within 0.23 pp of `shares_eight.csv`.
* **Sentinel hours.** Days with a `−1` hour are topped up from the same-weekday profile so a lost evening hour does not
  look like a dip. Part B runs every key number both ways (topped-up vs plain sum); no conclusion changes.
* **Part B.3, `period=365`.** statsmodels refuses (needs 730 daily points, there are 529). This is reported, not hidden.
* **Part F** uses **real** data (U.S. BLS unemployed persons by industry via vega-datasets, downloaded 2026-10-18); the result
  *disagrees* with the textbook airline case and is reported as found. Everything else here is synthetic course data.

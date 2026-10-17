#!/usr/bin/env bash
# Rebuilds every output in this folder from the bundled data. No downloads needed.
set -euo pipefail
cd "$(dirname "$0")"
python3 tslib.py                 # toolkit self-check
python3 partA_charts.py          # 18 figures + partA_numbers.json
python3 partD_figure.py          # cleaning + the 2x2 figure (300 dpi)
python3 partD_appendix.py        # 28-day window appendix
python3 partB_windows.py         # windows, smoothers, decomposition, lag, sweep
python3 partC_shares.py | tee partC_output.txt   # legality tests + stimuli (add --run for the reader)
python3 partF_cycle.py           # bonus
python3 build_pdfs.py            # partA_diagnosis.pdf + partE_justification.pdf

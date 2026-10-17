#!/usr/bin/env python3
"""
Part C - part-to-whole legality, and the pie-ranking experiment.

    python3 partC_shares.py          C.1 legality tests + writes both stimuli.
                                     If pie_ranking_results.csv exists, also
                                     scores it (C.3).
    python3 partC_shares.py --run    administers the experiment to a REAL reader,
                                     timing each stimulus with time.perf_counter(),
                                     appends to pie_ranking_results.csv, then scores.
    python3 partC_shares.py --score  score the existing CSV only.

NOTHING in the results file is invented: it only ever contains what a reader
typed and what perf_counter measured. Until a reader has been run, the script
says so instead of printing a result.

SYNTHETIC course data, CDB601220 Week 4.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tslib import PALETTE, exclusivity_check, save_fig, style_defaults

DATA = HERE / "data"
RESULTS = HERE / "pie_ranking_results.csv"
PIE_PNG, BAR_PNG = HERE / "pie_stimulus.png", HERE / "bars_stimulus.png"
FIELDS = ["reader", "stimulus", "order_given", "true_order", "n_wrong_letters",
          "wrong_rank_positions", "seconds"]
SYNTH = "SYNTHETIC course data, CDB601220 Week 4."


# ======================================================================= C.1
def legality() -> None:
    print("=" * 78)
    print("C.1  THE THREE CONDITIONS (slide 32), TESTED IN CODE")
    print("     1 exclusive parts   2 a meaningful whole   3 the share IS the question")
    print("=" * 78)

    # ---- (a) the four touch_* columns --------------------------------------
    d = pd.read_csv(DATA / "case08_channel_attrib.csv")
    cols = [c for c in d.columns if c.startswith("touch_")]
    ex = exclusivity_check(d, cols)
    print("\n(a) case08_channel_attrib.csv - the four touch_* columns")
    print(f"    1 exclusive?     {ex['exclusive']}  - {ex['n_multi']:,} of {ex['n']:,} customers "
          f"({ex['pct_multi']:.1f}%) carry two or more flags; {ex['n_zero']} carry none")
    print(f"      shares: " + ", ".join(f"{k.split('_')[1]} {v:.1f}%" for k, v in ex["shares_pct"].items()))
    print(f"      sum = {ex['sum_pct']:.2f}%  (a pie needs exactly 100)")
    assert not ex["exclusive"] and abs(ex["sum_pct"] - 100) > 1
    print("    2 meaningful whole? No. 'All customers' is the whole, but each slice is a")
    print("      fraction OF THAT WHOLE, not a part OF it: the slices do not partition it.")
    print("    3 share the question? The question is 'how many customers does each channel")
    print("      reach' - reach, not a split of a total.")
    print("    VERDICT: NEITHER as parts of a whole. A pie is illegal (131%). A sorted bar")
    print("      chart is legal only if it is labelled 'customers reached (%)', each bar")
    print("      read against 100%, never as slices of one - or better, split each bar into")
    print("      'only this channel' vs 'also others' (Part A case 8).")

    # ---- (b) shares_eight ---------------------------------------------------
    s = pd.read_csv(DATA / "shares_eight.csv")
    tot = s.share_pct.sum()
    srt = s.sort_values("share_pct", ascending=False).share_pct.to_numpy()
    gaps = -np.diff(srt)
    cat = pd.read_csv(DATA / "revenue_catalogue.csv").drop_duplicates("sku")
    one_parent = bool((cat.groupby("sku").subcategory.nunique() == 1).all())
    print("\n(b) shares_eight.csv - eight sub-categories")
    print(f"    1 exclusive?     True - every (de-duplicated) SKU sits in exactly one sub-category "
          f"({one_parent}); sum = {tot:.6f}%")
    assert abs(tot - 100) < 1e-6
    print("    2 meaningful whole? Yes: net revenue of the whole catalogue; there are exactly")
    print("      eight sub-categories, so 'the eight-category total' is the whole catalogue.")
    print(f"    3 share the question? Partly. 'Where is the mass' is a share question, but the")
    print(f"      task is to RANK eight slices. Eight is above the ~5 a pie can carry, and the")
    print(f"      middle is crowded: the gaps between neighbours (largest first) are")
    print("      " + ", ".join(f"{g:.1f}" for g in gaps) + f" points; the smallest is {gaps.min():.1f}.")
    print("    VERDICT: legal on conditions 1-2, but BAR CHART (sorted) - condition 3 fails")
    print("      because the reader must order close values, and position beats angle (W2).")

    # ---- (c) premium vs other, 2025Q4 --------------------------------------
    q = pd.read_csv(DATA / "case09_premium_share.csv")
    q["other"] = q.total_revenue_pkr_m - q.premium_revenue_pkr_m
    last = q.iloc[-1]
    ok_excl = bool(((q.other >= 0) & (q.premium_revenue_pkr_m >= 0)).all())
    share = last.premium_revenue_pkr_m / last.total_revenue_pkr_m * 100
    print("\n(c) premium vs other, 2025Q4 (case09_premium_share.csv)")
    print(f"    1 exclusive? True by construction: other = total - premium, both >= 0 in all "
          f"8 quarters ({ok_excl}); {last.premium_revenue_pkr_m:.1f} + {last.other:.1f} = "
          f"{last.total_revenue_pkr_m:.1f} PKR m")
    print(f"    2 meaningful whole? Yes - total revenue for the quarter.")
    print(f"    3 share the question? For the single quarter yes (premium = {share:.1f}%), but the")
    print(f"      CLAIM is 'a record', which is about change - and the whole fell from "
          f"{q.total_revenue_pkr_m.iloc[0]:.0f} to {last.total_revenue_pkr_m:.0f}.")
    print("    VERDICT: a two-slice pie (or one stacked bar) is LEGAL for 2025Q4 alone, since")
    print("      two exclusive parts of a real whole is the pie's best case. It is NOT enough")
    print("      for the claim: show premium and other in PKR m beside the share (Part A case 9).")


# ===================================================================== stimuli
def load_shares() -> pd.DataFrame:
    return pd.read_csv(DATA / "shares_eight.csv")


def build_stimuli() -> None:
    style_defaults()
    s = load_shares()
    pal = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#56B4E9", "#E69F00", "#999999", "#332288"]
    # pie: the file's order, no numbers, letters only
    fig, ax = plt.subplots(figsize=(5.4, 5.4))
    ax.pie(s.share_pct, labels=s.slice, colors=pal, startangle=90, counterclock=False,
           wedgeprops=dict(edgecolor="white", linewidth=1.5), textprops=dict(fontsize=14))
    ax.set_title("Stimulus 1 - rank slices A-H, largest first", loc="left", fontsize=11)
    save_fig(fig, PIE_PNG, note=SYNTH + " No numbers on the pie by design.")
    plt.close(fig)
    # bars: sorted horizontal, letters only, axis kept (it is the chart's advantage)
    o = s.sort_values("share_pct", ascending=False)
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    ax.barh(range(len(o)), o.share_pct, color=PALETTE["series"][0], height=0.66)
    ax.set_yticks(range(len(o)), o.slice, fontsize=13)
    ax.invert_yaxis()
    ax.set_xlim(0, 28)
    ax.set_xlabel("Share of the eight-category total (%)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Stimulus 2 - rank slices A-H, largest first", loc="left", fontsize=11)
    save_fig(fig, BAR_PNG, note=SYNTH + " Sorted; no value labels, axis shown.")
    plt.close(fig)
    print(f"\nstimuli written: {PIE_PNG.name}, {BAR_PNG.name}  (300 dpi)")


def true_order() -> str:
    s = load_shares().sort_values("share_pct", ascending=False)
    return "".join(s.slice)


# ======================================================================= run
def ask(prompt_png: Path, label: str, reader: str) -> dict:
    truth = true_order()
    input(f"\n--- {label} ---\nOpen {prompt_png.name} (it will try to open now). "
          f"Press Enter when the image is visible and the reader is ready... ")
    try:
        webbrowser.open(prompt_png.resolve().as_uri())
    except Exception:
        print(f"(open {prompt_png} yourself)")
    t0 = time.perf_counter()
    while True:
        raw = input("Reader: type the letters A-H largest first, no spaces (e.g. ABCDEFGH): ")
        order = "".join(ch for ch in raw.upper() if ch.isalpha())
        if sorted(order) == list("ABCDEFGH"):
            break
        print("  need each of A-H exactly once - try again (the clock is still running)")
    secs = time.perf_counter() - t0
    return _row(reader, label, order, truth, secs)


def _row(reader, stim, order, truth, secs) -> dict:
    wrong_pos = [i + 1 for i, (a, b) in enumerate(zip(order, truth)) if a != b]
    return dict(reader=reader, stimulus=stim, order_given=order, true_order=truth,
                n_wrong_letters=len(wrong_pos),
                wrong_rank_positions=" ".join(map(str, wrong_pos)) or "none",
                seconds=round(secs, 2))


def run_experiment() -> None:
    reader = input("Reader's name or initials: ").strip() or "reader1"
    print("\nThe reader must NOT have seen the shares. Do not tell them the answer.")
    rows = [ask(PIE_PNG, "pie", reader), ask(BAR_PNG, "sorted bars", reader)]
    new = not RESULTS.exists()
    with open(RESULTS, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerows(rows)
    print(f"\nsaved {len(rows)} rows to {RESULTS.name}")


# ===================================================================== C.3 / C.4
def score() -> None:
    print("\n" + "=" * 78)
    print("C.2 / C.3  RESULTS FROM THE REAL READER(S)")
    print("=" * 78)
    if not RESULTS.exists():
        print("NO READER DATA YET. Run:  python3 partC_shares.py --run")
        print("(Nothing is scored or reported until a person has actually done it.)")
        return
    r = pd.read_csv(RESULTS)
    truth = true_order()
    print(f"true order (largest first): {' '.join(truth)}   "
          f"= " + ", ".join(f"{l} {v:.1f}" for l, v in
                             load_shares().set_index('slice').share_pct.loc[list(truth)].items()))
    for _, row in r.iterrows():
        top2 = row.order_given[:2] == truth[:2]
        bottom = row.order_given[-1] == truth[-1]
        mid = row.order_given[2:5]
        print(f"\n  reader {row.reader!r} - {row.stimulus}")
        print(f"    order given        : {row.order_given}")
        print(f"    time               : {row.seconds:.2f} s")
        print(f"    letters misplaced  : {row.n_wrong_letters} of 8   (rank positions: {row.wrong_rank_positions})")
        print(f"    top two correct    : {top2}   bottom one correct: {bottom}")
        print(f"    middle (ranks 3-5) : gave {mid}, truth {truth[2:5]}  "
              f"-> {'errors fell in the middle (C 15.0 / H 13.1 / G 11.2)' if row.n_wrong_letters and all(2 <= int(p) - 1 <= 4 for p in str(row.wrong_rank_positions).split() if p != 'none') else ('no errors' if not row.n_wrong_letters else 'errors reached the ends')}")
    for who, g in r.groupby("reader"):
        if set(g.stimulus) >= {"pie", "sorted bars"}:
            p, b = g[g.stimulus == "pie"].iloc[0], g[g.stimulus == "sorted bars"].iloc[0]
            print(f"\n  {who}: pie {p.seconds:.1f} s / {p.n_wrong_letters} wrong  vs  bars {b.seconds:.1f} s / "
                  f"{b.n_wrong_letters} wrong  (bars are {p.seconds / b.seconds:.1f}x the speed)")
    print("\n  Limits: ", len(r.reader.unique()), "reader(s) cannot separate the chart from the person - one")
    print("  reader's speed, familiarity with pies, and the order the stimuli were shown (pie")
    print("  first, so the bars were seen second, with the letters already in mind) are all")
    print("  confounded with chart type. It can show the failure mode is possible, not that")
    print("  it is typical. Cleveland & McGill (1984) is the evidence for the general claim.")


def rule() -> None:
    print("\n" + "=" * 78)
    print("C.4  MY RULE")
    print("=" * 78)
    print("  I will draw a pie only when there are two or three exclusive parts of a")
    print("  meaningful whole, the part-to-whole share itself is the question, and nobody")
    print("  needs to rank or compare close slices - otherwise a sorted bar chart.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="administer the experiment to a real reader")
    ap.add_argument("--score", action="store_true", help="score the existing CSV only")
    a = ap.parse_args()
    if a.score:
        score()
        rule()
        sys.exit(0)
    legality()
    build_stimuli()
    if a.run:
        run_experiment()
    score()
    rule()

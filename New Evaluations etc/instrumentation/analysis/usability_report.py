#!/usr/bin/env python3
"""Usability leg: task performance + SUS + UMUX-Lite + NASA-TLX -> LaTeX and prose.

Two CSVs (templates in ../templates):
  usability_tasks.csv  one row per (participant, task)
  usability_survey.csv one row per participant

Statistics deliberately conservative:
 * task success uses a Wilson score interval, not a normal approximation - with
   n <= 10 the normal approximation is wrong in both directions;
 * SUS is computed with the canonical transformation (odd items x-1, even items 5-x,
   sum x 2.5) and reported as a median and an interquartile range, not a bare mean;
 * a sample of ten or fewer is labelled a pilot in every sentence we emit. We do not
   let a 6-person study sound like an evaluation.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

Z = 1.959963984540054


def wilson(k: int, n: int, z: float = Z):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = (z / den) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round(max(0.0, c - h) * 100, 1), round(min(1.0, c + h) * 100, 1))


def median_iqr(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None, None
    if len(vals) == 1:
        return round(float(vals[0]), 2), None
    q = statistics.quantiles(vals, n=4, method="inclusive")
    return round(statistics.median(vals), 2), [round(q[0], 2), round(q[2], 2)]


def num(row, key, cast=float, default=None):
    v = (row.get(key) or "").strip()
    if v == "":
        return default
    try:
        return cast(float(v))
    except ValueError:
        try:
            return cast(v)
        except ValueError:
            return default


def read(path: Path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)]


SUS_ITEMS = [f"Q{i}" for i in range(1, 11)]


def sus_score(row) -> float | None:
    vals = []
    for i, q in enumerate(SUS_ITEMS, start=1):
        v = num(row, q, int)
        if v is None or not 1 <= v <= 5:
            return None
        vals.append(v - 1 if i % 2 else 5 - v)
    return round(sum(vals) * 2.5, 1)


def umux(row):
    q1, q2 = num(row, "U1", int), num(row, "U2", int)
    if q1 is None or q2 is None:
        return None
    return round(((q1 + (6 - q2)) - 2) / 8 * 100, 1)


TLX = ["mental", "physical", "temporal", "performance", "effort", "frustration"]
TLX_W = ["w_mental", "w_physical", "w_temporal", "w_performance", "w_effort", "w_frustration"]


def tlx(row):
    vals = [num(row, k, float) for k in TLX]
    if any(v is None for v in vals):
        return None
    ws = [num(row, k, float) for k in TLX_W]
    if all(w is not None for w in ws) and sum(ws) > 0:
        return round(sum(v * w for v, w in zip(vals, ws)) / sum(ws), 1)
    return round(sum(vals) / 6, 1)     # unweighted; reported as such


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, required=True)
    ap.add_argument("--survey", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, default=Path("results"))
    a = ap.parse_args()

    tasks = read(a.tasks)
    survey = read(a.survey)
    if not tasks and not survey:
        raise SystemExit("both CSVs empty or missing - nothing to report")

    # ---- per task
    by_task = defaultdict(list)
    for r in tasks:
        by_task[(num(r, "task_id", int) or 0, (r.get("task_name") or "").strip())].append(r)
    task_rows = []
    for (tid, name), rs in sorted(by_task.items()):
        n = len(rs)
        k = sum(1 for r in rs if num(r, "success", int) == 1)
        ci = wilson(k, n)
        med_t, iqr_t = median_iqr([num(r, "time_s", float) for r in rs])
        k_ui = sum(1 for r in rs if num(r, "correct_ui", int) == 1)
        k_help = sum(1 for r in rs if num(r, "help_requested", int) == 1)
        att = median_iqr([num(r, "attempts", int) for r in rs])[0]
        task_rows.append({
            "id": f"U{tid}", "name": name, "n": n, "success": k, "rate": round(100.0 * k / n, 1),
            "ci": ci, "t_med": med_t, "t_iqr": iqr_t,
            "ui": k_ui, "help": k_help, "attempts": att,
        })

    # ---- questionnaires
    sus = [s for s in (sus_score(r) for r in survey) if s is not None]
    um = [s for s in (umux(r) for r in survey) if s is not None]
    tx = [s for s in (tlx(r) for r in survey) if s is not None]
    q = lambda v: (None, None) if len(v) < 2 else (
        round(statistics.median(v), 1), [round(x, 1) for x in statistics.quantiles(v, n=4, method="inclusive")][::2])
    sus_med, sus_iqr = q(sus)
    um_med, um_iqr = q(um)
    tx_med, tx_iqr = q(tx)
    n_part = len({r.get("participant") for r in survey} or {0}) - (1 if "" in {r.get("participant") for r in survey} else 0)
    n_part = max(n_part, len(survey))
    pilot = n_part <= 10

    # ---- LaTeX
    scale_note = ("; pilot sample, reported as a pilot" if pilot else
                  "; 95\\% Wilson intervals")
    L = ["% GENERATED by usability_report.py - do not edit by hand.",
         "\\begin{table}[t]", "\\centering",
         f"\\caption{{Task-level usability performance "
         f"(n\\,=\\,{n_part} participants{scale_note}).}}",
         "\\label{tab:usability}", "\\small",
         "\\begin{tabular}{llllll}", "\\toprule",
         "Task & Content & Done & Rate & 95\\% CI & Time \\\\",
         "\\midrule"]
    for r in task_rows:
        ci = f"[{r['ci'][0]:.1f},\\,{r['ci'][1]:.1f}]" if r["ci"] else "--"
        t = f"{r['t_med']:.0f}\\,s" if r["t_med"] is not None else "--"
        L.append(f"  {r['id']} & {r['name'][:34]} & {r['success']}/{r['n']} & "
                 f"{r['rate']:.0f}\\,\\% & {ci} & {t} \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table}", "",
          "\\begin{table}[t]", "\\centering",
          "\\caption{Self-reported measures after the session. Medians and interquartile "
          "ranges are used because the sample is small and the scales are ordinal.}",
          "\\label{tab:usability-q}", "\\begin{tabular}{lrrr}", "\\toprule",
          "Instrument & Median & IQR & $n$ \\\\", "\\midrule"]
    for nm, med, iqr, nn in (("SUS (0--100)", sus_med, sus_iqr, len(sus)),
                             ("UMUX-Lite (0--100)", um_med, um_iqr, len(um)),
                             ("NASA-TLX, unweighted (0--100)", tx_med, tx_iqr, len(tx))):
        L.append(f"  {nm} & " + (f"{med:.1f}" if med is not None else "--") + " & "
                 + (f"[{iqr[0]:.1f},\\,{iqr[1]:.1f}]" if iqr else "--") + f" & {nn} \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]

    a.outdir.mkdir(parents=True, exist_ok=True)
    (a.outdir / "usability.tex").write_text("\n".join(L) + "\n", encoding="utf-8")

    caveats = (" This is a pilot: with %d participants, task-level rates are indicative and "
               "not powered for a between-group comparison." % n_part) if pilot else ""
    sentences = []
    for r in task_rows:
        ci = f" [\\emph{{{r['ci'][0]:.1f}}}, \\emph{{{r['ci'][1]:.1f}}}]" if r["ci"] else ""
        t = f"; median completion time \\emph{{{r['t_med']:.0f}}}\\,s" if r["t_med"] is not None else ""
        sentences.append(f"Task {r['id']} ({r['name']}) was completed by {r['success']} of {r['n']} "
                         f"participants ({r['rate']:.0f}\\%{ci}){t}.")
    if sus_med is not None:
        sentences.append(f"Mean-level usability was {sus_med:.1f} on the SUS (IQR "
                         f"[{sus_iqr[0]:.1f}, {sus_iqr[1]:.1f}] , n\\,=\\,{len(sus)})"
                         if sus_iqr else f"Median SUS was {sus_med:.1f} (n\\,=\\,{len(sus)}).")
    if um_med is not None:
        sentences.append(f"UMUX-Lite gave {um_med:.1f} of 100.")
    if tx_med is not None:
        sentences.append(f"Reported workload (NASA-TLX, unweighted) was {tx_med:.1f} of 100.")
    md = ["# Usability numbers (paste-ready)", "",
          f"Participants: {n_part}. Tasks recorded: {len(tasks)}. SUS: {len(sus)}, "
          f"UMUX-Lite: {len(um)}, TLX: {len(tx)}.", "",
          ("**Pilot-scale caution:** " + caveats.strip()) if caveats else "",
          "", "## Sentences for the manuscript", ""] + [f"- {s}" for s in sentences]
    (a.outdir / "usability_numbers.md").write_text("\n".join(x for x in md if x is not None) + "\n",
                                                   encoding="utf-8")
    print(json.dumps({"participants": n_part, "tasks": len(task_rows), "pilot": pilot,
                      "sus_median": sus_med, "umux_median": um_med, "tlx_median": tx_med}, indent=2))
    print(f"wrote {a.outdir/'usability.tex'} and {a.outdir/'usability_numbers.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""meter_report.py — per-leg metrics JSONs -> a LaTeX table and paste-ready prose.

    analysis/meter_report.py runs/B1-idle-baseline_1/metrics.json runs/B2-*_1/metrics.json \
        --capacity-mah 4600 --outdir results

Reads what parse_leg.py wrote (one metrics.json per repetition). Two rules:
 * Nothing is printed as a number unless a capture produced it. Missing -> "n/m", and the
   prose line is dropped rather than softened into a vague claim.
 * Across repetitions we report the median and the observed range (n=3 by protocol), never a
   mean with two decimals, which would dress up three samples as precision.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

NF = "n/m"
LEGS = ["B1", "B2", "B3", "B4", "B5", "B6"]
LEG_NAME = {
    "B1": "Idle baseline: screen off, meter app stopped",
    "B2": "Sensing active, screen off (deployment case)",
    "B3": "Sensing active, screen on at 40\\,\\% brightness",
    "B4": "Two-handset transit/mesh session, screen off except unlocks",
    "B5": "Forced Doze with sensing enabled (\\texttt{deviceidle force-idle})",
    "B6": "Battery saver on, sensing enabled",
}
LEG_Q = {
    "B1": "floor of this handset at these settings",
    "B2": "background drain when nobody is looking at the phone",
    "B3": "cost of the operator view",
    "B4": "multi-node configuration",
    "B5": "whether the duty cycle survives deep idle",
    "B6": "what a normal user's settings do to coverage",
}

# (label, path in metrics.json, decimals, unit suffix)
FIELDS = [
    ("soc", ("soc", "soc_pct_per_h"), 2, " \\%/h"),
    ("cur", ("current", "mA_discharge"), 1, " \\,mA"),
    ("scans_req", ("cadence", "per_hour", "ble_scan_starts"), 0, ""),
    ("scans_res", ("cadence", "per_hour", "ble_results"), 0, ""),
    ("deliv", ("cadence", "delivered_per_start"), 2, ""),
    ("epch", ("cadence", "per_hour", "epochs_completed"), 0, ""),
    ("epcr", ("cadence", "epoch_completion_ratio"), 3, ""),
    ("wratio", ("cadence", "wifi_startscan_accepted_ratio"), 3, ""),
    ("gap", ("events", "epoch_gap_s", "median"), 1, ""),
    ("store", ("storage", "bytes_growth_per_hour"), 0, ""),
    ("mob", ("storage", "mobile_bytes_total"), 0, ""),
]


def dig(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur or cur[k] is None:
            return None
        cur = cur[k]
    return cur if isinstance(cur, (int, float)) else None


def agg(reps, *keys):
    vals = [v for v in (dig(r, *keys) for r in reps) if isinstance(v, (int, float))]
    if not vals:
        return None, None
    if len(vals) == 1:
        return vals[0], None
    return statistics.median(vals), [min(vals), max(vals)]


def fmt(v, spread, unit="", dec=2):
    if v is None:
        return NF
    s = f"{v:.{dec}f}{unit}"
    if spread is not None:
        s += f" [{spread[0]:.{dec}f}--{spread[1]:.{dec}f}]"
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics", nargs="+", type=Path, help="metrics.json files, one per repetition")
    ap.add_argument("--capacity-mah", type=float, default=None,
                    help="rated battery capacity, to turn %/h into mAh/h")
    ap.add_argument("--outdir", type=Path, default=Path("results"))
    a = ap.parse_args()

    reps = []
    for p in a.metrics:
        data = json.loads(p.read_text(encoding="utf-8"))
        for d in (data if isinstance(data, list) else [data]):
            d.setdefault("_file", p.name)
            reps.append(d)

    by_leg: dict[str, list[dict]] = {}
    for r in reps:
        m = re.match(r"^([A-Z]\d)", (r.get("leg") or "").upper())
        by_leg.setdefault(m.group(1) if m and m.group(1) in LEGS else "other", []).append(r)

    base = by_leg.get("B1", [])
    soc_base, _ = agg(base, "soc", "soc_pct_per_h") if base else (None, None)

    rows, prose = [], []
    for leg in LEGS:
        rs = by_leg.get(leg, [])
        if not rs:
            continue
        v = {f[0]: agg(rs, *f[1]) for f in FIELDS}
        soc, soc_sp = v["soc"][0], v["soc"][1]
        net = (round(soc - soc_base, 3), None) if (soc is not None and soc_base is not None) else (None, None)
        mah = (round(soc / 100.0 * a.capacity_mah, 2), None) if (soc is not None and a.capacity_mah) else (None, None)
        store, store_sp = v["store"]
        cells = {
            "n": len(rs),
            "soc": fmt(soc, soc_sp, " \\%/h"),
            "mah": fmt(mah[0], None, " \\,mAh/h", 2),
            "net": fmt(net[0], None, " \\pp", 2),
            "cur": fmt(v["cur"][0], v["cur"][1], " \\,mA", 1),
            "scans": fmt(v["scans_req"][0], None, "/h", 0),
            "res": fmt(v["scans_res"][0], None, "/h", 0),
            "epch": fmt(v["epch"][0], None, "/h", 0),
            "epcr": fmt(v["epcr"][0], None, "", 3),
            "wratio": fmt(v["wratio"][0], None, "", 3),
            "gap": fmt(v["gap"][0], None, "\\,s", 1),
            "store": fmt((store / 1024.0) if store is not None else None, None, " \\,kB/h", 1),
        }
        rows.append({"leg": leg, **cells})
        bits = []
        if soc is not None:
            bits.append("drain " + fmt(soc, soc_sp, r" \%/h"))
        if net[0] is not None:
            bits.append(f"{net[0]:+.2f}\\,pp against the idle baseline")
        if v["cur"][0] is not None:
            bits.append(f"{v['cur'][0]:.1f}\\,mA mean discharge current")
        if v["scans_req"][0] is not None:
            bits.append(f"{v['scans_req'][0]:.0f} scan bursts/h and "
                        f"{v['scans_res'][0]:.0f} result batches/h "
                        f"({fmt(v['deliv'][0], None, '', 2)} per burst)")
        if v["epch"][0] is not None:
            epc = (f" at {v['epcr'][0]:.3f} of attempted" if v["epcr"][0] is not None else "")
            bits.append(f"{v['epch'][0]:.0f} epochs completed/h{epc}")
        if v["wratio"][0] is not None:
            bits.append(f"active Wi-Fi scan requests honoured {v['wratio'][0]:.3f} of the time")
        if store is not None:
            bits.append(f"log storage grew {store/1024.0:.1f}\\,kB/h")
        if v["mob"][0] is not None:
            bits.append(f"mobile traffic {v['mob'][0]:.0f}\\,B for the whole leg")
        prose.append(f"**{leg}** ({LEG_Q[leg]}): " + "; ".join(bits) + ".")

    a.outdir.mkdir(parents=True, exist_ok=True)
    tex = ["% GENERATED by analysis/meter_report.py - do not edit by hand.",
           "% n/m means the quantity was not present in the capture (see gaps[] in metrics.json).",
           "\\begin{table*}[t]", "\\centering",
           "\\caption{Background-operation cost per measurement leg. Values are medians over the "
           "repetitions, with the observed range in brackets; drain is percent of rated capacity per "
           "hour with the screen off. \\texttt{n/m} marks a quantity the capture did not yield.}",
           "\\label{tab:cost}", "\\small",
           "\\begin{tabular}{llrrrrrrrrrr}", "\\toprule",
           "Leg & $n$ & Drain & mAh/h & vs.\\ B1 & Current & Bursts/h & Results/h & Epochs/h "
           "& Compl.\\ & Gap & Store \\\\", "\\midrule"]
    for r in rows:
        tex.append("  {leg} & {n} & {soc} & {mah} & {net} & {cur} & {scans} & {res} & {epch} & "
                   "{epcr} & {gap} & {store} \\\\".format(**r))
    if not rows:
        tex.append("  \\multicolumn{12}{c}{No leg directories analysed yet.} \\\\")
    tex += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (a.outdir / "measurements.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")

    md = ["# Measured numbers (paste-ready)", "",
          "Generated by `analysis/meter_report.py`. `n/m` = not measured.",
          "**No value below is estimated, imputed, or taken from the repository's simulation "
          "harness.**", "",
          f"Capacity used for mAh/h: {a.capacity_mah if a.capacity_mah else 'not supplied (mAh/h = n/m)'}.",
          "", "## Legs", ""]
    md += prose or ["- no legs analysed yet"]
    md += ["", "## Sentences for the manuscript", "",
           "Use only sentences whose numbers are present; delete the rest rather than hedging.", ""]
    if soc_base is not None:
        md.append("- With sensing active and the display off, the handset lost \\emph{<B2 drain>} of "
                  "battery per hour against \\emph{<B1 drain>} in the idle baseline "
                  "(Table~\\ref{tab:cost}); the same configuration with the operator view open cost "
                  "\\emph{<B3 drain>}.")
    md.append("- Background scheduling is not cosmetic: under forced Doze the meter completed "
              "\\emph{<B5 epochs/h>} of \\emph{<B2 epochs/h>} sensing epochs, and \\emph{<n>} of the "
              "epoch gaps exceeded twice the nominal interval.")
    md.append("- The meter wrote \\emph{<kB/h>} of session log per hour and generated "
              "\\emph{<B>} bytes of mobile traffic over the leg, which is the quantitative form of "
              "the claim that observation stays on the handset.")
    md.append("")
    (a.outdir / "numbers.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"wrote {a.outdir/'measurements.tex'} and {a.outdir/'numbers.md'}")
    print("legs with data: " + (", ".join(f"{r['leg']}(n={r['n']})" for r in rows) or "none"))
    for r in rows:
        print(f"  {r['leg']}: drain {r['soc']} | net {r['net']} | cur {r['cur']} | "
              f"bursts {r['scans']} | epochs {r['epch']} | store {r['store']}")
    if "other" in by_leg:
        print(f"  (ignored {len(by_leg['other'])} file(s) whose leg name matched none of B1-B6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

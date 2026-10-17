#!/usr/bin/env python3
"""storage_delta.py - growth between two storage_net_snapshot.sh captures.

    analysis/storage_delta.py runs/B2-r1-before.txt runs/B2-r1-after.txt --minutes 30

Numbers come from the snapshot files only; anything a device did not report stays null.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

KEYS = ("du_files_bytes", "du_cache_bytes", "du_no_backup_bytes", "file_count")


def grab(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    txt = path.read_text(encoding="utf-8", errors="replace")
    for k in KEYS:
        m = re.search(rf"^{k}:\s*(-?\d+|unavailable)\s*$", txt, re.M)
        if m and m.group(1).isdigit():
            out[k] = int(m.group(1))
    # external files dir line from `du -sb`
    m = re.search(r"^(\d+)\s+/sdcard/Android/data/\S+/files\s*$", txt, re.M)
    if m:
        out["external_files_bytes"] = int(m.group(1))
    m = re.search(r"^level: (\d+)", txt, re.M)
    if m:
        out["soc_level"] = int(m.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--minutes", type=float, default=None, help="leg duration, for per-hour rates")
    a = ap.parse_args()
    b, aft = grab(a.before), grab(a.after)
    if not b or not aft:
        print(json.dumps({"error": "one of the snapshots has no numeric lines - re-run the capture"}, indent=2))
        return 1
    dur_h = (a.minutes / 60.0) if a.minutes else None
    res = {}
    for k in sorted(set(b) | set(aft)):
        vb, va = b.get(k), aft.get(k)
        if vb is None or va is None:
            res[k] = {"before": vb, "after": va, "delta": None, "note": "not reported by the device"}
            continue
        d = {"before": vb, "after": va, "delta": va - vb}
        if k != "soc_level" and dur_h:
            d["delta_per_hour"] = round((va - vb) / dur_h, 1)
        res[k] = d
    tot_b = sum(v for k, v in b.items() if k.startswith("du_")) + b.get("external_files_bytes", 0)
    tot_a = sum(v for k, v in aft.items() if k.startswith("du_")) + aft.get("external_files_bytes", 0)
    res["total_app_bytes"] = {"before": tot_b, "after": tot_a, "delta": tot_a - tot_b}
    if dur_h:
        res["total_app_bytes"]["delta_per_hour"] = round((tot_a - tot_b) / dur_h, 1)
        res["total_app_bytes"]["per_month_at_12min_per_day"] = round((tot_a - tot_b) / dur_h * 0.2 * 30, 1)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

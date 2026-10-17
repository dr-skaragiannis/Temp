#!/usr/bin/env python3
"""SYNTHETIC FIXTURE GENERATOR - not measurement data.

Builds tests/fixture/<leg>/ directories with exactly the file names and column headers that
scripts/run_leg.sh and the app-side probes produce, so the analysers can be exercised without a
handset. Every number here is a round fake; none of it may reach the manuscript. Run
tests/run_tests.sh, which asserts the analysers recover the values this file put in.
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixture"
random.seed(20261005)

# the ground truth the tests assert against
TRUTH = {
    "leg_duration_s": 1200.0,
    "soc_start": 100, "soc_end": 98, "scale": 100,
    "expected_pct_per_h": round(2.0 / (1200.0 / 3600.0), 3),      # 6.0
    "mean_current_ma": -320.0,
    "ble_starts_total": 200, "ble_results_total": 1040,
    "wifi_tried": 40, "wifi_accepted": 0,
    "epochs_attempted": 80, "epochs_completed": 68,
    "epoch_gap_s": 15.0,
    "storage_growth_bytes": 188_000,
    "uid_bytes_total": 0,
    "doze_windows": 5,
}


def battery_rows(n=241, start=100, end=98, scale=100, current_ma=-320.0):
    out = []
    for i in range(n):
        t = i * 5.0
        frac = i / (n - 1)
        lvl = int(round(start + (end - start) * frac))
        cur = current_ma * 1000.0 * (1.0 + 0.05 * math.sin(i / 7.0))
        out.append({"elapsed_s": f"{t:.1f}", "level": lvl, "scale": scale,
                    "voltage_duV": int(3850 + 40 * math.sin(i / 40.0)) * 1000,
                    "temperature_dC": 296 + (i % 3), "status": 4, "plugged": 0,
                    "current_uA": int(cur), "device_idle": 1 if i >= n - TRUTH["doze_windows"] * 12 else 0,
                    "light_idle": 0, "screen": "off"})
    return out


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def gen_leg(name: str, with_app_logs: bool = True) -> Path:
    leg = FIX / name
    if leg.exists():
        shutil.rmtree(leg)
    n = int(TRUTH["leg_duration_s"] / 5) + 1
    rows = battery_rows(n=n)
    # shell sampler: different column names for the same quantities
    shell = []
    for r in rows:
        e = float(r["elapsed_s"])
        d = {k: v for k, v in r.items() if k not in ("device_idle", "screen")}
        d["idle_state"] = 4 if r["device_idle"] == 1 else 0
        d["screen"] = "Asleep" if r["screen"] == "off" else "Awake"
        d["timestamp"] = "2026-10-05T%02d:%02d:%02d" % (12 + int(e // 3600), int(e // 60) % 60, int(e % 60))
        shell.append(d)
    write_csv(leg / "battery.csv", shell)

    st = []
    step = TRUTH["storage_growth_bytes"] // 20
    for i in range(21):
        t = i * 60.0
        st.append({"elapsed_s": f"{t:.1f}", "files_bytes": 512_000 + step * i, "cache_bytes": 40_000,
                   "nobackup_bytes": 0, "session_files": 3 + i, "exported_bytes": 0})
    write_csv(leg / "storage.csv", st)

    if with_app_logs:
        write_csv(leg / "app-logs" / "battery-B2.csv", rows)
        cad = []
        for i in range(20):
            cad.append({"window_start_s": i * 60.0, "ble_scan_starts": 10, "ble_results": 52,
                        "ble_links": 3, "wifi_polls": 2, "wifi_polls_fresh": 1,
                        "wifi_startscan_tried": 2, "wifi_startscan_accepted": 0,
                        "epochs_attempted": 4, "epochs_completed": int(68 / 20) + (1 if i < 8 else 0),
                        "screen_on": 0, "device_idle": 1 if i >= 15 else 0, "light_idle": 0})
        write_csv(leg / "app-logs" / "cadence-B2.csv", cad)
        stg = []
        for i in range(21):
            stg.append({"elapsed_s": i * 60.0, "files_bytes": 512_000 + step * i, "cache_bytes": 40_000,
                        "nobackup_bytes": 0, "log_files": 3 + i, "log_bytes_max": 24_000,
                        "log_bytes_total": 512_000 + step * i,
                        "traffic": f"mobile_rx={1000+i};mobile_tx={2000+i};uid_rx={1000+i};uid_tx={1000+i}"})
        write_csv(leg / "app-logs" / "storage-B2.csv", stg)
        ev = []
        t = 0.0
        for i in range(int(TRUTH["leg_duration_s"] / TRUTH["epoch_gap_s"])):
            ev.append({"elapsed_s": round(t, 1), "event": "epoch_attempted"})
            t += TRUTH["epoch_gap_s"]
        ev.insert(5, {"elapsed_s": 75.0, "event": "screen_off"})
        write_csv(leg / "app-logs" / "events-B2.csv", ev)

    (leg / "batterystats-after.txt").write_text("""Battery stats for u0a234/com.example
  Time on battery: +20m 3s 999ms running, 0s dozing
  Estimated power use (mAh):
    Capacity: 4600, Computed drain: 46.2, actual drain: 45.9
    Screen: 0.0
    App: 6.1
    Bluetooth: 1.9
    Wifi: 3.4
    Uid 10234 (org.meshcrowd.meter): 4.81
  Wake lock u0a234/MeterService: +1m 12s 345ms (41 times) partial
  Wake lock u0a234/WifiManager: +14.500ms (2 times) partial
""", encoding="utf-8")
    (leg / "deviceidle-after.txt").write_text(
        "  mDeviceIdleMode=4  mLightDeviceIdleMode=0\n  step=IDLE\nReason: Alarm 12\nReason: Alarm 3\n",
        encoding="utf-8")
    (leg / "netstats-before.txt").write_text("  10234: rxBytes=1000 txBytes=2000\n", encoding="utf-8")
    (leg / "netstats-after.txt").write_text("  10234: rxBytes=2021 txBytes=3021\n", encoding="utf-8")
    (leg / "SYNTHETIC.txt").write_text(
        "SYNTHETIC FIXTURE - generated by tests/make_fixture.py.\n"
        "Not a measurement. Never quote anything in this directory in the paper.\n", encoding="utf-8")
    return leg


def gen_usability():
    u = FIX / "usability"
    u.mkdir(parents=True, exist_ok=True)
    hdr = ["participant", "task_id", "task_name", "attempts", "success", "time_s", "correct_ui", "help_requested", "notes"]
    rows = []
    for p in range(1, 9):
        for tid, ok, t in ((1, 1, 40), (2, 1, 12), (3, 1, 25), (4, 0, 90), (5, 1, 30),
                           (6, 1, 44), (7, 0, 120), (8, 1, 18)):
            if tid == 4 and p > 6:
                ok = 1
            rows.append({"participant": f"P{p:02d}", "task_id": tid, "task_name": f"task{tid}",
                         "attempts": 1 if ok else 2, "success": ok, "time_s": t + p,
                         "correct_ui": ok, "help_requested": 1 if (tid + p) % 9 == 0 else 0, "notes": ""})
    write_csv(u / "usability_tasks.csv", rows)
    shdr = (["participant", "age", "gender", "handset", "android", "prior_experience_1to5"]
            + [f"Q{i}" for i in range(1, 11)] + ["U1", "U2"]
            + ["mental", "physical", "temporal", "performance", "effort", "frustration"]
            + [f"w_{k}" for k in ("mental", "physical", "temporal", "performance", "effort", "frustration")]
            + ["comment"])
    srows = []
    for p in range(1, 9):
        q = [4] * 10 if p % 2 == 0 else [3, 4, 3, 4, 3, 4, 3, 4, 3, 4]
        srows.append({"participant": f"P{p:02d}", "age": 30 + p, "gender": "f" if p % 2 else "m",
                      "handset": "Pixel 6a", "android": 14, "prior_experience_1to5": 3,
                      **{f"Q{i}": q[i - 1] for i in range(1, 11)}, "U1": 4, "U2": 2,
                      "mental": 40, "physical": 20, "temporal": 35, "performance": 65,
                      "effort": 50, "frustration": 30,
                      **{f"w_{k}": 15 for k in ("mental", "physical", "temporal", "performance", "effort", "frustration")},
                      "comment": ""})
    write_csv(u / "usability_survey.csv", srows)
    return u


if __name__ == "__main__":
    FIX.mkdir(parents=True, exist_ok=True)
    (FIX / "SYNTHETIC-FIXTURE.txt").write_text(
        "Everything under this directory is generated by tests/make_fixture.py for parser tests.\n"
        "It is NOT measurement data and must not be cited, pasted, or plotted.\n", encoding="utf-8")
    good = gen_leg("B2-sensing-screen-off_1")
    broken = gen_leg("B5-forced-doze_1", with_app_logs=False)
    us = gen_usability()
    print(json.dumps({"truth": TRUTH, "legs": [good.name, broken.name],
                      "usability": str(us.relative_to(HERE))}, indent=2))

#!/usr/bin/env python3
"""Turn one measurement leg directory into a metrics JSON.

Expected layout, as written by scripts/run_leg.sh:

    <leg>/battery.csv                     shell 5 s sampler  (columns below)
    <leg>/storage.csv                     shell 60 s sampler
    <leg>/batterystats-before.txt         dumpsys (cumulative, pre-reset)
    <leg>/batterystats-after.txt          dumpsys, human readable
    <leg>/batterystats-checkin.txt        kept for manual work, not parsed here
    <leg>/netstats-{before,after}.txt     per-UID counters
    <leg>/deviceidle-after.txt
    <leg>/app-logs/battery-<label>.csv    app-side, authoritative if present
    <leg>/app-logs/cadence-<label>.csv    scans/epochs actually obtained
    <leg>/app-logs/storage-<label>.csv    bytes + TrafficStats
    <leg>/app-logs/events-<label>.csv     service lifecycle and startScan outcomes

Header contracts:
  app battery : elapsed_s,level,scale,voltage_duV,temperature_dC,status,plugged,
                current_uA,device_idle,light_idle,screen
  shell battery: ...,current_uA,idle_state,light_idle,screen,timestamp
  cadence     : window_start_s,ble_scan_starts,ble_results,ble_links,wifi_polls,
                wifi_polls_fresh,wifi_startscan_tried,wifi_startscan_accepted,
                epochs_attempted,epochs_completed,screen_on,device_idle,light_idle
  storage     : elapsed_s,files_bytes,cache_bytes,nobackup_bytes,log_files,
                log_bytes_max,log_bytes_total,traffic   (traffic is ';'-joined)

Rule: a quantity that cannot be extracted is null, with a note. Never zero.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from pathlib import Path

# ------------------------------------------------------------------ utilities


def _read_text(path: Path) -> str:
    """Decode a dump, honouring a byte-order mark.

    Shell-captured dumps are not reliably UTF-8. Windows PowerShell 5.1 writes
    `cmd > file` as UTF-16LE (BOM FF FE), and `Out-File -Encoding utf8` writes a
    UTF-8 BOM. Decoding either of those as plain UTF-8 yields NUL-interleaved
    text, so every section-header match silently misses and the leg reports a
    `batterystats` gap even though the data is present. Sniff the BOM first, and
    fall back to a UTF-16 read when NUL bytes indicate a mark-less UTF-16 file.
    """
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe"):
        return raw[2:].decode("utf-16-le", errors="replace")
    if raw.startswith(b"\xfe\xff"):
        return raw[2:].decode("utf-16-be", errors="replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    txt = raw.decode("utf-8", errors="replace")
    if txt.count("\x00") > len(txt) // 4:
        return raw.decode("utf-16", errors="replace").lstrip("\ufeff")
    return txt


def _num(s):
    s = ("" if s is None else str(s)).strip()
    if s in ("", "-", "?", "NA", "null", "N/A"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _int(s):
    v = _num(s)
    return None if v is None else int(v)


def read_csv_rows(path: Path) -> list[dict]:
    if not path or not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        return [r for r in csv.DictReader(fh)]


def find_first(root: Path, patterns: list[str]) -> Path | None:
    for pat in patterns:
        hits = sorted(root.glob(pat))
        if hits:
            return hits[0]
    return None


# ---------------------------------------------------------------- battery side


def normalise_battery(rows: list[dict], source: str) -> list[dict]:
    """Map either sampler onto one shape.

    charging: an external supply is connected. `plugged` is authoritative, because
      status alone is ambiguous: 2 is always CHARGING, but several OEM builds report
      status=3 (which upstream defines as BATTERY_STATUS_FULL) while the cell is
      actually discharging with nothing attached. Measured on a motorola edge 60 pro,
      Android 16: unplugged discharging samples arrive as status=3, plugged=0, with
      current_now negative. Keying on status alone discards the entire discharge
      window and reports `n_points: 0`, so unplugged wins and status is only a
      corroborating signal when `plugged` is unreadable.
    idle    : app side device_idle==1; shell side mState==4 (STATE_IDLE) or light==1
    screen  : app side on/off; shell side mWakefulness Awake/Dozing/Asleep
    """
    out = []
    for r in rows:
        t = _num(r.get("elapsed_s"))
        if t is None:
            continue
        plugged = _int(r.get("plugged"))
        status = _int(r.get("status"))
        if plugged is None:
            charging = status in (2, 3)
        else:
            charging = plugged != 0
        if "idle_state" in r:
            idle = (_int(r.get("idle_state")) == 4) or (_int(r.get("light_idle")) == 1)
        else:
            idle = (_int(r.get("device_idle")) == 1) or (_int(r.get("light_idle")) == 1)
        scr = (r.get("screen") or "").strip().lower()
        if scr in ("on", "awake"):
            screen_on = True
        elif scr in ("off", "asleep", "dozing"):
            screen_on = False
        else:
            screen_on = None
        lvl, scl = _num(r.get("level")), _num(r.get("scale")) or 100.0
        cur = _num(r.get("current_uA"))
        if cur is not None and cur < 0:
            cur = None if cur <= -2_000_000 else cur     # -999999-ish sentinels
        temp = _num(r.get("temperature_dC"))
        out.append({"t": t, "level": lvl, "scale": scl, "current_ua": cur,
                    "temp_dc": temp, "charging": charging, "idle": idle,
                    "screen_on": screen_on, "source": source})
    return out


def load_battery(leg: Path) -> tuple[list[dict], str | None]:
    app = find_first(leg / "app-logs", ["battery-*.csv", "**/battery-*.csv"])
    if app:
        rows = normalise_battery(read_csv_rows(app), "app")
        if len(rows) >= 3:
            return rows, app.name
    shell = leg / "battery.csv"
    rows = normalise_battery(read_csv_rows(shell), "shell")
    if len(rows) >= 3:
        return rows, "battery.csv"
    return [], None


def soc_metrics(pts: list[dict]) -> dict:
    """Percent-of-capacity per hour, unplugged samples only."""
    usable = [p for p in pts if p["level"] is not None and not p["charging"]]
    if len(usable) < 2:
        return {"soc_pct_per_h": None, "n_points": len(usable),
                "note": "fewer than two unplugged SOC samples - charger still connected?"}
    span_h = (usable[-1]["t"] - usable[0]["t"]) / 3600.0
    if span_h <= 0:
        return {"soc_pct_per_h": None, "n_points": len(usable), "note": "zero-length window"}
    delta = (usable[0]["level"] - usable[-1]["level"]) / usable[0]["scale"] * 100.0
    if delta < 0:
        return {"soc_pct_per_h": None, "n_points": len(usable),
                "note": "SOC rose during the leg (charging or calibration jump)"}
    # SOC is an integer: the useful caveat is how much one step moves the answer,
    # not the per-sample rate (which is 0 between steps and huge at a step).
    steps = sum(1 for a, b in zip(usable, usable[1:]) if b["level"] != a["level"])
    per_step = (1.0 / usable[0]["scale"] * 100.0) / span_h if span_h > 0 else None
    rate = delta / span_h
    return {
        "soc_pct_per_h": round(rate, 3),
        "span_h": round(span_h, 4),
        "soc_delta_pct": round(delta, 3),
        "soc_steps_observed": steps,
        "quantisation_pct_per_h_per_step": round(per_step, 3) if per_step is not None else None,
        "minutes_needed_for_1pp_resolution": round(60.0 / rate, 1) if rate > 0 else None,
        "n_points": len(usable),
        "resolution_note": ("below the quantisation floor - extend the leg"
                            if per_step is not None and rate < 2 * per_step else "ok"),
    }


def current_metrics(pts: list[dict]) -> dict:
    """CURRENT_NOW, only if the HAL exposes it; the drain in mA needs no SOC model."""
    neg = [p["current_ua"] for p in pts if p["current_ua"] is not None and p["current_ua"] < 0 and not p["charging"]]
    if len(neg) < 3:
        return {"mA_discharge": None, "mAh_total": None,
                "note": "power_supply/current_now unavailable or unreadable from the app on this build"}
    mean_ua = statistics.mean(neg)
    span_s = pts[-1]["t"] - pts[0]["t"]
    return {
        "mA_discharge": round(-mean_ua / 1000.0, 2),
        "mA_iqr": ([round(x / 1000.0, 2) for x in statistics.quantiles([-c for c in neg],
                                                                n=4, method="inclusive")][::2]
                    if len(neg) >= 4 else None),
        "mAh_total": round(-mean_ua / 1000.0 * (span_s / 3600.0), 3),
        "n": len(neg),
    }


def split_metrics(pts: list[dict]) -> dict:
    def grp(f):
        return [p for p in pts if f(p)]

    def rate(sub):
        return soc_metrics(sub).get("soc_pct_per_h")

    temps = [p["temp_dc"] for p in pts if p["temp_dc"] is not None]
    return {
        "n_total": len(pts),
        "n_screen_on": len(grp(lambda p: p["screen_on"] is True)),
        "n_screen_off": len(grp(lambda p: p["screen_on"] is False)),
        "n_idle": len(grp(lambda p: p["idle"])),
        "soc_pct_per_h_screen_on": rate(grp(lambda p: p["screen_on"] is True)),
        "soc_pct_per_h_screen_off": rate(grp(lambda p: p["screen_on"] is False)),
        "soc_pct_per_h_idle": rate(grp(lambda p: p["idle"])),
        "temp_c_mean": round(statistics.mean(temps) / 10.0, 2) if temps else None,
        "temp_c_range": [round(min(temps) / 10.0, 1), round(max(temps) / 10.0, 1)] if temps else None,
    }


# ---------------------------------------------------------------- cadence side


def load_cadence(leg: Path) -> dict:
    p = find_first(leg / "app-logs", ["cadence-*.csv", "**/cadence-*.csv"])
    if not p:
        return {"note": "no cadence CSV - the app-side logger did not run, so scans/hour is not measured"}
    rows = read_csv_rows(p)
    if not rows:
        return {"note": f"{p.name} is empty"}
    cols = ("ble_scan_starts", "ble_results", "ble_links", "wifi_polls", "wifi_polls_fresh",
            "wifi_startscan_tried", "wifi_startscan_accepted", "epochs_attempted", "epochs_completed")
    tot = {c: int(sum(v for v in (_int(r.get(c)) for r in rows) if v is not None)) for c in cols}
    span_s = (_num(rows[-1].get("window_start_s")) or 0) - (_num(rows[0].get("window_start_s")) or 0) + 60.0
    per_h = {c: round(v / (span_s / 3600.0), 2) if span_s > 0 else None for c, v in tot.items()}
    on = [r for r in rows if _int(r.get("screen_on")) == 1]
    off = [r for r in rows if _int(r.get("screen_on")) != 1]
    idle = [r for r in rows if _int(r.get("device_idle")) == 1]

    def starts(rs):
        return int(sum(v for v in (_int(r.get("ble_scan_starts")) for r in rs) if v is not None))

    def res(rs):
        return int(sum(v for v in (_int(r.get("ble_results")) for r in rs) if v is not None))

    nwin = max(len(rows), 1)
    return {
        "windows": len(rows),
        "span_s": round(span_s, 1),
        "totals": tot,
        "per_hour": per_h,
        "starts_requested": tot["ble_scan_starts"],
        "results_delivered": tot["ble_results"],
        "delivered_per_start": round(tot["ble_results"] / tot["ble_scan_starts"], 3) if tot["ble_scan_starts"] else None,
        "wifi_startscan_accepted_ratio": (round(tot["wifi_startscan_accepted"] / tot["wifi_startscan_tried"], 4)
                                          if tot["wifi_startscan_tried"] else None),
        "epoch_completion_ratio": (round(tot["epochs_completed"] / tot["epochs_attempted"], 4)
                                   if tot["epochs_attempted"] else None),
        "screen_on_starts_per_window": round(starts(on) / len(on), 3) if on else None,
        "screen_off_starts_per_window": round(starts(off) / len(off), 3) if off else None,
        "results_per_start_screen_on": round(res(on) / starts(on), 3) if on and starts(on) else None,
        "results_per_start_screen_off": round(res(off) / starts(off), 3) if off and starts(off) else None,
        "results_per_start_idle": round(res(idle) / starts(idle), 3) if idle and starts(idle) else None,
        "idle_windows": len(idle),
        "source": p.name,
    }


def load_events(leg: Path, epoch_nominal_s: float = 15.0) -> dict:
    """Event markers give us the timing the window aggregates cannot: epoch gaps."""
    p = find_first(leg / "app-logs", ["events-*.csv", "**/events-*.csv"])
    if not p:
        return {"note": "no events CSV"}
    rows = read_csv_rows(p)
    counts, times = {}, []
    for r in rows:
        vals = [v for v in r.values()]
        name, t = "", None
        for v in vals:
            x = (v or "").strip()
            if x and _num(x) is None:
                name = x
            elif _num(x) is not None and t is None:
                t = _num(x)
        if name:
            counts[name] = counts.get(name, 0) + 1
            if name == "epoch_attempted" and t is not None:
                times.append(t)
    out: dict = {"events": counts or None, "source": p.name}
    gaps = [round(b - a, 2) for a, b in zip(times, times[1:]) if b > a]
    gaps = [g for g in gaps if g < 3600]
    if len(gaps) >= 3:
        gs = sorted(gaps)
        out["epoch_gap_s"] = {
            "median": round(statistics.median(gs), 2),
            "p95": round(gs[max(0, min(len(gs) - 1, round(0.95 * (len(gs) - 1))))], 2),
            "max": round(gs[-1], 2),
            "n_gaps": len(gs),
            "missed_epochs_gt_2x_nominal": sum(1 for g in gs if g > 2 * epoch_nominal_s),
            "nominal_s": epoch_nominal_s,
        }
    else:
        out["epoch_gap_s"] = None
        out["gap_note"] = "fewer than three epoch_attempted markers - gaps not reported"
    return out


# ---------------------------------------------------------------- storage side


def load_storage(leg: Path) -> dict:
    p = find_first(leg / "app-logs", ["storage-*.csv", "**/storage-*.csv"])
    rows = read_csv_rows(p) if p else []
    src = p.name if p else None
    if not rows:
        rows, src = read_csv_rows(leg / "storage.csv"), "storage.csv"
    if not rows:
        return {"note": "no storage CSV - byte growth is not measured"}

    def col(name):
        return [v for v in (_num(r.get(name)) for r in rows) if v is not None]

    span_s = (_num(rows[-1].get("elapsed_s")) or 0) - (_num(rows[0].get("elapsed_s")) or 0)
    per = {}
    for c in ("files_bytes", "cache_bytes", "nobackup_bytes", "log_bytes_total", "session_files"):
        v = col(c)
        if v:
            per[c] = int(v[-1])
    tot_first = sum((_num(rows[0].get(c)) or 0) for c in ("files_bytes", "cache_bytes", "nobackup_bytes"))
    tot_last = sum((_num(rows[-1].get(c)) or 0) for c in ("files_bytes", "cache_bytes", "nobackup_bytes"))
    out = {
        "source": src,
        "n_rows": len(rows),
        "bytes_final": {k: v for k, v in per.items() if k != "session_files"},
        "log_files_final": int(_num(rows[-1].get("log_files")) or _num(rows[-1].get("session_files")) or 0),
        "bytes_growth": int(tot_last - tot_first),
        "bytes_growth_per_hour": round((tot_last - tot_first) / (span_s / 3600.0), 1) if span_s > 30 else None,
        "max_log_bytes": int(max(col("log_bytes_max") or [0])),
    }
    if span_s <= 30:
        out["note"] = "storage window shorter than 30 s - growth per hour not reported"
    tr = {}
    for key in ("mobile_rx", "mobile_tx", "uid_rx", "uid_tx"):
        vals = []
        for r in rows:
            blob = r.get("traffic") or ""
            for tok in blob.replace(",", ";").split(";"):
                if tok.startswith(key + "="):
                    v = _num(tok.split("=", 1)[1])
                    if v is not None and v >= 0:
                        vals.append(v)
        if vals:
            tr[key + "_delta"] = int(vals[-1] - vals[0])
    if tr:
        out["traffic"] = tr
        out["mobile_bytes_total"] = int((tr.get("mobile_rx_delta", 0)) + (tr.get("mobile_tx_delta", 0)))
        out["uid_bytes_total"] = int((tr.get("uid_rx_delta", 0)) + (tr.get("uid_tx_delta", 0)))
    else:
        out["traffic"] = None
        out["traffic_note"] = "TrafficStats not in this capture (shell sampler does not read them)"
    return out


# --------------------------------------------------- batterystats (best effort)

# Case-insensitive and tolerant of trailing columns: Android 16 prints
# "  UID 10492: 0.0 bg: 0.0" where older builds printed "  Uid 10492: 0.0".
# A case-sensitive `Uid \d+` match silently skips every UID line on this build,
# which surfaces only as a `batterystats` gap in the metrics.
RE_MAH = re.compile(r"^\s{2,}([A-Za-z][A-Za-z0-9 /_.-]{1,38}):\s*(-?\d+\.\d+)(?:\s|$)")
# Per-UID rows need their own pattern, tried before RE_MAH. Three shapes exist in
# the wild and this Android 16 build produces two of them at once:
#   "  Uid 10492: 0.5 bg: 0.5"      older builds, numeric uid, decimal total
#   "  UID 1000: 6.31 bg: 6.31"     this build, numeric uid, decimal total
#   "  UID u0a492: 156 fg: 2.65 ..." this build, name-form uid, INTEGER total
# RE_MAH alone misses the third (no decimal point) and mislabels the second
# ("uid 1000"), so the meter's own row is silently dropped and the leg reports a
# `batterystats` gap. Total is the first figure; fg/bg follow as named columns.
RE_UIDROW = re.compile(
    r"^\s{2,}UID\s+([A-Za-z0-9_]+)(?:\s*\([^)]*\))?:\s*([\d.]+)(?:\s|$)(.*)$",
    re.IGNORECASE)
RE_WAKE = re.compile(r"Wake lock\s+(\S+?):\s*\+?([0-9][0-9dhms. ]*?)\s*\((\d+) times\)")
RE_DUR = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")


def _uid_matches(name: str, uid: str | None) -> bool:
    """`u0a234` and `10234` are the same app: uid = user*100000 + 10000 + appId."""
    if not uid:
        return True
    if uid in name:
        return True
    m = re.search(r"u(\d+)a(\d+)", name)
    if m:
        return int(m.group(1)) * 100000 + 10000 + int(m.group(2)) == int(uid)
    return False


def parse_batterystats(path: Path, uid: str | None) -> dict:
    if not path or not path.exists():
        return {"note": "no human-readable batterystats dump in this leg"}
    txt = _read_text(path)
    out: dict = {}
    in_est, est, uid_split = False, {}, {}
    for ln in txt.splitlines():
        if "Estimated power use (mAh)" in ln:
            in_est = True
            continue
        if in_est:
            if ln.strip() and not ln.startswith(" "):
                break
            # UID rows first: they are a superset of the generic label form, and
            # this build's name-form rows (integer totals) would otherwise be
            # dropped or mis-keyed.
            mu = RE_UIDROW.match(ln)
            if mu:
                name = mu.group(1).strip().lower()
                key = f"uid {name}"
                est[key] = float(mu.group(2))
                tail = mu.group(3)
                fg = re.search(r"\bfg:\s*([\d.]+)", tail)
                bg = re.search(r"\bbg:\s*([\d.]+)", tail)
                if fg or bg:
                    uid_split[key] = {"fg_mah": float(fg.group(1)) if fg else None,
                                      "bg_mah": float(bg.group(1)) if bg else None}
                continue
            m = RE_MAH.match(ln)
            if m:
                est[m.group(1).strip().lower()] = float(m.group(2))
    out["estimated_mah_tree"] = est or None
    out["uid_fg_bg_mah"] = uid_split or None
    if uid and est:
        out["estimated_mah_for_uid"] = {k: v for k, v in est.items()
                                        if uid in k or _uid_matches(k, uid)} or None
    wakes = {}
    for m in RE_WAKE.finditer(txt):
        if not _uid_matches(m.group(1), uid):
            continue
        secs = 0.0
        for v, unit in RE_DUR.findall(m.group(2)):
            v = float(v)
            secs += v * 3600 if unit == "h" else v * 60 if unit == "m" else v / 1000 if unit == "ms" else v
        wakes[m.group(1)] = wakes.get(m.group(1), 0.0) + secs
    out["wake_lock_seconds"] = {k: round(v, 1) for k, v in sorted(wakes.items(), key=lambda x: -x[1])[:10]} or None
    m = re.search(r"Time on battery:\s*\+?([\dhms. +]+)", txt)
    if m:
        out["time_on_battery_raw"] = m.group(1).strip()
    # Two fields are optional refinements rather than required data, and their
    # absence must not mark the leg as gapped:
    #   uid_fg_bg_mah - builds that print one total per UID have no split to give.
    #   wake_lock_seconds - Android 16 dropped the "Wake lock <name>: +..." lines
    #     from `dumpsys batterystats` entirely (verified: zero occurrences on a
    #     motorola edge 60 pro). Nothing to parse is not a measurement gap.
    optional = {"uid_fg_bg_mah", "wake_lock_seconds"}
    miss = [k for k, v in out.items() if v is None and k not in optional]
    if miss:
        out["note"] = ("not present in this dump (OEM-specific formatting): " + ", ".join(miss)
                       + "; the drain figures above come from the sampler CSVs, not from this file")
    return out


def parse_netstats(before: Path, after: Path, uid: str | None) -> dict:
    """Netstats deltas, kept separate because the reset already isolates the leg."""
    def grab(path: Path) -> dict:
        if not path.exists():
            return {}
        txt = _read_text(path)
        res = {}
        for m in re.finditer(r"uid=(\d+)[^\n]*", txt):
            pass
        for m in re.finditer(r"^\s*(\d{4,6}):\s*(.*)$", txt, re.M):
            line = m.group(2)
            rx = re.search(r"rxBytes=(\d+)", line)
            tx = re.search(r"txBytes=(\d+)", line)
            if rx and tx and (uid is None or m.group(1) == uid):
                res[m.group(1)] = [int(rx.group(1)), int(tx.group(1))]
        return res
    b, a = grab(before), grab(after)
    if not a:
        return {"note": "netstats lines not recognised; use the app-side TrafficStats instead"}
    out = {"after": a}
    if b and set(a) == set(b):
        out["delta"] = {u: [a[u][0] - b[u][0], a[u][1] - b[u][1]] for u in a}
        out["delta_note"] = "rx,tx bytes over the window (batterystats/netstats were reset at start)"
    else:
        out["delta_note"] = "no matching before-snapshot; only the after counters are reported"
    return out


# --------------------------------------------------------------------- driver


def analyse(leg: Path, uid: str | None = None) -> dict:
    pts, bsrc = load_battery(leg)
    m = {
        "leg": leg.name,
        "battery_source": bsrc,
        "duration_min": round((pts[-1]["t"] - pts[0]["t"]) / 60.0, 2) if len(pts) > 1 else None,
        "soc": soc_metrics(pts) if pts else {"soc_pct_per_h": None, "note": "no battery CSV"},
        "current": current_metrics(pts) if pts else {"mA_discharge": None},
        "states": split_metrics(pts) if pts else {},
        "cadence": load_cadence(leg),
        "storage": load_storage(leg),
        "events": load_events(leg),
        "batterystats": parse_batterystats(leg / "batterystats-after.txt", uid),
        "netstats": parse_netstats(leg / "netstats-before.txt", leg / "netstats-after.txt", uid),
    }
    m["gaps"] = [k for k in ("soc", "current", "cadence", "storage", "batterystats")
                 if isinstance(m[k], dict) and m[k].get("note")]
    return m


def main() -> int:
    ap = argparse.ArgumentParser(description="leg directory -> metrics JSON")
    ap.add_argument("legs", nargs="+", type=Path)
    ap.add_argument("--uid", default=None, help="numeric Android UID, for the batterystats subtree")
    ap.add_argument("--out", type=Path, default=None, help="write JSON here as well (default <leg>/metrics.json)")
    a = ap.parse_args()
    allm = []
    for leg in a.legs:
        if not leg.is_dir():
            print(f"skip {leg}: not a directory", flush=True)
            continue
        m = analyse(leg, a.uid)
        dst = a.out if a.out and len(a.legs) == 1 else leg / "metrics.json"
        dst.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
        allm.append(m)
        print(f"{leg.name}: {m['duration_min']} min of samples -> {dst}")
        print(f"   drain {m['soc'].get('soc_pct_per_h')} %/h | current {m['current'].get('mA_discharge')} mA"
              f" | scans/h {m['cadence'].get('per_hour', {}).get('ble_scan_starts')}"
              f" | store {m['storage'].get('bytes_growth_per_hour')} B/h"
              f" | gaps {m['gaps'] or 'none'}", flush=True)
    if a.out and len(a.legs) > 1:
        a.out.write_text(json.dumps(allm, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

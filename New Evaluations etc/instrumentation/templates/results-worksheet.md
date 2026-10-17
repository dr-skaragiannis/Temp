# Results worksheet — fill this while the legs run, not afterwards

One row per leg repetition. Anything you leave blank here will come out of
`analysis/meter_report.py` as `n/m`, and the manuscript sentence that depends on it must then be
deleted, not softened. **Do not fill a cell from memory or from a second run of a different leg.**

## 0. Device card (fill once per handset)

| Field | Value | Where it came from |
|---|---|---|
| Model / codename | | `adb shell getprop ro.product.model` / `ro.product.device` |
| Android version / SDK | | `adb shell getprop ro.build.version.release` / `.sdk` |
| Build ID | | `ro.build.id` |
| Rated capacity (mAh) | | `adb shell dumpsys battery properties \| grep -i charge` or the spec sheet — say which |
| Battery health / cycle count | | `dumpsys batterystats \| grep -i "Health\|Cycle"` if the OEM exposes it |
| `current_now` readable? | yes / no | `adb shell cat /sys/class/power_supply/battery/current_now` |
| Kernel / baseband | | `uname -r`, `getprop gsm.version.baseband` |
| App under test + version | | campaign build or `org.meshcrowd.meter` `meter-1.0` |
| Signing | release key / debug key | a debug-signed meter installs beside the campaign build; note which one you measured |

## 1. Per-leg rows

Copy the block for each repetition. `templates/leg-log.csv` is the machine-readable version of the
same fields — keep both consistent, the CSV is what `analysis/*.py` and the release use.

```
leg:            B2 rep 1   (B1..B6, rep 1..3)
start / end:    12:00 / 12:30        # from runs/<leg>-<ts>/start.txt, end.txt
SOC start/end:  92 / 89              # the sampler's first and last unplugged rows
temperature:    29.6 C -> 31.0 C     # dumpsys battery at both ends; > 5 C swing = repeat the leg
screen:         off                  # off / on-40% / as-noted
radios:         BLE on, Wi-Fi on (scan-result polling)
battery saver:  off                  # off / on
Doze:           inactive -> idle     # from deviceidle-after.txt; note any forced force-idle
adaptive charging: off               # verify in Settings, not by assumption
adaptive battery (per-app): Unrestricted
charger:        unplugged the whole leg   # if it was ever plugged in, mark the leg void
metrics.json:   runs/B2-.../metrics.json
anomalies:      service killed once at 12:14, restarted by startForeground   # a kill is a result
usable?         yes / void (reason)
```

Void rules, decided **before** looking at the data: a leg is void if the charger was connected at
any point, if the phone was used as a phone, if a system update or a thermal-throttle event landed
in the window, or if the temperature rose more than 5 °C. Record the void; do not delete the folder.

## 2. Derived values, per leg (what the scripts compute, so you can spot nonsense)

| Quantity | Source line in `metrics.json` | Sanity check |
|---|---|---|
| Drain, %/h | `soc.soc_pct_per_h` | B1 should be near zero and always below B2 |
| Quantisation floor | `soc.quantisation_pct_per_h_per_step` | if `resolution_note` is "below the quantisation floor", extend the leg; do not report the number |
| Discharge current | `current.mA_discharge` | `null` on devices without `current_now` — that is a finding, not a failure |
| Net-of-idle | computed by `meter_report.py` | negative values mean B1 was measured warmer/steadier; re-run |
| Bursts requested vs results delivered | `cadence.totals.*`, `cadence.delivered_per_start` | delivered per burst < 1 in Doze is the expected throttling signature |
| Epoch completion ratio | `cadence.epoch_completion_ratio` | < 1 in B5 is the coverage-gap mechanism |
| Epoch gaps | `events.epoch_gap_s` | `missed_epochs_gt_2x_nominal` is the count that goes in the prose |
| Active Wi-Fi scan acceptance | `cadence.wifi_startscan_accepted_ratio` | 0.000 on Android 9+ for a third-party app is the documented behaviour — report the zero |
| Storage growth | `storage.bytes_growth_per_hour` | extrapolate to the campaign cadence in the text, show both |
| Mobile traffic | `storage.mobile_bytes_total` | expected ≈ 0; state the number, not the adjective |
| Service survival | `events.events` + `logcat.txt` | every kill gets a sentence in the limitations |

## 3. Which number retires which reviewer item

| Reviewer item | Fills | Paper location |
|---|---|---|
| "no energy measurements" | B1/B2/B3 drain, current, net-of-idle | Section V, new subsection + `tab:cost` |
| "no background-operation analysis" | B5 (and B6) cadence + epoch gaps + Doze splits | Section V, same table + `tab:cadence` |
| "storage/traffic impact unquantified" | `storage.*` + `mobile_bytes_total` | Section V + `tab:storage`; also reword the privacy paragraph from "no data leaves" to "measured: N bytes in M hours" |
| "no usability evidence for the gamification layer" | `tab:usability`, `tab:usability-q` | Section V (gamification discussion) + Discussion sentence on onboarding burden |
| "consent not documented" | signed `consent-form.md` per participant | Section IV protocol sentence + the release README |
| M1 per-cell counts | the tally sheets, **not** this kit | Section IV tables + Fig. 6 regeneration |

## 4. Before the numbers enter the manuscript

1. `tests/run_tests.sh` passes on this copy of the kit (it does, as of 2026-10-05).
2. `runs/` is archived (the folder, not just the tables) and its size + file count recorded in the
   release README; the session-log release should ship the CSVs with participant codes removed.
3. Every value that reaches the paper appears verbatim in a `metrics.json` — re-run
   `analysis/parse_leg.py` on the archived folder and diff, so a transcription error cannot survive.
4. Anything still `n/m` is described as not measured. The paper already says so in
   `\subsection{Not instrumented}`; edit that subsection rather than deleting it, keeping the
   legs you did not run listed as gaps.

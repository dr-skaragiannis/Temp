# Measurement protocol — battery, storage, background operation, usability

Everything below is a *recording* protocol: fixed conditions, fixed duration, machine-generated
logs, no hand-transcribed numbers. Fill `protocol-results.md` as you go; it is the file I need
back together with `runs/`.

Conventions: one leg = one uninterrupted run. Start the log, wait 5 min for the battery gauge to
settle, then start the timer (`run_leg.sh` does this). Label runs `<leg>-<rep>` with rep ∈ {1,2,3}.
`scripts/run_campaign.sh` does the whole plan in one go (shuffled order, seed logged, prompts per leg,
B5/B6 environment applied and restored, analysis at the end); `--dry-run` prints the plan only.
Randomise leg order; write the order down. Ambient temperature recorded at start/end
(`run_leg.sh` grabs it from `dumpsys battery`).

---

## Part B — power, background operation, storage, traffic

### Conditions

| Leg | Screen | Radios/scanning | Other | Question it answers |
|---|---|---|---|---|
| B1 | off | app not installed/stopped | — | idle floor of this handset at these settings |
| B2 | off | meter/app scanning, 15 s epochs | foreground service running | **the deployment case**: background drain, screen-off scan availability |
| B3 | on, 40 % brightness, dashboard visible | as B2 | — | cost of the operator view |
| B4 | off | two phones, transit sessions every 5 min | RFCOMM + L2CAP | mesh/perimeter configuration |
| B5 | off, then forced Doze | scanning only | `adb shell dumpsys deviceidle force-idle` for the last 30 min | does the duty cycle survive deep idle, and how much of it is lost |
| B6 | off | scanning, **battery saver ON** | — | what a normal user's settings do to range |

3 reps each; 30 min for B1–B3, 60 min for B4–B6 (long enough that a 15 s epoch count is
meaningful). Between reps: unplug, let the phone idle 10 min, re-run.

### Captured per leg (automated by `scripts/run_leg.sh`)

- `batterystats-before.txt`, `batterystats-after.txt` — `dumpsys batterystats` full report
- `batterystats-checkin.txt` — machine-parseable `--checkin` dump
- `battery.csv` — 5 s samples: `elapsed_s,level,scale,voltage_duV,temperature_dC,status,plugged,current_uA,idle_state,light_idle,screen`
- `storage.csv` — 60 s samples: `elapsed_s,files_bytes,cache_bytes,nobackup_bytes,session_files,exported_bytes`
- `netstats-before.txt` / `-after.txt` — `dumpsys netstats --uid` (per-UID mobile/Wi-Fi bytes)
- `deviceidle-history.txt` — `dumpsys deviceidle` + `dumpsys deviceidle history`
- `app-logs/` — the app's own CSV/JSON exports (scan cadence, epochs delivered, refusals)
- `logcat.txt` — `adb logcat -d` snapshot, kept for service kills/ANRs (a killed service is a
  result, not noise — report it)

### Derived quantities (computed by `analysis/parse_leg.py` then `analysis/meter_report.py`)

1. `drain_pct_per_h` = (level_start − level_end)/hours, and `drain_mah_per_h` from
   `BatteryProperty CURRENT_NOW` medians where the HAL exposes it, else from rated capacity.
2. `net_cost_pct_per_h` = leg drain minus B1 drain (the number a reviewer actually wants).
3. `ble_scan_requests_per_h`, `ble_scan_results_per_h`, `wifi_polls_per_h`,
   `wifi_startscan_accepted_ratio` (Android 9+ returns false for third-party apps — report it),
   `epochs_delivered_per_h`, `epoch_gap_s` median/p95 (from `events-<label>.csv`, which the app stamps at every epoch attempt).
4. `scans_per_hour_screen_off / _doze / _idle` → the operational consequence of throttling.
5. `storage_bytes_per_h`, `…_per_month_at_campaign_cadence`, `export_bytes_per_session`,
   `mobile_bytes_tx/rx` (expected ≈ 0 — say so with the number, not with an adjective).
6. Service survival: count of `started`/`killed` events, and whether the notification produced a
   wake-up storm (`dumpsys batterystats` "Wake lock" section).

Report every quantity as median [IQR] over the three reps with the exposure `T`; never a single run.

---

## Part U — usability, permission burden, and consent

Recruit **6–10** participants who are not authors. Students/colleagues are fine; record role and
prior Android development experience (that is your only stratification at this n).
**Do this only after the consent form is signed and kept** — the same form covers the field
campaign, which closes the outstanding consent item.

### Session (≈35 min, think-aloud, no assistance unless the participant asks)

| # | Task | Success criterion (objective) |
|---|---|---|
| U1 | Install the APK, grant everything the app asks for, reach the Sense tab | first live link counter > 0; record **taps and dialogs count** and **time from launch to first classification** |
| U2 | Start sensing, place the phone as instructed, verify a person crossing is flagged | event appears within 60 s |
| U3 | Open Scans, explain what one stored epoch says out loud | correctly states window length, one link that changed, and the verdict |
| U4 | Set the radius preset and explain what the envelope means | mentions distance-conditioned limit, not "unlimited range" |
| U5 | Read the Sense tab's classifier confidence and say whether it is a probability of a person or of the class being right | correct interpretation (this probes the displayed-vs-realized gap) |
| U6 | Configure a two-phone transit barrier at a chosen separation and start it | both phones show the barrier active |
| U7 | Export a session, find the file, describe who could read it | export completes; states on-device/no-server correctly |
| U8 | Reopen the app after 1 h in the drawer and say whether sensing continued | correct answer against the log (this is the background-operation literacy check) |

Per task record: `completed ∈ {yes, partial, no}`, `time_s`, `errors`, `help_requested`,
and one NASA-TLX score (0–100) for the whole session. After the session: **SUS** (10 items) and
**UMUX-Lite** (4 items), plus two open questions: "what would you not run this on, and why" and
"what did you expect the mesh to do that you now doubt".

### Reported

completion rate with Wilson interval per task, median time [IQR], error counts, SUS mean ± SD and
UMUX-Lite scores, and the permission-burden numbers from U1 (dialogs, taps, time to first
classification). With n ≤ 10 report medians and intervals and call it a pilot — do not test
hypotheses, describe.

### Consent

`templates/consent-form.md` is a fill-in template: purpose, what is recorded (task times,
errors, questionnaire answers, no audio unless you record it), storage location and retention,
right to withdraw, and the fact that crossing subjects are the experimenters themselves. Keep
signed copies; state in the paper that participants consented and that the field campaign's
bystanders were not identifiable because no identifiers are retained.

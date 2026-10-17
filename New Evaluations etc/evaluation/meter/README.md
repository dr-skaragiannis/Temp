# Measuring battery, storage, background operation, and usability for MeshCrowd

This kit turns the reviewer's "no energy, background-operation, or usability measurements"
into a real results section. Nothing here invents numbers: every value in the final tables comes
from a log file this tooling produces, and the raw `adb` dumps are kept so the analysis can be
re-run independently.

There are two routes. **Choose A if you have the v2.1 app sources** (the repository you made
public does *not* contain them — only `evaluation/android/` fragments), because A is what a
referee will accept without qualification.

| | What you measure | Paper wording it supports |
|---|---|---|
| **A. Instrumented campaign build** | the exact APK that produced E1–E5/G4, with two probe classes added | "measured on the deployment build" |
| **B. Standalone meter APK** (this kit) | a minimal app that reproduces the scan duty cycle, foreground service, and log writing | "measured on a purpose-built harness reproducing the sensing duty cycle of the deployment build" |

Route B is honest and still closes the reviewer item, but it must be described as a replication
of the duty cycle, not as the campaign build. Do not let it become "the app" in the text.

---

## 0. One-time machine setup

```bash
# JDK 17 (Android Studio bundles one; needed for CLI builds too)
java -version                     # expect 17.x
# Android Studio (Ladybug or newer) -> Settings -> Languages & Frameworks -> Android SDK
#   install: Android SDK Platform 35, Build-Tools 35.0.0, Platform-Tools (adb)
# CLI-only alternative:
#   download "commandlinetools-linux-*.zip", then
sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0"
export ANDROID_HOME=~/Android/Sdk        # or your path
export PATH="$PATH:$ANDROID_HOME/platform-tools"
```

Phone side (do these before any measurement, and record them in `protocol-results.md`):
Settings → Battery → **adaptive/optimised charging off**, Battery saver **off**,
App info → MeshCrowd → Battery → **Unrestricted**; enable *Developer options* →
**Disable background restrictions** if present; Settings → Network → **Wi-Fi scanning**
and **Bluetooth scanning** (system location scanners) **off**, so system-level scanning is not
confused with the app's; note the exact Android build (`adb shell getprop ro.build.version.incremental`).
Airplane mode stays **off** (the app needs radios) but turn *mobile data off* for the storage
baseline leg and *on* for the traffic leg — see §3.

---

## 1. Route A — instrument the campaign build

Copy these two files into the app module next to the existing classes
(the repo's `evaluation/android/src/main/java/org/meshcrowd/evaluation/` shows the house style):

```
probes/BatteryProbe.kt
probes/ScanCadenceLogger.kt
probes/StorageProbe.kt
```

and call them from the class that owns the sensing session, next to `EvaluationRecorder`:

```kotlin
private val battery  = BatteryProbe(applicationContext)
private val cadence  = ScanCadenceLogger(applicationContext)
private val storage  = StorageProbe(applicationContext)

override fun onCreate() {                       // or the session start hook
    battery.start("B2-idle-sensing"); cadence.start(); storage.start()
    ...existing EvaluationHooks.onSessionStarted(...)
}
override fun onDestroy() {                      // session stop
    battery.stop(); cadence.stop(); storage.stop()
    ...existing EvaluationHooks.onSessionStopped(...)
}
```

Also make sure the scan callbacks call `cadence.onBleScanResults(n)` /
`cadence.onWifiScanResults(n)` and that the foreground service declares
`android:foregroundServiceType="connectedDevice"` with the matching
`FOREGROUND_SERVICE_CONNECTED_DEVICE` permission (Android 14+ refuses the service otherwise —
and if that refusal is what you hit, that *is* a permission-burden result worth reporting).

Then build the variant you always shipped:

```bash
./gradlew :app:assembleRelease        # or assembleDebug if you need run-as for file sizes
adb install -r app/build/outputs/apk/release/app-release.apk
```

## 2. Route B — build the meter APK

```
meter-app/                       <- this kit's Gradle project
```

Open `meter-app/` in Android Studio (**File → Open**, not "New project") and let it sync, or:

```bash
cd meter-app
gradle wrapper --gradle-version 8.9      # creates gradlew if you prefer CLI
./gradlew :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Then in the app: press **Grant permissions**, then **Start meter**, choose the condition label
(`B1-idle`, `B2-idle-sensing`, `B4-transit`, …), and leave the phone alone. The service writes
`meter-<label>-<timestamp>.csv` into app-private storage; **Export ZIP** saves it through the
Storage Access Framework.

What the meter reproduces (edit `MeterConfig.kt` so the values match your real build — these are
the campaign settings as the manuscript describes them):

- 15 s scan epochs, 20-sample baseline windows
- a 5-per-30 s BLE scan duty cycle, `SCAN_MODE_LOW_POWER`, batched reporting
- `WifiManager.getScanResults()` polling at the epoch boundary, plus an explicit attempt at
  `startScan()` whose **rejection is itself recorded** (this is the Android-9+ reality your
  reviewer asked about)
- foreground service with `never_freeze`, screen-state and Doze-transition timestamps
- the same log-then-export path (`files/` + SAF) that `EvaluationRecorder` uses

---

## 2b. The short version, if you just want to run it

```bash
# one command: shuffled leg order, prompts per leg, capture + analysis at the end
scripts/run_campaign.sh --dry-run          # look at the ~16 h plan first
scripts/run_campaign.sh --pkg org.meshcrowd.meter --capacity-mah 4600
```

It prints a checklist before every leg, applies `deviceidle force-idle` for B5 and battery saver for
B6 and undoes them after, wraps B2 with `storage_net_snapshot.sh`, logs `runs/campaign-log.csv` with
the shuffle seed, then runs `parse_leg.py` and `meter_report.py` over everything. `--only B2,B5
--reps 1` is a 1.5 h pilot evening; `--auto` is for a bench session you watch from across the room.
The sections below explain what each leg means and why the settings have to be as stated -- read
them before the first real run, not after.

## 3. The measurement legs

Run each leg 3 times on a fresh charge cycle, in randomised order, phone on the tripod it was
mounted on during the campaign, no charger, `dumpsys battery` temperature logged at start/end.

| Leg | Screen | App state | What it answers |
|---|---|---|---|
| **B1** idle baseline | off | app not running | the floor everything is compared against |
| **B2** sensing, screen off | off | meter running, radios scanning | the deployment case: background drain |
| **B3** sensing, screen on | on, UI visible | meter running | what an operator watching the dashboard costs |
| **B4** transit / mesh | off | two phones, RFCOMM+L2CAP sessions | the multi-node configuration |
| **B5** forced Doze | off | meter running, last 30 min under `deviceidle force-idle` | does the duty cycle survive deep idle, and how much of it is lost |
| **B6** battery saver on | off | meter running, system battery saver enabled | what a normal user's own settings do to coverage |

Per leg, wrap the run with the capture script (it resets batterystats, logs state at 30 s, and
collects everything into `runs/<leg>-<n>/`):

```bash
scripts/run_leg.sh B2-idle-sensing 300      # label, minutes
```

Storage and traffic need no extra app work: run `scripts/storage_net_snapshot.sh before <leg> <pkg>`
and `... after <leg> <pkg>` around any leg, then `analysis/storage_delta.py` on the two files. It
captures app-private bytes, the external files dir, per-UID `netstats` counters and the battery
level at snapshot time. The app-side `StorageProbe` writes the same quantities plus its own
TrafficStats line, which is the only source that works on a release build with no `run-as`.

## 4. Usability (this also closes the consent item that has been pending)

`protocol.md` §U has eight tasks against the real tabs, 6–10 non-author participants, SUS and
UMUX-Lite after each session, and a consent form you can reuse for the release. Record:
task completion, time on task, unassisted vs assisted, taps from clean install to first
classification (that is the permission-burden number), and mis-taps. Do not skip the
**first-run** leg: permission dialogs are a real deployment cost and no one has measured them.

## 5. From logs to paper text

```bash
# one pass per leg directory -> <leg>/metrics.json (drain, current, cadence, storage, gaps)
analysis/parse_leg.py runs/B2-sensing-screen-off_1 runs/B2-sensing-screen-off_2 \
                      runs/B2-sensing-screen-off_3 --uid 10234

# all legs -> results/measurements.tex + results/numbers.md
analysis/meter_report.py runs/*/metrics.json --capacity-mah 4600 --outdir results

# storage/traffic from the snapshot pair, if you took one
analysis/storage_delta.py runs/B2-r1-before.txt runs/B2-r1-after.txt --minutes 30

# usability
analysis/usability_report.py --templates-dir-independent \
    --tasks templates/usability_tasks.csv --survey templates/usability_survey.csv --outdir results
```

Run `tests/run_tests.sh` before trusting a real capture: it regenerates the labelled synthetic
fixture in `tests/fixture/` and asserts every derived quantity, including that a leg with no
app-side log yields `n/m` rather than a zero.

`meter_report.py` emits `results/measurements.tex` (one row per leg: drain, net-of-idle, current,
bursts, delivered results, epochs, gap median, storage growth; medians with the observed range over
the repetitions, `n/m` where a capture was incomplete) and `results/numbers.md` with the sentences
for Sections V and VI. `usability_report.py` emits the task table with Wilson intervals and the
SUS/UMUX-Lite/NASA-TLX table. `latex/measurement_tables.tex` is the empty skeleton those outputs
drop into -- never cite the skeleton, it contains no data.

If you do not pass `--capacity-mah`, the table still reports \% per hour, the milliamperes read
straight off `current_now` where the HAL exposes it, the `batterystats` per-UID mAh attribution, and
every scan and epoch count; only the mAh/h column falls back to `n/m`, because that conversion is the
one thing that needs a constant we cannot observe.

## 6. What is verified here, and what is not

Verified in this workspace (2026-10-05), because a JDK, kotlinc 1.9.24 and the raw Android SDK
zips were installed under `/home/user`:

* **The Kotlin compiles.** `MeterConfig.kt`, `MeterService.kt`, `MainActivity.kt` and the three
  probe classes: `kotlinc -classpath platforms/android-35/android.jar`, 0 errors, 21 class files.
  Two real API errors were found and fixed this way — `PowerManager.isLightDeviceIdleMode` is
  actually `isDeviceLightIdleMode`, and `ScanSettings.setReportMode(REPORT_MODE_FIRST_MATCH)` is
  `@hide`, so the meter now uses `setLegacy(true)` and counts deliveries itself instead.
* **An APK was built and signed.** `scripts/build_apk_local.sh` (kotlinc → d8 → aapt2 → zipalign →
  apksigner, no Gradle needed) produces `dist/MeshCrowdMeter-debug.apk`, 618,923 bytes, package
  `org.meshcrowd.meter`, `minSdkVersion=26`, `targetSdkVersion=35`, debug-signed; `apksigner verify`
  and `aapt2 dump badging` pass, and `classes.dex` contains all six app classes plus the Kotlin
  stdlib. It is signed with a throwaway debug key, so it installs **alongside** your campaign build,
  never over it.
* **The analysers run and their arithmetic is pinned.** `tests/run_tests.sh`: 30 checks on a
  labelled synthetic fixture, all passing, including the null-not-zero behaviour for an incomplete
  capture.
* **`run_leg.sh` and the shell helpers are `bash -n` clean.**

Not verified, and not verifiable in this workspace:

* **Nothing has run on a handset.** No emulator, no device, so the service's real behaviour under
  Doze, the notification, and the SAF export are unexercised. Expect a first-run fix or two.
* **Gradle itself was not run** (no network for the AGP artifacts here, and the wrapper needs your
  Studio's AGP). `meter-app/` is written for AGP 8.5 / Gradle 8.7 / compileSdk 35; if your Studio
  is older, bump or lower those two numbers and the same sources should build. `build_apk_local.sh`
  is the fallback that needs no Gradle.
* **The rated capacity and the `current_now` exposure are device-specific** — if your handset hides
  the counter, the mA column stays `n/m` and the paper reports %/h only.

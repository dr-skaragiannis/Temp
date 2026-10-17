# Wiring the cost probes into the campaign build (Route A)

Read this with `README.md` (kit overview, routes, phone settings) and `protocol.md` (leg
definitions, tasks U1–U8). This file is only about *where the code goes in this repository*.

## 0. The situation, stated plainly

As of commit `d87a713` this repository contains **no Android application module**. `git log --all
--name-only` over both branches (`main`, `master`, one commit each) returns exactly four Kotlin
files under `evaluation/android/`, plus `AndroidManifest.fragment.xml`, and no `build.gradle*`, no
`AndroidManifest.xml`, no `app/` tree. `.gitignore` excludes `app/build`, `app/*.apk`, `app/*.aab`
but **not** `app/src`, so nothing was filtered out by accident — the module was simply never
committed. The public README still points at an absent `app/`.

Consequence for the paper: the campaign APK cannot be instrumented *from this repository alone*.
Route A below therefore ships as a patch you apply to the private module; Route B (the standalone
meter APK in `meter-app/`) is the part that is fully buildable from here.

## 1. Route A — files to add to the private app module

| This repo | In your module |
|---|---|
| `evaluation/android/src/main/java/org/meshcrowd/probes/BatteryProbe.kt` | `app/src/main/java/org/meshcrowd/probes/BatteryProbe.kt` |
| `…/probes/ScanCadenceLogger.kt` | same relative path |
| `…/probes/StorageProbe.kt` | same relative path |
| `…/evaluation/MeshCrowdMeterHooks.kt` | `app/src/main/java/org/meshcrowd/evaluation/MeshCrowdMeterHooks.kt` |
| `evaluation/android/AndroidManifest.fragment.xml` | merged into `app/src/main/AndroidManifest.xml` |
| `evaluation/schemas/session.schema.json` (adds optional `cost`) | your `assets/schemas/session.schema.json`, if the app bundles one |

`evaluation/meter/probes/` holds the same three classes as the canonical copies used by the meter
APK. Keep them identical:

```bash
evaluation/meter/scripts/sync_probes.sh          # copy canonical -> evaluation/android tree
evaluation/meter/scripts/sync_probes.sh --check   # CI / pre-measurement: fail on drift
```

The `--check` mode is not decoration: while this kit was assembled the two trees drifted by exactly
two API fixes (`isDeviceLightIdleMode`, `setLegacy(true)`), and a stale copy would have failed to
compile in Studio with a confusing error.

## 2. Call sites

`MeshCrowdEvaluationHooks.kt` is the existing adapter for the recorder; the meter needs the same
five moments. Everything else stays untouched — the probes never gate sensing.

```kotlin
// in the session owner, next to the recorder
private val meter = MeshCrowdMeterHooks(context, label = "B2-r1")   // <leg>-<rep>

fun onSessionStarted(...) {
    meter.start()                       // before the first startScan(), so the window brackets it
    recorder.beginSession(...)
}

// BluetoothLeScanner.startScan(...) — immediately before the call
meter.onBleScanStarted()

// ScanCallback.onBatchResults(results, clientMode)
meter.onBleScanResults(results.size, results.map { it.device.address }.distinct().size)

// Wi-Fi epoch: once per attempt, and once when the epoch's gate is satisfied
meter.onEpochAttempted()
meter.onWifiPoll(fresh = newestTimestamp > previousNewestTimestamp)
meter.onWifiStartScan(accepted = wifi.startScan())   // record the boolean, do not ignore it
if (epochGatePassed) meter.onEpochCompleted()

fun onSessionStopped(...) {
    val id = recorder.finishSession(summary)
    meter.stop()                        // after the last write, so log growth includes it
    return id
}
```

Write the CSV path through `getExternalFilesDir("meter")` (the probes already default to it). That
is what lets a **release** build be measured: `scripts/run_leg.sh` pulls
`/sdcard/Android/data/<pkg>/files/meter` first and only falls back to `run-as` (debuggable builds).

Optional, but it is what makes the numbers travel with the data: when the session closes, read the
tail of `cadence-<label>.csv` and `storage-<label>.csv` and store the summary in the session JSON
under `cost` (the schema now allows it, with `null` meaning "not measured" — never `0`).

## 3. One discrepancy to settle before attributing anything to the campaign build

`MeshCrowdEvaluationHooks.onSessionStarted` records `epochDurationMs = 10_000`, and
`evaluation/config/experiment.config.json` also has `epoch.durationMs: 10000`, while the deployed
app's epoch gate is the 15 s window the manuscript describes. Whichever is right, the instrumentation
must bracket the *same* interval the field campaign used, because "epochs completed per hour" scales
inversely with that constant. Confirm against the private module (`MeterConfig`/service constant),
then fix the fragment and the config so all three agree — and note the corrected value in the
measurement protocol. The meter APK uses 15 s (`meter-app/…/MeterConfig.kt`) and says so.

Also do not carry `sampleIntervalMs: 200` from the config into prose: Android delivers BLE scan
results in bursts (≈5 per 30 s under the platform throttle), which is why the classifier is
specified as "three consecutive samples above the trigger" rather than as a 200 ms rate.

## 4. Build and check

```bash
# 1) Route B APK (no Gradle needed): kotlinc -> d8 -> aapt2 -> zipalign -> apksigner
evaluation/meter/scripts/build_apk_local.sh
#    -> evaluation/meter/dist/MeshCrowdMeter-debug.apk (debug key; installs beside the campaign build)

# 2) normal Gradle route, if you have AGP 8.5 / Gradle 8.7 + SDK 35
cd evaluation/meter/meter-app && ./gradlew :app:assembleDebug

# 3) analyser self-test (synthetic, labelled; never a measurement)
cd evaluation/meter && bash tests/run_tests.sh
```

Verified here on 2026-10-05: `kotlinc 1.9.24` against `platforms/android-35/android.jar` compiles
the three probes, the meter app, and this `MeshCrowdMeterHooks.kt` with 0 errors;
`build_apk_local.sh` produced a signed 618,923-byte APK (`minSdkVersion=26`,
`targetSdkVersion=35`) whose `classes.dex` contains all six app classes; `tests/run_tests.sh`
passes 30 checks; `node validate.mjs` and `node tests/self-test.mjs` still pass with the schema
change. **Nothing has been run on a handset**, so the first on-device run may need small fixes.

## 5. Measurement run, once the build is on the phone

```bash
adb shell dumpsys deviceidle whitelist +org.meshcrowd.app       # keep Doze out of B1-B4
settings put global adaptive_battery_management_enabled 0
adb shell settings put global adaptive_charging_enabled 0
for leg in B1-idle-baseline B2-sensing-screen-off B3-sensing-screen-on-40pct \
           B4-two-phone-transit B5-forced-doze B6-battery-saver; do
  evaluation/meter/scripts/run_leg.sh "$leg" 30 org.meshcrowd.app
done
python3 evaluation/meter/analysis/parse_leg.py runs/*/ --uid <uid>
python3 evaluation/meter/analysis/meter_report.py runs/*/metrics.json --capacity-mah <mAh> --outdir results
```

Then the numbers go into `latex/measurement_tables.tex`'s structure (see the manuscript's Section V
`Not instrumented` subsection, which should become the measured one). Keep `runs/` out of git:
`.gitignore` already excludes `evaluation/meter/dist/` and `evaluation/meter/runs/`.

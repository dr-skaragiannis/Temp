# Android APK evaluation recording integration

The repository supplied to this task contains the React research website, not the Android/Gradle application. Therefore these Kotlin files cannot be wired into or compiled into the APK here. Copy this directory into the actual Android app module (normally `app/src/main/java/org/meshcrowd/evaluation/`) and connect the hooks described below.

## What the integration provides

- Every evaluation run is retained in app-private storage as a normal `.json` file.
- Writes are atomic and checkpoint automatically after 100 records.
- BLE addresses, BSSIDs, and SSIDs are never stored. Link identifiers are salted SHA-256 values valid only inside one session.
- Export uses Android's Storage Access Framework (`ACTION_CREATE_DOCUMENT`) with MIME type `application/json`.
- No `READ_EXTERNAL_STORAGE`, `WRITE_EXTERNAL_STORAGE`, or all-files permission is needed.
- A user can export one session or a single JSON document containing all sessions.
- The recorder targets Android 5.0 / API 21 or later so `Os.rename` can atomically replace a checkpoint file. Change the package declaration if the real app does not use `org.meshcrowd`.

## Integration

Create the recorder and controller in the Activity that owns the sensing session:

```kotlin
private lateinit var evaluationRecorder: EvaluationRecorder
private lateinit var evaluationExport: EvaluationExportController
private lateinit var evaluationHooks: MeshCrowdEvaluationHooks

override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    evaluationRecorder = EvaluationRecorder(applicationContext)
    evaluationExport = EvaluationExportController(this, evaluationRecorder)
    evaluationHooks = MeshCrowdEvaluationHooks(evaluationRecorder)
}
```

Start and stop a session around an evaluation run:

```kotlin
val sessionId = evaluationHooks.onSessionStarted(BuildConfig.VERSION_NAME)

// From BLE/Wi-Fi scan callbacks. `identifier` is hashed before it is stored.
evaluationHooks.onRssi(
    timestampMs = System.currentTimeMillis(),
    epochId = currentEpochId,
    identifier = bssidOrBleAddress,
    band = "wifi5",
    frequencyMhz = 5180,
    rssiDbm = -61.0,
)

val completedFile = evaluationHooks.onSessionStopped(
    people = peopleCount,
    vehicles = vehicleCount,
    disturbances = disturbanceCount,
    rfLinks = activeLinks,
    confirmedCrossings = confirmedCrossings,
)
```

Wire an **Export JSON** button to:

```kotlin
evaluationExport.requestSessionExport(sessionId)
// or
evaluationExport.requestAllSessionsExport()
```

Alternatively, register `EvaluationDataActivity` using `AndroidManifest.fragment.xml` and open the complete session-management UI from the existing Settings screen:

```kotlin
startActivity(Intent(this, EvaluationDataActivity::class.java))
```

That screen provides **Export selected JSON**, **Export all JSON**, and **Delete selected session** actions.

Forward the Activity result:

```kotlin
@Deprecated("Legacy callback retained for a dependency-free integration example")
override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
    if (evaluationExport.handleActivityResult(requestCode, resultCode, data)) return
    super.onActivityResult(requestCode, resultCode, data)
}
```

## Where to call the typed recorder methods

| Production event | Recorder method |
|---|---|
| BLE/Wi-Fi RSSI callback | `recordRssiSample(...)` |
| `DipDetector` closes an event | `recordEvent(...)` |
| scan epoch is stored | `recordEpoch(...)` |
| RFCOMM/L2CAP transit is classified | `recordTransit(JSONObject)` |
| a mesh event is fused | `recordMesh(JSONObject)` |
| XP or a reliability bonus is awarded | `recordReward(JSONObject)` |
| app goes to background | `checkpoint()` |
| user stops evaluation | `finishSession(summary)` |

## UI recommendation

Add an **Evaluation data** section in Settings:

1. Evaluation recording toggle (explicit opt-in).
2. Session list: timestamp, duration, bytes, event/epoch count.
3. Export selected JSON.
4. Export all JSON.
5. Delete selected session.
6. A privacy note: raw radio identifiers are never exported; location is opt-in.

The schema consumed by the experiment package is `../../schemas/session.schema.json`.

Route A instrumentation now lives beside this file: `src/main/java/org/meshcrowd/probes/*.kt`
(copies of the canonical `../meter/probes/`) and
`src/main/java/org/meshcrowd/evaluation/MeshCrowdMeterHooks.kt`. Run
`../meter/scripts/sync_probes.sh --check` before a measurement session, so the app module and the
meter APK cannot be compiling different probe code. The standalone meter APK under
`../meter/meter-app` builds without the missing app module; see `../meter/INTEGRATION.md`.

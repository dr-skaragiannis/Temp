package org.meshcrowd.evaluation

import android.content.Context
import org.meshcrowd.probes.BatteryProbe
import org.meshcrowd.probes.ScanCadenceLogger
import org.meshcrowd.probes.StorageProbe
import java.io.File

/**
 * Route A adapter: the cost probes for the campaign build.
 *
 * [MeshCrowdEvaluationHooks] records what the app *sensed*. This records what sensing *cost*:
 * battery drain, the fraction of scan opportunities the platform actually granted, and the bytes
 * the session log occupied. Both are written under the same external files dir so a release build
 * needs no `run-as`, and both are bracketed by the same session id.
 *
 * Design constraints, in case this is reviewed later:
 *  - it adds no behaviour to the sensing path: every method here is a counter or a periodic
 *    `dumpsys`-equivalent read; nothing is throttled, reordered, or gated on a measurement;
 *  - the CSV cadence, not the per-sample hooks, is what `analysis/parse_leg.py` reads, so a
 *    missed hook cannot silently bias a drain number;
 *  - no identifier, position, or raw frame is written here. If you add one, the session schema
 *    (`evaluation/schemas/session.schema.json`) and the privacy claims both need updating.
 */
class MeshCrowdMeterHooks(
    context: Context,
    private val label: String,
) {
    private val dir: File = context.getExternalFilesDir("meter") ?: context.filesDir
    private val battery = BatteryProbe(context, dir)
    private val cadence = ScanCadenceLogger(context, dir)
    private val storage = StorageProbe(context)
    private var started = false

    /** Call before the first scan is opened, so the sampling window brackets the whole session. */
    fun start() {
        if (started) return
        started = true
        battery.start(label)
        cadence.start(label)
        storage.start(label)
    }

    /** Call after the recorder has finished the session, so log growth includes the final write. */
    fun stop() {
        if (!started) return
        started = false
        storage.stop()
        cadence.stop()
        battery.stop()
    }

    // ---- sensing-engine call sites -------------------------------------------------

    /** At each `BluetoothLeScanner.startScan(...)`, immediately before the call. */
    fun onBleScanStarted() = cadence.onBleScanStarted()

    /** In `onBatchResults`/`onScanResult`: how many results arrived, how many distinct links. */
    fun onBleScanResults(count: Int, distinctLinks: Int) = cadence.onBleScanResults(count, distinctLinks)

    /**
     * Each Wi-Fi scan-results poll. [fresh] is the important one: true when at least one result is
     * newer than the previous poll's newest timestamp, i.e. the platform delivered something new.
     */
    fun onWifiPoll(fresh: Boolean) = cadence.onWifiPoll(fresh)

    /** Record the return value of `WifiManager.startScan()` (false on Android 9+ for third-party apps). */
    fun onWifiStartScan(accepted: Boolean) = cadence.onWifiStartScan(accepted)

    fun onEpochAttempted() {
        cadence.onEpochAttempted()
        cadence.noteEvent("epoch_attempted")
    }

    fun onEpochCompleted() {
        cadence.onEpochCompleted()
        cadence.noteEvent("epoch_completed")
    }

    /** Traffic counters as the app sees them; also written into the storage CSV every minute. */
    fun trafficLine(): String = storage.trafficLine()

    /** Where the CSVs land — needed by the export screen and by `scripts/run_leg.sh`. */
    fun outputDir(): File = dir
}

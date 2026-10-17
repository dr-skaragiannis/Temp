package org.meshcrowd.probes

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Handler
import android.os.Looper
import android.os.PowerManager
import android.os.SystemClock
import java.io.File

/**
 * Records whether the OS actually delivers the scan cadence the app asks for.
 *
 * Call the on* methods from your real scan callbacks; the logger aggregates per window
 * (default 30 s, matching Android's scan-throttle window) and writes one row per window.
 * That is the evidence for "operational consequence of throttling": epochs *attempted* vs
 * epochs *delivered*, split by screen state and Doze state.
 */
class ScanCadenceLogger(
    private val context: Context,
    private val dir: File,
    private val windowMs: Long = 30_000L,
) {
    private val handler = Handler(Looper.getMainLooper())
    private val power by lazy { context.getSystemService(Context.POWER_SERVICE) as PowerManager }
    private lateinit var out: File
    private var labelName: String = "session"
    private var t0 = 0L
    private var running = false

    // window accumulators
    private var bleStarts = 0
    private var bleResults = 0
    private var bleLinks = 0
    private var wifiPolls = 0
    private var wifiFreshPolls = 0
    private var wifiStartScanTried = 0
    private var wifiStartScanAccepted = 0
    private var epochsAttempted = 0
    private var epochsCompleted = 0

    private val screenReceiver = object : BroadcastReceiver() {
        override fun onReceive(c: Context, i: Intent) {
            when (i.action) {
                Intent.ACTION_SCREEN_ON -> writeEvent("screen_on")
                Intent.ACTION_SCREEN_OFF -> writeEvent("screen_off")
            }
        }
    }

    private val flush = object : Runnable {
        override fun run() {
            if (!running) return
            flushWindow()
            handler.postDelayed(this, windowMs)
        }
    }

    fun start(label: String) {
        labelName = label
        if (!dir.exists()) dir.mkdirs()
        out = File(dir, "cadence-$label.csv")
        out.writeText(
            "window_start_s,ble_scan_starts,ble_results,ble_links,wifi_polls,wifi_polls_fresh," +
                "wifi_startscan_tried,wifi_startscan_accepted,epochs_attempted,epochs_completed," +
                "screen_on,device_idle,light_idle\n"
        )
        t0 = SystemClock.elapsedRealtime()
        running = true
        context.registerReceiver(screenReceiver, IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_ON); addAction(Intent.ACTION_SCREEN_OFF)
        })
        handler.post(flush)
    }

    fun stop() {
        running = false
        handler.removeCallbacks(flush)
        runCatching { context.unregisterReceiver(screenReceiver) }
    }

    // ---- call these from the app -------------------------------------------------
    fun onBleScanStarted() { bleStarts++ }
    fun onBleScanResults(count: Int, distinctLinks: Int) {
        bleResults += count
        bleLinks = maxOf(bleLinks, distinctLinks)
    }
    /** [fresh] true when the results are newer than the previous poll's timestamp list. */
    fun onWifiPoll(fresh: Boolean) { wifiPolls++; if (fresh) wifiFreshPolls++ }
    fun onWifiStartScan(accepted: Boolean) { wifiStartScanTried++; if (accepted) wifiStartScanAccepted++ }
    fun onEpochAttempted() { epochsAttempted++ }
    fun onEpochCompleted() { epochsCompleted++ }
    /** Timestamped marker in events-<label>.csv; used to recover epoch gaps. */
    fun noteEvent(name: String) { writeEvent(name) }
    // ------------------------------------------------------------------------------

    private fun flushWindow() {
        val el = (SystemClock.elapsedRealtime() - t0) / 1000.0
        out.appendText(
            listOf(
                "%.1f".format(el), bleStarts, bleResults, bleLinks, wifiPolls, wifiFreshPolls,
                wifiStartScanTried, wifiStartScanAccepted, epochsAttempted, epochsCompleted,
                if (power.isInteractive) 1 else 0,
                if (power.isDeviceIdleMode) 1 else 0,
                if (power.isDeviceLightIdleMode) 1 else 0,
            ).joinToString(",") + "\n"
        )
        bleStarts = 0; bleResults = 0; bleLinks = 0
        wifiPolls = 0; wifiFreshPolls = 0
        wifiStartScanTried = 0; wifiStartScanAccepted = 0
        epochsAttempted = 0; epochsCompleted = 0
    }

    private fun writeEvent(name: String) {
        val el = (SystemClock.elapsedRealtime() - t0) / 1000.0
        File(dir, "events-$labelName.csv").appendText("%.1f,%s\n".format(el, name))
    }
}

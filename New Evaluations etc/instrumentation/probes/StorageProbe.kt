package org.meshcrowd.probes

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import java.io.File

/**
 * Tracks how much the app's own logging costs on disk, and (via [trafficSnapshot]) how much
 * mobile/Wi-Fi traffic the process accounts for. No root needed: only the app's own
 * directories are measured, which is exactly what the deployment question is about.
 */
class StorageProbe(private val context: Context, private val periodMs: Long = 60_000L) {
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var out: File
    private var t0 = 0L
    private var running = false

    private val tick = object : Runnable {
        override fun run() {
            if (!running) return
            sample(); handler.postDelayed(this, periodMs)
        }
    }

    fun start(label: String) {
        val d = context.getExternalFilesDir("meter") ?: context.filesDir
        out = File(d, "storage-$label.csv")
        out.writeText("elapsed_s,files_bytes,cache_bytes,nobackup_bytes,log_files,log_bytes_max,log_bytes_total,traffic\n")
        t0 = SystemClock.elapsedRealtime()
        running = true
        handler.post(tick)
    }

    fun stop() { running = false; handler.removeCallbacks(tick) }

    private fun sample() {
        val files = context.filesDir
        val cache = context.cacheDir
        val noBackup = File(context.dataDir, "no_backup")
        val logs = files.listFiles { f: File -> f.isFile && !f.name.endsWith(".csv") }?.toList() ?: emptyList()
        val el = (SystemClock.elapsedRealtime() - t0) / 1000.0
        out.appendText(
            listOf(
                "%.1f".format(el), sizeOf(files), sizeOf(cache),
                if (noBackup.exists()) sizeOf(noBackup) else 0,
                logs.size, logs.maxOfOrNull { it.length() } ?: 0L, logs.sumOf { it.length() },
                trafficLine(),
            ).joinToString(",") + "\n"
        )
    }

    private fun sizeOf(dir: File): Long {
        if (!dir.exists()) return 0L
        return dir.walkTopDown().filter { it.isFile && it.canRead() }.map { it.length() }.sum()
    }

    /** Per-UID traffic from the same counters Settings shows: the paper's "no data plan
     *  impact" claim is only as good as these four numbers. */
    fun trafficLine(): String {
        val rx = android.net.TrafficStats.getMobileRxBytes()
        val tx = android.net.TrafficStats.getMobileTxBytes()
        val urx = android.net.TrafficStats.getUidRxBytes(android.os.Process.myUid())
        val utx = android.net.TrafficStats.getUidTxBytes(android.os.Process.myUid())
        // ';' inside the field: a comma would split the column in the CSV.
        return "mobile_rx=$rx;mobile_tx=$tx;uid_rx=$urx;uid_tx=$utx"
    }
}

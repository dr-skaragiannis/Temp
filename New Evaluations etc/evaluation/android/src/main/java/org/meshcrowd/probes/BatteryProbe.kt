package org.meshcrowd.probes

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Handler
import android.os.Looper
import android.os.PowerManager
import android.os.SystemClock
import java.io.File

/**
 * Samples the battery gauge, the instantaneous current where the HAL exposes it, and the
 * Doze/screen state on a fixed period. Writes one CSV per leg so drain can be computed
 * independently of batterystats.
 *
 * Drop-in: create in whatever owns the sensing session, call start()/stop() around it.
 */
class BatteryProbe(
    private val context: Context,
    private val dir: File,
    private val periodMs: Long = 5_000L,
) {
    private val handler = Handler(Looper.getMainLooper())
    private val battery = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
    private val power = context.getSystemService(Context.POWER_SERVICE) as PowerManager
    private var t0 = 0L
    private lateinit var out: File
    private var running = false

    private val tick = object : Runnable {
        override fun run() {
            if (!running) return
            sample()
            handler.postDelayed(this, periodMs)
        }
    }

    fun start(label: String) {
        if (!dir.exists()) dir.mkdirs()
        out = File(dir, "battery-$label.csv")
        out.writeText("elapsed_s,level,scale,voltage_duV,temperature_dC,status,plugged,current_uA,device_idle,light_idle,screen\n")
        t0 = SystemClock.elapsedRealtime()
        running = true
        handler.post(tick)
    }

    fun stop() {
        running = false
        handler.removeCallbacks(tick)
    }

    private fun sample() {
        val intent: Intent? = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val level = intent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = intent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        val volt = intent?.getIntExtra(BatteryManager.EXTRA_VOLTAGE, -1) ?: -1
        val temp = intent?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, -1) ?: -1
        val status = intent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val plugged = intent?.getIntExtra(BatteryManager.EXTRA_PLUGGED, -1) ?: -1
        // CURRENT_NOW is uA on most HALs and negative while discharging; -1 where unavailable.
        val current = runCatching { battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW) }.getOrDefault(-1)
        val elapsed = (SystemClock.elapsedRealtime() - t0) / 1000.0
        out.appendText(
            listOf(
                "%.1f".format(elapsed), level, scale, volt * 1000, temp, status, plugged, current,
                if (power.isDeviceIdleMode) 1 else 0,
                if (power.isDeviceLightIdleMode) 1 else 0,
                screenState(),
            ).joinToString(",") + "\n"
        )
    }

    private fun screenState(): String =
        if (power.isInteractive) "on" else "off"
}

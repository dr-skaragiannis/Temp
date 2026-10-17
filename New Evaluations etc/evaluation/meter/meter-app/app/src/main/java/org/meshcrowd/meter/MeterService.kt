package org.meshcrowd.meter

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.BluetoothLeScanner
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.wifi.WifiManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import org.meshcrowd.probes.BatteryProbe
import org.meshcrowd.probes.ScanCadenceLogger
import org.meshcrowd.probes.StorageProbe
import java.io.File

/**
 * Reproduces the deployment app's observation duty cycle and records what the platform actually
 * delivers: scan bursts opened at the allowed rate, Wi-Fi scan-result polls at the epoch
 * boundary, and the three probes writing CSV into the app's external files directory.
 *
 * This is a measurement harness, not the sensing stack: no classification happens here.
 */
class MeterService : Service() {

    private val handler = Handler(Looper.getMainLooper())
    private var label = "session"
    private var scanner: BluetoothLeScanner? = null
    private var burstOpen = false
    private var lastWifiSignature: String? = null
    private var startedAt = 0L
    private lateinit var outDir: File

    private lateinit var battery: BatteryProbe
    private lateinit var cadence: ScanCadenceLogger
    private lateinit var storage: StorageProbe

    private val distinct = mutableSetOf<String>()

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            distinct += result.device.address
            cadence.onBleScanResults(1, distinct.size)
        }

        override fun onBatchScanResults(results: MutableList<ScanResult>) {
            results.forEach { distinct += it.device.address }
            cadence.onBleScanResults(results.size, distinct.size)
        }

        override fun onScanFailed(errorCode: Int) {
            Log.w(TAG, "BLE scan failed: $errorCode")
            cadence.onBleScanResults(0, distinct.size)
        }
    }

    private val burstRunnable = Runnable { openBurst() }
    private val epochRunnable = object : Runnable {
        override fun run() {
            runEpoch()
            handler.postDelayed(this, MeterConfig.EPOCH_MS)
        }
    }

    override fun onCreate() {
        super.onCreate()
        outDir = getExternalFilesDir("meter") ?: filesDir
        if (!outDir.exists()) outDir.mkdirs()
        battery = BatteryProbe(this, outDir, MeterConfig.LOG_PERIOD_BATTERY_MS)
        cadence = ScanCadenceLogger(this, outDir, MeterConfig.SCAN_WINDOW_MS)
        storage = StorageProbe(this, MeterConfig.LOG_PERIOD_STORAGE_MS)
        makeChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        label = intent?.getStringExtra(EXTRA_LABEL) ?: "session"
        startForegroundCompat()
        startedAt = System.currentTimeMillis()
        battery.start(label); cadence.start(label); storage.start(label)
        scanner = bluetoothAdapter()?.bluetoothLeScanner
        scheduleBursts()
        handler.postDelayed(epochRunnable, MeterConfig.EPOCH_MS)
        running = true
        Log.i(TAG, "meter started: $label")
        return START_STICKY
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        runCatching { scanner?.stopScan(scanCallback) }
        battery.stop(); cadence.stop(); storage.stop()
        File(outDir, "summary-$label.txt").writeText(
            "label=$label\nstarted=$startedAt\nstopped=${System.currentTimeMillis()}\n" +
                "unique_ble_addresses=${distinct.size}\n"
        )
        running = false
        Log.i(TAG, "meter stopped: $label")
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    // --- BLE duty cycle: BLE_BURSTS_PER_WINDOW bursts per SCAN_WINDOW_MS ------------------
    private fun scheduleBursts() {
        val perWindow = MeterConfig.SCAN_WINDOW_MS / MeterConfig.BLE_BURSTS_PER_WINDOW
        handler.postDelayed(burstRunnable, perWindow)
    }

    private fun openBurst() {
        val s = scanner ?: run { scheduleBursts(); return }
        cadence.onBleScanStarted()
        burstOpen = true
        runCatching {
            s.startScan(
                null,
                ScanSettings.Builder()
                    .setScanMode(ScanSettings.SCAN_MODE_LOW_POWER)
                    .setLegacy(true) // every advertisement; setReportMode is @hide, not callable
                    .build(),
                scanCallback,
            )
        }.onFailure { Log.w(TAG, "startScan threw: ${it.message}") }
        handler.postDelayed({
            if (burstOpen) {
                burstOpen = false
                runCatching { s.stopScan(scanCallback) }
            }
            handler.postDelayed(burstRunnable, MeterConfig.SCAN_WINDOW_MS / MeterConfig.BLE_BURSTS_PER_WINDOW - MeterConfig.BURST_MS)
        }, MeterConfig.BURST_MS)
    }

    // --- epoch: Wi-Fi scan-result poll + freshness check ---------------------------------
    private fun runEpoch() {
        cadence.onEpochAttempted()
        cadence.noteEvent("epoch_attempted")
        val wifi = applicationContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
        var fresh = false
        if (wifi != null) {
            val accepted = runCatching {
                @Suppress("DEPRECATION")
                wifi.startScan()          // returns false on Android 9+ for third-party apps
            }.getOrDefault(false)
            cadence.onWifiStartScan(accepted)
            val results = runCatching { wifi.scanResults ?: emptyList() }.getOrDefault(emptyList())
            val signature = results.joinToString(";") { "${it.BSSID}@${it.timestamp}" }
            fresh = signature.isNotEmpty() && signature != lastWifiSignature
            lastWifiSignature = signature
            cadence.onWifiPoll(fresh)
        } else {
            cadence.onWifiPoll(false)
        }
        if (burstOpen || distinct.isNotEmpty() || fresh) {
            cadence.onEpochCompleted()
            cadence.noteEvent("epoch_completed")
        }
    }

    private fun bluetoothAdapter(): BluetoothAdapter? =
        (getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager)?.adapter

    private fun makeChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = getSystemService(NotificationManager::class.java)
            if (nm.getNotificationChannel(MeterConfig.CHANNEL_ID) == null) {
                nm.createNotificationChannel(
                    NotificationChannel(
                        MeterConfig.CHANNEL_ID, "MeshCrowd Meter",
                        NotificationManager.IMPORTANCE_LOW,
                    )
                )
            }
        }
    }

    private fun startForegroundCompat() {
        val notif: Notification = Notification.Builder(this, MeterConfig.CHANNEL_ID)
            .setContentTitle("MeshCrowd Meter")
            .setContentText("recording: $label")
            .setSmallIcon(android.R.drawable.ic_menu_manage)
            .setOngoing(true)
            .build()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                MeterConfig.NOTIF_ID, notif,
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE,
            )
        } else {
            startForeground(MeterConfig.NOTIF_ID, notif)
        }
    }

    companion object {
        const val EXTRA_LABEL = "label"
        private const val TAG = "MeshCrowdMeter"
        @Volatile var running: Boolean = false
    }
}

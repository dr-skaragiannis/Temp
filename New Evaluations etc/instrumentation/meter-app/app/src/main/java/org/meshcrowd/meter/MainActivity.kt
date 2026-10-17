package org.meshcrowd.meter

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import java.io.File
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * Minimal control surface: grant, start, stop, export. Deliberately no Compose/AppCompat so the
 * build has no dependency surprises; the whole point of this app is the logs it writes.
 */
class MainActivity : Activity() {

    private lateinit var status: TextView
    private lateinit var labelField: EditText

    private val requiredPermissions: Array<String>
        get() = buildList {
            add("android.permission.BLUETOOTH_SCAN")
            add("android.permission.BLUETOOTH_CONNECT")
            add("android.permission.POST_NOTIFICATIONS")
            add("android.permission.ACCESS_FINE_LOCATION")
        }.toTypedArray()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val pad = (16 * resources.displayMetrics.density).toInt()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(pad, pad, pad, pad)
        }
        status = TextView(this).apply { text = describeState() }
        labelField = EditText(this).apply { setText("B2-idle-sensing") }

        root.addView(TextView(this).apply {
            text = "MeshCrowd Meter\nrecords battery, scan cadence, storage, traffic"
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, pad)
        })
        root.addView(status)
        root.addView(TextView(this).apply { text = "leg label"; setPadding(0, pad, 0, 0) })
        root.addView(labelField)
        root.addView(Button(this).apply {
            text = "1. Grant permissions"
            setOnClickListener {
                val missing = requiredPermissions.filter {
                    checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED
                }
                // U1 in the protocol counts these dialogs and taps - do not pre-grant via adb.
                if (missing.isEmpty()) toast("already granted")
                else requestPermissions(missing.toTypedArray(), 1)
            }
        })
        root.addView(Button(this).apply {
            text = "2. Ignore battery optimisation"
            setOnClickListener {
                val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
                if (pm.isIgnoringBatteryOptimizations(packageName)) {
                    toast("already exempt")
                } else {
                    runCatching {
                        startActivity(
                            Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                                .setData(Uri.parse("package:$packageName"))
                        )
                    }.onFailure {
                        startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
                    }
                }
            }
        })
        root.addView(Button(this).apply {
            text = "3. Start meter"
            setOnClickListener {
                startForegroundService(
                    Intent(this@MainActivity, MeterService::class.java)
                        .putExtra(MeterService.EXTRA_LABEL, labelField.text.toString().trim())
                )
                refresh()
            }
        })
        root.addView(Button(this).apply {
            text = "4. Stop and export"
            setOnClickListener {
                stopService(Intent(this@MainActivity, MeterService::class.java))
                refresh()
                zipAndExport()
            }
        })

        setContentView(ScrollView(this).apply { addView(root) })
    }

    override fun onResume() { super.onResume(); refresh() }

    private fun refresh() { status.text = describeState() }

    private fun describeState(): String {
        val dir = logDir()
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        val files = dir.listFiles()?.size ?: 0
        val bytes = dir.walkTopDown().filter { it.isFile }.map { it.length() }.sum()
        return buildString {
            append("meter running: ${MeterService.running}\n")
            append("logs: $files files, $bytes bytes in ${dir.absolutePath}\n")
            append("battery optimisation exempt: ${pm.isIgnoringBatteryOptimizations(packageName)}\n")
            append("device idle: ${pm.isDeviceIdleMode}  light idle: ${pm.isDeviceLightIdleMode}\n")
            val granted = requiredPermissions.all {
                checkSelfPermission(it) == PackageManager.PERMISSION_GRANTED
            }
            append("permissions granted: $granted")
        }
    }

    private fun logDir(): File = getExternalFilesDir("meter") ?: filesDir

    private fun zipAndExport() {
        val zip = File(cacheDir, "meter-${System.currentTimeMillis()}.zip")
        runCatching {
            ZipOutputStream(zip.outputStream()).use { out ->
                logDir().walkTopDown().filter { it.isFile }.forEach { f ->
                    out.putNextEntry(ZipEntry(f.name))
                    f.inputStream().use { it.copyTo(out) }
                    out.closeEntry()
                }
            }
        }.onFailure { toast("zip failed: ${it.message}"); return }
        startActivityForResult(
            Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "application/zip"
                putExtra(Intent.EXTRA_TITLE, zip.name)
            },
            2,
        )
    }

    @Deprecated("kept simple on purpose: no Activity Result API dependency")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != 2 || resultCode != RESULT_OK) return
        val uri = data?.data ?: return
        contentResolver.openOutputStream(uri)?.use { out ->
            cacheDir.listFiles { f: File -> f.name.startsWith("meter-") && f.name.endsWith(".zip") }
                ?.sortedByDescending { it.lastModified() }
                ?.firstOrNull()?.inputStream()?.use { it.copyTo(out) }
        }
        toast("exported")
    }

    private fun toast(m: String) = Toast.makeText(this, m, Toast.LENGTH_SHORT).show()
}

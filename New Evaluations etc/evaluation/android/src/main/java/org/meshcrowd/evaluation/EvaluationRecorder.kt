package org.meshcrowd.evaluation

import android.content.ContentResolver
import android.content.Context
import android.net.Uri
import android.os.Build
import android.system.Os
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.io.OutputStreamWriter
import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.UUID

/**
 * Persists one evaluation session as standards-compliant JSON in app-private storage.
 * Writes are atomic: a temporary file is fsynced and then renamed over the session file.
 * Raw SSIDs, BSSIDs and BLE addresses are never persisted.
 */
class EvaluationRecorder(context: Context) {
    private val appContext = context.applicationContext
    private val directory = File(appContext.filesDir, "evaluation").apply { mkdirs() }
    private val lock = Any()
    private val sessionSalt = UUID.randomUUID().toString()
    private var pendingRecords = 0
    private var activeFile: File? = null
    private var document: JSONObject? = null

    data class SessionInfo(
        val sessionId: String,
        val createdAt: String,
        val completedAt: String?,
        val file: File,
        val bytes: Long,
    )

    fun beginSession(
        appVersion: String,
        radiusM: Int,
        rangeGateDbm: Int = -75,
        noiseFloorDbm: Int = -90,
        epochDurationMs: Long = 10_000,
        stableSamples: Int = 20,
        locationIncluded: Boolean = false,
    ): String = synchronized(lock) {
        check(document == null) { "Finish the active evaluation session before starting another." }
        val sessionId = "session-${utcFileTimestamp()}-${UUID.randomUUID().toString().take(8)}"
        val createdAt = utcTimestamp()
        val root = JSONObject()
            .put("schemaVersion", SCHEMA_VERSION)
            .put("sessionId", sessionId)
            .put("createdAt", createdAt)
            .put("completedAt", JSONObject.NULL)
            .put("appVersion", appVersion)
            .put(
                "device",
                JSONObject()
                    .put("pseudonymousId", "sha256:${hashIdentifier(sessionId)}")
                    .put("model", Build.MODEL ?: "unknown")
                    .put("androidApi", Build.VERSION.SDK_INT),
            )
            .put(
                "privacy",
                JSONObject()
                    .put("rawIdentifiersStored", false)
                    .put("cameraUsed", false)
                    .put("microphoneUsed", false)
                    .put("locationIncluded", locationIncluded),
            )
            .put(
                "configuration",
                JSONObject()
                    .put("radiusM", radiusM)
                    .put("rangeGateDbm", rangeGateDbm)
                    .put("noiseFloorDbm", noiseFloorDbm)
                    .put("epochDurationMs", epochDurationMs)
                    .put("stableSamples", stableSamples),
            )
            .put("samples", JSONArray())
            .put("events", JSONArray())
            .put("epochs", JSONArray())
            .put("transit", JSONArray())
            .put("mesh", JSONArray())
            .put("rewards", JSONArray())
            .put("summary", JSONObject())

        activeFile = File(directory, "$sessionId.json")
        document = root
        pendingRecords = 0
        flushLocked()
        sessionId
    }

    fun recordRssiSample(
        timestampMs: Long,
        epochId: String,
        rawLinkIdentifier: String,
        radioBand: String,
        frequencyMhz: Int?,
        rssiDbm: Double,
    ) = append("samples") {
        require(radioBand in ALLOWED_BANDS) { "Unsupported radio band: $radioBand" }
        require(rssiDbm in -127.0..20.0) { "RSSI outside the Android scan range: $rssiDbm" }
        JSONObject()
            .put("timestampMs", timestampMs)
            .put("epochId", epochId)
            .put("linkIdHash", "sha256:${hashIdentifier(rawLinkIdentifier)}")
            .put("radioBand", radioBand)
            .put("frequencyMhz", frequencyMhz ?: JSONObject.NULL)
            .put("rssiDbm", rssiDbm)
    }

    fun recordEvent(
        eventId: String,
        startMs: Long,
        endMs: Long,
        dominantBand: String,
        depthDb: Double,
        durationMs: Long,
        texture: Double,
        varianceDb2: Double,
        prominenceDb: Double,
        coherentLinks: Int,
        classification: String,
        confidence: Double,
        range: JSONObject,
    ) = append("events") {
        JSONObject()
            .put("eventId", eventId)
            .put("startMs", startMs)
            .put("endMs", endMs)
            .put("dominantBand", dominantBand)
            .put("depthDb", depthDb)
            .put("durationMs", durationMs)
            .put("texture", texture)
            .put("varianceDb2", varianceDb2)
            .put("prominenceDb", prominenceDb)
            .put("coherentLinks", coherentLinks)
            .put("classification", classification)
            .put("confidence", confidence.coerceIn(0.0, 1.0))
            .put("range", range)
    }

    fun recordEpoch(
        epochId: String,
        startMs: Long,
        endMs: Long,
        place: String?,
        latitude: Double?,
        longitude: Double?,
        accuracyM: Double?,
        linkCount: Int,
        changedLinkCount: Int,
        maxChangeDb: Double,
        changeThresholdDb: Double = 3.0,
        changed: Boolean,
    ) = append("epochs") {
        val geo = if (latitude != null && longitude != null) {
            JSONObject()
                .put("latitude", latitude)
                .put("longitude", longitude)
                .put("accuracyM", accuracyM ?: JSONObject.NULL)
        } else {
            JSONObject.NULL
        }
        JSONObject()
            .put("epochId", epochId)
            .put("startMs", startMs)
            .put("endMs", endMs)
            .put("place", place ?: JSONObject.NULL)
            .put("geo", geo)
            .put("linkCount", linkCount)
            .put("changedLinkCount", changedLinkCount)
            .put("maxChangeDb", maxChangeDb)
            .put("changeThresholdDb", changeThresholdDb)
            .put("fieldVerdict", if (changed) "changed" else "unchanged")
    }

    fun recordTransit(record: JSONObject) = appendValue("transit", record)

    fun recordMesh(record: JSONObject) = appendValue("mesh", record)

    fun recordReward(record: JSONObject) = appendValue("rewards", record)

    fun checkpoint() = synchronized(lock) { flushLocked() }

    fun finishSession(summary: JSONObject): File = synchronized(lock) {
        val root = checkNotNull(document) { "No active evaluation session." }
        root.put("completedAt", utcTimestamp())
        root.put("summary", summary)
        flushLocked()
        val completed = checkNotNull(activeFile)
        document = null
        activeFile = null
        pendingRecords = 0
        completed
    }

    fun listSessions(): List<SessionInfo> = directory
        .listFiles { file -> file.isFile && file.extension == "json" }
        .orEmpty()
        .mapNotNull { file ->
            runCatching {
                val root = JSONObject(file.readText())
                SessionInfo(
                    sessionId = root.getString("sessionId"),
                    createdAt = root.getString("createdAt"),
                    completedAt = root.optString("completedAt").takeIf { it.isNotBlank() && it != "null" },
                    file = file,
                    bytes = file.length(),
                )
            }.getOrNull()
        }
        .sortedByDescending { it.createdAt }

    fun exportSession(contentResolver: ContentResolver, destination: Uri, sessionId: String) {
        synchronized(lock) {
            if (document?.optString("sessionId") == sessionId) flushLocked()
        }
        val source = File(directory, "$sessionId.json")
        require(source.exists()) { "Unknown evaluation session: $sessionId" }
        contentResolver.openOutputStream(destination, "w").use { output ->
            checkNotNull(output) { "Could not open export destination." }
            source.inputStream().use { input -> input.copyTo(output) }
        }
    }

    fun exportAll(contentResolver: ContentResolver, destination: Uri) {
        synchronized(lock) { if (document != null) flushLocked() }
        val sessions = JSONArray()
        listSessions().sortedBy { it.createdAt }.forEach { info ->
            sessions.put(JSONObject(info.file.readText()))
        }
        val export = JSONObject()
            .put("schemaVersion", SCHEMA_VERSION)
            .put("exportedAt", utcTimestamp())
            .put("sessionCount", sessions.length())
            .put("sessions", sessions)
        contentResolver.openOutputStream(destination, "w").use { output ->
            checkNotNull(output) { "Could not open export destination." }
            output.writer(Charsets.UTF_8).use { writer -> writer.write(export.toString(2)) }
        }
    }

    fun deleteSession(sessionId: String): Boolean = synchronized(lock) {
        check(document?.optString("sessionId") != sessionId) { "Cannot delete the active session." }
        File(directory, "$sessionId.json").delete()
    }

    private fun append(arrayName: String, createValue: () -> JSONObject) = appendValue(arrayName, createValue())

    private fun appendValue(arrayName: String, value: JSONObject) = synchronized(lock) {
        val root = checkNotNull(document) { "Begin an evaluation session before recording data." }
        root.getJSONArray(arrayName).put(value)
        pendingRecords += 1
        if (pendingRecords >= AUTO_FLUSH_RECORDS) flushLocked()
    }

    private fun flushLocked() {
        val root = document ?: return
        val target = checkNotNull(activeFile)
        val temporary = File(target.parentFile, "${target.name}.tmp")
        FileOutputStream(temporary).use { stream ->
            val writer = OutputStreamWriter(stream, Charsets.UTF_8).buffered()
            writer.write(root.toString(2))
            writer.flush()
            stream.fd.sync()
        }
        runCatching { Os.rename(temporary.absolutePath, target.absolutePath) }
            .getOrElse {
                // Compatibility fallback for unusual filesystems; same-directory rename is preferred.
                if (target.exists() && !target.delete()) error("Could not replace ${target.absolutePath}")
                check(temporary.renameTo(target)) { "Could not commit ${target.absolutePath}" }
            }
        pendingRecords = 0
    }

    private fun hashIdentifier(raw: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
        return digest.digest("$sessionSalt:$raw".toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
    }

    private fun utcTimestamp(): String = ISO_FORMAT.get().format(Date())

    private fun utcFileTimestamp(): String = FILE_FORMAT.get().format(Date())

    companion object {
        const val SCHEMA_VERSION = "1.0.0"
        private const val AUTO_FLUSH_RECORDS = 100
        private val ALLOWED_BANDS = setOf("ble", "wifi24", "wifi5", "rfcomm", "l2cap")
        private val ISO_FORMAT = ThreadLocal.withInitial {
            SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US).apply { timeZone = TimeZone.getTimeZone("UTC") }
        }
        private val FILE_FORMAT = ThreadLocal.withInitial {
            SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US).apply { timeZone = TimeZone.getTimeZone("UTC") }
        }
    }
}
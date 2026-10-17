package org.meshcrowd.evaluation

import android.app.Activity
import android.content.Intent

/**
 * Storage Access Framework integration. Exported JSON is chosen by the user and
 * needs no broad storage permission on Android 4.4+.
 */
class EvaluationExportController(
    private val activity: Activity,
    private val recorder: EvaluationRecorder,
) {
    private var pendingSessionId: String? = null
    private var exportingAll = false

    fun requestSessionExport(sessionId: String) {
        pendingSessionId = sessionId
        exportingAll = false
        activity.startActivityForResult(
            createDocumentIntent("meshcrowd-$sessionId.json"),
            REQUEST_CREATE_JSON,
        )
    }

    fun requestAllSessionsExport() {
        pendingSessionId = null
        exportingAll = true
        activity.startActivityForResult(
            createDocumentIntent("meshcrowd-evaluation-all.json"),
            REQUEST_CREATE_JSON,
        )
    }

    /** Call this from the host Activity's onActivityResult. */
    fun handleActivityResult(requestCode: Int, resultCode: Int, data: Intent?): Boolean {
        if (requestCode != REQUEST_CREATE_JSON) return false
        if (resultCode != Activity.RESULT_OK) return true
        val destination = data?.data ?: return true
        if (exportingAll) recorder.exportAll(activity.contentResolver, destination)
        else pendingSessionId?.let { recorder.exportSession(activity.contentResolver, destination, it) }
        pendingSessionId = null
        exportingAll = false
        return true
    }

    private fun createDocumentIntent(fileName: String) = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
        addCategory(Intent.CATEGORY_OPENABLE)
        type = "application/json"
        putExtra(Intent.EXTRA_TITLE, fileName)
    }

    companion object {
        const val REQUEST_CREATE_JSON = 0xA511
    }
}
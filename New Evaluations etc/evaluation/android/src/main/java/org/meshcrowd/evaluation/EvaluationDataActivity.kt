package org.meshcrowd.evaluation

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ListView
import android.widget.TextView
import android.widget.Toast

/**
 * Dependency-free session management screen. Register it in the app manifest and
 * launch it from Settings with startActivity(Intent(this, EvaluationDataActivity::class.java)).
 */
class EvaluationDataActivity : Activity() {
    private lateinit var recorder: EvaluationRecorder
    private lateinit var exportController: EvaluationExportController
    private lateinit var list: ListView
    private lateinit var empty: TextView
    private var sessions: List<EvaluationRecorder.SessionInfo> = emptyList()
    private var selectedSessionId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        recorder = EvaluationRecorder(applicationContext)
        exportController = EvaluationExportController(this, recorder)
        setContentView(createContentView())
    }

    override fun onResume() {
        super.onResume()
        refreshSessions()
    }

    @Deprecated("Legacy callback retained so this integration has no AndroidX dependency")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (exportController.handleActivityResult(requestCode, resultCode, data)) return
        super.onActivityResult(requestCode, resultCode, data)
    }

    private fun createContentView(): View {
        val density = resources.displayMetrics.density
        fun dp(value: Int) = (value * density).toInt()

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(20))
        }
        root.addView(TextView(this).apply {
            text = "Evaluation data"
            textSize = 26f
        })
        root.addView(TextView(this).apply {
            text = "Sessions are private JSON files. Raw SSIDs, BSSIDs and BLE addresses are never retained."
            textSize = 14f
            setPadding(0, dp(8), 0, dp(16))
        })

        empty = TextView(this).apply {
            text = "No evaluation sessions yet."
            gravity = Gravity.CENTER
            visibility = View.GONE
        }
        list = ListView(this).apply {
            choiceMode = ListView.CHOICE_MODE_SINGLE
            setOnItemClickListener { _, _, position, _ -> selectedSessionId = sessions[position].sessionId }
        }
        root.addView(list, LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f))
        root.addView(empty, LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(80)))

        val actions = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(12), 0, 0)
        }
        actions.addView(Button(this).apply {
            text = "Export selected JSON"
            setOnClickListener {
                val id = selectedSessionId
                if (id == null) toast("Select a session first.") else exportController.requestSessionExport(id)
            }
        })
        actions.addView(Button(this).apply {
            text = "Export all JSON"
            setOnClickListener {
                if (sessions.isEmpty()) toast("There are no sessions to export.") else exportController.requestAllSessionsExport()
            }
        })
        actions.addView(Button(this).apply {
            text = "Delete selected session"
            setOnClickListener {
                val id = selectedSessionId
                if (id == null) toast("Select a session first.")
                else {
                    recorder.deleteSession(id)
                    selectedSessionId = null
                    refreshSessions()
                }
            }
        })
        root.addView(actions)
        return root
    }

    private fun refreshSessions() {
        sessions = recorder.listSessions()
        empty.visibility = if (sessions.isEmpty()) View.VISIBLE else View.GONE
        list.visibility = if (sessions.isEmpty()) View.GONE else View.VISIBLE
        val rows = sessions.map { info ->
            val completed = info.completedAt ?: "recording / interrupted"
            "${info.createdAt}\n$completed · ${info.bytes / 1024.0f} KB\n${info.sessionId}"
        }
        list.adapter = ArrayAdapter(this, android.R.layout.simple_list_item_single_choice, rows)
    }

    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
}
package org.meshcrowd.evaluation

import org.json.JSONObject

/** Example adapter showing where the production sensing engine records each artefact. */
class MeshCrowdEvaluationHooks(private val recorder: EvaluationRecorder) {
    fun onSessionStarted(appVersion: String): String = recorder.beginSession(
        appVersion = appVersion,
        radiusM = 20,
        rangeGateDbm = -75,
        noiseFloorDbm = -90,
        epochDurationMs = 10_000,
        stableSamples = 20,
        locationIncluded = false,
    )

    fun onRssi(timestampMs: Long, epochId: String, identifier: String, band: String, frequencyMhz: Int?, rssiDbm: Double) {
        recorder.recordRssiSample(timestampMs, epochId, identifier, band, frequencyMhz, rssiDbm)
    }

    fun onMeshConfirmation(eventId: String, nodeCount: Int, fusedAccuracy: Double, reliability: Double) {
        recorder.recordMesh(
            JSONObject()
                .put("eventId", eventId)
                .put("nodeCount", nodeCount)
                .put("confirmed", nodeCount >= 2)
                .put("fusedAccuracy", fusedAccuracy)
                .put("reliabilityScore", reliability)
                .put("rewardMultiplier", if (reliability >= 0.9) 1.25 else 1.0),
        )
    }

    fun onReward(timestampMs: Long, reason: String, baseXp: Int, fusionBonusXp: Int, multiplier: Double) {
        recorder.recordReward(
            JSONObject()
                .put("timestampMs", timestampMs)
                .put("reason", reason)
                .put("baseXp", baseXp)
                .put("fusionBonusXp", fusionBonusXp)
                .put("multiplier", multiplier)
                .put("awardedXp", (baseXp + fusionBonusXp) * multiplier),
        )
    }

    fun onSessionStopped(people: Int, vehicles: Int, disturbances: Int, rfLinks: Int, confirmedCrossings: Int) =
        recorder.finishSession(
            JSONObject()
                .put("people", people)
                .put("vehicles", vehicles)
                .put("disturbances", disturbances)
                .put("rfLinks", rfLinks)
                .put("confirmedCrossings", confirmedCrossings),
        )
}
package org.meshcrowd.meter

/**
 * Duty-cycle parameters. Set these to the values your deployment build uses; the meter is only
 * evidence about the campaign configuration if these match it. The defaults are the values the
 * manuscript describes for the field campaign.
 */
object MeterConfig {
    const val EPOCH_MS = 15_000L            // scan-epoch window
    const val BASELINE_SAMPLES = 20         // per-link median baseline depth
    const val BLE_BURSTS_PER_WINDOW = 5     // Android 15 unprivileged scan allowance per 30 s
    const val SCAN_WINDOW_MS = 30_000L      // throttle accounting window
    const val BURST_MS = 1_500L             // how long each scan burst stays open
    const val LOG_PERIOD_BATTERY_MS = 5_000L
    const val LOG_PERIOD_STORAGE_MS = 60_000L
    const val NOTIF_ID = 0x4D43             // "MC"
    const val CHANNEL_ID = "meshcrowd-meter"
}

#!/usr/bin/env bash
# run_leg_local_usb.sh — one measurement leg on a USB-only setup.
#
# Why this exists: run_leg.sh needs a live `adb` link the whole leg, but on this bench the
# only usable link IS the charge cable, and a phone on USB power sits in status=2 forever, so
# drain is unobservable. `adb shell dumpsys battery set status 3` would fix the number but it
# fakes the battery broadcast, and a fabricated drain must never reach the manuscript.
#
# So this script does the honest thing instead: the app records autonomously and we retrieve
# afterwards. The probes (BatteryProbe/ScanCadenceLogger/StorageProbe) write into
# /sdcard/Android/data/<pkg>/files/meter/ continuously, so a leg is:
#
#   1. cable in  -> app starts, all probes run from inside the phone
#   2. cable out -> phone discharges on its own, nobody touches it, nothing is sampled remotely
#   3. cable in  -> pull the CSVs, dumpsys, logcat, then stop the service
#
# Only steps 1 and 3 need the cable. The drain numbers come from the app-side CSVs, which
# parse_leg.py already treats as authoritative (`battery_source` = "app"), so nothing is lost
# except the remote 5 s/60 s shell samplers -- and those are the ones that cannot exist here.
#
# The cost, stated plainly: this is not the ~16 h unattended campaign. Each leg is a hands-on
# session, and the operator must genuinely leave the phone alone between the unplug and the
# replug. Nothing sleeps on the host while unplugged, so there is no way for the PC to
# "keep watching".
#
# Usage: scripts/run_leg_local_usb.sh <label> <minutes> [package]
set -u -o pipefail
cd "$(dirname "$0")/.."

LABEL="${1:?label, e.g. B2-idle-sensing}"
MINUTES="${2:?discharge duration in minutes}"
PKG="${3:-org.meshcrowd.meter}"

OUT="runs/${LABEL}-$(date +%Y%m%d-%H%M%S)"
DEVLOG="/sdcard/Android/data/$PKG/files/meter"
mkdir -p "$OUT/app-logs"

say() { echo; echo ">>> $*"; }
die() { echo "ABORT: $*" >&2; exit 1; }

command -v adb >/dev/null 2>&1 || die "adb not on PATH"
adb wait-for-device >/dev/null 2>&1 &
WAITER=$!

say "leg $LABEL, ${MINUTES} min of unplugged discharge -> $OUT"

# ---- 1. cable in: pre-state -----------------------------------------------------------
adb shell dumpsys batterystats        > "$OUT/batterystats-before.txt" 2>&1
adb shell dumpsys battery             >> "$OUT/batterystats-before.txt" 2>&1
adb shell dumpsys netstats --uid      > "$OUT/netstats-before.txt" 2>&1
adb shell dumpsys deviceidle          > "$OUT/deviceidle-before.txt" 2>&1
adb shell dumpsys deviceidle history  >> "$OUT/deviceidle-before.txt" 2>&1
adb shell dumpsys power | head -40    > "$OUT/power-before.txt" 2>&1
adb shell getprop ro.build.version.incremental > "$OUT/device-build.txt" 2>&1
bash scripts/storage_net_snapshot.sh before "$LABEL" "$PKG" >/dev/null 2>&1 || true
date -Is > "$OUT/start.txt"

# Clear old CSVs so the pull cannot mix two sessions, then start the service.
adb shell "rm -f $DEVLOG/*.csv $DEVLOG/summary-*.txt" >/dev/null 2>&1

echo
echo "=================================================================="
echo " The meter service starts now and records on its own."
echo " 1. put the phone where it will sit for ${MINUTES} min (tripod, screen off)"
echo " 2. UNPLUG the USB cable  <-- this is what makes it discharge"
echo " 3. leave it completely alone. no tapping, no picking up."
echo "=================================================================="
adb shell am start -n "$PKG/.MainActivity" >/dev/null 2>&1
sleep 3
echo " Tapping '3. Start meter' for you (label=$LABEL)."
adb shell input tap 610 1045 >/dev/null 2>&1
sleep 6

RUNNING=$(adb shell dumpsys activity services "$PKG" 2>/dev/null | grep -c "isForeground=true")
[ "${RUNNING:-0}" -gt 0 ] || die "service did not come up foreground - check logcat before continuing"
echo " service is foreground. Good."

# Confirm the probes opened their files; if not, there is no log to retrieve later.
adb shell "ls -1 $DEVLOG" 2>/dev/null | tr -d '\r' > "$OUT/device-log-list-start.txt"
for f in battery cadence events storage; do
  grep -q "$f" "$OUT/device-log-list-start.txt" || die "probe CSV for '$f' missing at start"
done
echo " all four probe CSVs present."
cat "$OUT/device-log-list-start.txt" | sed 's/^/    /'

say "NOW UNPLUG THE CABLE AND WAIT ${MINUTES} MINUTES"
echo "The phone is recording on its own. This script cannot observe anything while"
echo "unplugged and is not pretending to. Come back in ${MINUTES} minutes."
echo
printf "  press Enter once you have UNPLUGGED the cable  "
read -r _
UNPLUGGED_AT=$(date -Is)
date -Is > "$OUT/unplugged.txt"

# While unplugged there is nothing to poll. Sit out the discharge window without
# touching the host, so no accidental adb traffic perturbs the leg.
say "discharging for ${MINUTES} min (host idle, phone untouched)"
END=$(( $(date +%s) + MINUTES * 60 ))
while [ "$(date +%s)" -lt "$END" ]; do
  printf "\r   %3d min remaining" $(( (END - $(date +%s)) / 60 ))
  sleep 60
done
printf "\r   done.                \n"

say "REPLUG THE USB CABLE NOW, then press Enter"
printf "  press Enter after the cable is back in  "
read -r _
REPLUGGED_AT=$(date -Is)
date -Is > "$OUT/replugged.txt"
sleep 5

# ---- 3. cable in: post-state and retrieval ---------------------------------------------
say "retrieving"
adb shell logcat -d -t 4000            > "$OUT/logcat.txt" 2>&1
adb shell dumpsys batterystats          > "$OUT/batterystats-after.txt" 2>&1
adb shell dumpsys batterystats --checkin> "$OUT/batterystats-checkin.txt" 2>&1
adb shell dumpsys netstats --uid        > "$OUT/netstats-after.txt" 2>&1
adb shell dumpsys deviceidle            > "$OUT/deviceidle-after.txt" 2>&1
adb shell dumpsys deviceidle history    >> "$OUT/deviceidle-after.txt" 2>&1
bash scripts/storage_net_snapshot.sh after "$LABEL" "$PKG" >/dev/null 2>&1 || true

# Stop the service so onDestroy writes summary-<label>.txt with its own bounds.
adb shell am force-stop "$PKG" >/dev/null 2>&1
sleep 3
adb pull "$DEVLOG" "$OUT/app-logs/" >/dev/null 2>&1

{
  echo "label=$LABEL"
  echo "unplugged_at=$UNPLUGGED_AT"
  echo "replugged_at=$REPLUGGED_AT"
  echo "requested_minutes=$MINUTES"
  echo "battery capacity used for mAh/h: read charge_full, not this file"
  echo "NOTE: drain comes from the app-side battery CSV, sampled inside the phone."
  echo "      There was no remote sampler while unplugged; that is deliberate."
} > "$OUT/notes.txt"

PLG=$(adb shell dumpsys battery 2>/dev/null | tr -d '\r' | sed -n 's/.*plugged: \([0-9]*\).*/\1/p')
LVL=$(adb shell dumpsys battery 2>/dev/null | tr -d '\r' | sed -n 's/.*level: \([0-9]*\).*/\1/p')

echo
echo "== done: $OUT"
echo "   unplugged $UNPLUGGED_AT"
echo "   replugged $REPLUGGED_AT"
echo "   plugged=${PLG:-?} level=${LVL:-?}"
echo "   pulled:"; ls -1 "$OUT/app-logs" 2>/dev/null | sed 's/^/     /'
echo
echo "next:"
echo "  python3 analysis/parse_leg.py $OUT --uid \$(adb shell dumpsys package $PKG | sed -n 's/.*appId=\\([0-9]*\\).*/\\1/p' | tr -d '\\r')"
echo "  python3 analysis/meter_report.py runs/*/metrics.json --capacity-mah <charge_full/1000> --outdir results"
#!/usr/bin/env bash
# storage_net_snapshot.sh — one storage/traffic snapshot, to be taken before and after a leg.
#
#   scripts/storage_net_snapshot.sh before B2-r1 org.meshcrowd.meter
#   scripts/storage_net_snapshot.sh after  B2-r1 org.meshcrowd.meter
#   analysis/storage_delta.py runs/B2-r1-before.txt runs/B2-r1-after.txt
#
# Everything here is readable without root on a release build except the run-as lines, which
# are attempted and skipped (the app-side StorageProbe covers the same ground on release builds).
set -u -o pipefail

WHEN="${1:?before|after}"
LABEL="${2:?leg label}"
PKG="${3:-org.meshcrowd.meter}"
OUT="runs/${LABEL}-${WHEN}.txt"
mkdir -p runs
{
  echo "# snapshot when=$WHEN label=$LABEL package=$PKG"
  echo "time: $(date -Is)"
  echo "uptime_s: $(awk '{print int($1)}' /proc/uptime 2>/dev/null || adb shell cat /proc/uptime | tr -d '\r' | awk '{print int($1)}')"
  echo "== device storage of the package (dumpsys diskstats)"
  adb shell dumpsys diskstats 2>/dev/null | tr -d '\r' \
    | awk '/Package Names:/{p=1} p{print} /App Sizes:/{q=1} q&&/^$/{exit}' | head -40
  echo "== app-private bytes via run-as (debuggable builds only)"
  for d in files cache no_backup; do
    v=$(adb shell "run-as $PKG du -sb $d 2>/dev/null" | tr -d '\r' | grep -o '^[0-9]*' || true)
    echo "du_${d}_bytes: ${v:-unavailable}"
  done
  n=$(adb shell "run-as $PKG sh -c 'find files -type f 2>/dev/null | wc -l'" | tr -d '\r' | grep -o '[0-9]*$' || true)
  echo "file_count: ${n:-unavailable}"
  echo "== external files dir (works on release builds too)"
  adb shell "du -sb /sdcard/Android/data/$PKG/files 2>/dev/null" | tr -d '\r'
  adb shell "find /sdcard/Android/data/$PKG/files -type f -printf '%s %p\n' 2>/dev/null | sort -n | tail -20" | tr -d '\r'
  echo "== per-UID network counters"
  adb shell dumpsys netstats --uid 2>/dev/null | tr -d '\r' \
    | grep -E "uid=|rxBytes|txBytes|^  [0-9]{4,6}:" | head -40
  echo "== TrafficStats as the app sees them (logcat tail, from StorageProbe)"
  adb shell "dumpsys activity providers | grep -q $PKG" 2>/dev/null || true
  adb logcat -d -s MeshCrowdMeter:V 2>/dev/null | tr -d '\r' | grep -E "traffic|mobile_rx" | tail -5
  echo "== battery level at snapshot time"
  adb shell dumpsys battery 2>/dev/null | tr -d '\r' | grep -E "level|scale|voltage|temperature|status|plugged"
} > "$OUT" 2>&1
echo "wrote $OUT"

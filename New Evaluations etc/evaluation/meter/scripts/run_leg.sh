#!/usr/bin/env bash
# run_leg.sh — capture one battery/background/storage measurement leg.
# Usage: scripts/run_leg.sh <label> <minutes> [package]
#   scripts/run_leg.sh B2-idle-sensing 30 org.meshcrowd.app
# Requires: adb on PATH (platform-tools). No root needed; run-as is used only if the build is debuggable.
set -u -o pipefail

LABEL="${1:?label, e.g. B2-idle-sensing}"
MINUTES="${2:?duration in minutes}"
PKG="${3:-org.meshcrowd.meter}"

OUT="runs/${LABEL}-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT/app-logs"
echo "== leg $LABEL, ${MINUTES} min -> $OUT"

# 1) pre-state snapshots
adb shell dumpsys batterystats           > "$OUT/batterystats-before.txt"
adb shell dumpsys battery               >> "$OUT/batterystats-before.txt"
adb shell dumpsys netstats --uid        > "$OUT/netstats-before.txt"
adb shell dumpsys deviceidle            > "$OUT/deviceidle-before.txt"
adb shell dumpsys power | head -40      > "$OUT/power-before.txt"
date -Is                                > "$OUT/start.txt"

# 2) reset accounting so the post-run report covers exactly this window
adb shell dumpsys batterystats --reset
adb shell dumpsys netstats --reset 2>/dev/null || true
echo "batterystats reset at $(date -Is)" | tee "$OUT/notes.txt"
echo "preconditions to verify manually: adaptive charging off, battery saver off, app battery=Unrestricted, no charger" >> "$OUT/notes.txt"

# 3) 5 s battery/idle/screen sampler (this is the primary drain record)
(
  END=$(( $(date +%s) + MINUTES*60 ))
  printf 'elapsed_s,level,scale,voltage_duV,temperature_dC,status,plugged,current_uA,idle_state,light_idle,screen,timestamp\n' \
    > "$OUT/battery.csv"
  T0=$(date +%s)
  while [ "$(date +%s)" -lt "$END" ]; do
    B=$(adb shell dumpsys battery | tr -d '\r')
    lvl=$(sed -n 's/.*level: \([0-9]*\).*/\1/p' <<<"$B")
    scl=$(sed -n 's/.*scale: \([0-9]*\).*/\1/p' <<<"$B")
    vol=$(sed -n 's/.*voltage: \([0-9]*\).*/\1/p' <<<"$B")
    tmp=$(sed -n 's/.*temperature: \([0-9-]*\).*/\1/p' <<<"$B")
    st=$(sed -n 's/.*status: \([0-9]*\).*/\1/p' <<<"$B")
    plg=$(sed -n 's/.*plugged: \([0-9]*\).*/\1/p' <<<"$B")
    cur=$(adb shell dumpsys battery_properties 2>/dev/null | tr -d '\r' | sed -n 's/.*chargingStatus.*//p' >/dev/null; \
          adb shell cat /sys/class/power_supply/battery/current_now 2>/dev/null | tr -d '\r')
    idl=$(adb shell dumpsys deviceidle 2>/dev/null | tr -d '\r' | grep -m1 -o 'mState=[0-9]*' | cut -d= -f2)
    lgt=$(adb shell dumpsys deviceidle 2>/dev/null | tr -d '\r' | grep -m1 -o 'mLightState=[0-9]*' | cut -d= -f2)
    scr=$(adb shell dumpsys power 2>/dev/null | tr -d '\r' | grep -m1 -o 'mWakefulness=[A-Za-z]*' | cut -d= -f2)
    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$(( $(date +%s) - T0 ))" "${lvl:-NA}" "${scl:-NA}" "${vol:-NA}" "${tmp:-NA}" \
      "${st:-NA}" "${plg:-NA}" "${cur:-NA}" "${idl:-NA}" "${lgt:-NA}" "${scr:-NA}" "$(date -Is)" \
      >> "$OUT/battery.csv"
    sleep 5
  done
) &
SAMPLER=$!

# 4) 60 s storage sampler (app-private bytes; run-as works on debuggable builds only)
(
  END=$(( $(date +%s) + MINUTES*60 ))
  printf 'elapsed_s,files_bytes,cache_bytes,nobackup_bytes,session_files,exported_bytes\n' \
    > "$OUT/storage.csv"
  T0=$(date +%s)
  while [ "$(date +%s)" -lt "$END" ]; do
    f=$(adb shell "run-as $PKG du -sb files 2>/dev/null" | tr -d '\r' | grep -o '^[0-9]*' || true)
    c=$(adb shell "run-as $PKG du -sb cache 2>/dev/null" | tr -d '\r' | grep -o '^[0-9]*' || true)
    n=$(adb shell "run-as $PKG du -sb no_backup 2>/dev/null" | tr -d '\r' | grep -o '^[0-9]*' || true)
    cnt=$(adb shell "run-as $PKG sh -c 'ls files 2>/dev/null | wc -l'" | tr -d '\r' | grep -o '[0-9]*$' || true)
    exp=$(adb shell "run-as $PKG sh -c 'du -cb files/*.json 2>/dev/null | tail -1'" | tr -d '\r' | grep -o '[0-9]*\s*total' | grep -o '[0-9]*' || true)
    printf '%s,%s,%s,%s,%s,%s\n' "$(( $(date +%s) - T0 ))" "${f:-NA}" "${c:-NA}" "${n:-NA}" "${cnt:-NA}" "${exp:-NA}" \
      >> "$OUT/storage.csv"
    sleep 60
  done
) &
STORAGE=$!

# 5) wait, then post-state
wait $SAMPLER $STORAGE 2>/dev/null || true

adb shell logcat -d -t 4000 > "$OUT/logcat.txt"
adb shell dumpsys batterystats            > "$OUT/batterystats-after.txt"
adb shell dumpsys batterystats --checkin  > "$OUT/batterystats-checkin.txt"
adb shell dumpsys netstats --uid          > "$OUT/netstats-after.txt"
adb shell dumpsys deviceidle              > "$OUT/deviceidle-after.txt"
adb shell dumpsys deviceidle history     >> "$OUT/deviceidle-after.txt"
date -Is                                  > "$OUT/end.txt"

# 6) pull the logs. Preferred location is the app's external files dir
#    (/sdcard/Android/data/<pkg>/files/meter) so that release builds need no run-as.
adb pull "/sdcard/Android/data/$PKG/files/meter" "$OUT/app-logs/" 2>/dev/null || true
if [ -z "$(ls -A "$OUT/app-logs" 2>/dev/null)" ]; then
  adb shell "run-as $PKG sh -c 'cd files && tar -cf /sdcard/meter-pull.tar * 2>/dev/null'" || true
  adb pull /sdcard/meter-pull.tar "$OUT/app-logs/" 2>/dev/null || \
    echo "NOTE: no logs pulled - pass getExternalFilesDir(\"meter\") to the probes, or use the app's Export ZIP and drop it in $OUT/app-logs/" | tee -a "$OUT/notes.txt"
fi
adb bugreport "$OUT/bugreport.zip" >/dev/null 2>&1 || echo "bugreport skipped (re-run manually if wanted)" | tee -a "$OUT/notes.txt"

echo "== done: $OUT"
echo "   next: analysis/parse_batterystats.py $OUT/batterystats-after.txt -o $OUT/metrics.json"

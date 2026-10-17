#!/usr/bin/env bash
# run_campaign.sh — drive the whole battery/background/storage measurement plan.
#
#   scripts/run_campaign.sh --dry-run              # print the plan, touch nothing
#   scripts/run_campaign.sh                        # interactive: one prompt per leg (recommended)
#   scripts/run_campaign.sh --only B2,B5 --reps 1  # a subset, e.g. a pilot evening
#   scripts/run_campaign.sh --auto                 # no prompts, for a long bench session
#
# Options: --pkg <package> (default org.meshcrowd.meter) --capacity-mah <mAh> (for the report)
#          --uid <android uid> --minutes-b123 <n> --minutes-b456 <n>
#
# What it does per repetition: applies the leg's environment (Doze force, battery saver), runs
# scripts/run_leg.sh, then restores the environment. It refuses to guess: it stops if `adb` is
# missing, and if the charger turns out to be connected at the end of a leg it appends a VOID row
# to runs/campaign-log.csv instead of letting that leg enter the tables.
#
# Randomised order, one shuffle for the whole campaign, seed printed into the log so the order is
# reconstructable when you write the protocol paragraph.
set -u -o pipefail
cd "$(dirname "$0")/.."

PKG=org.meshcrowd.meter; REPS=3; DRY=0; AUTO=0; ONLY=""; UID_ARG=""; CAP=""
M_SHORT=30; M_LONG=60
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1;; --auto) AUTO=1;;
    --pkg) PKG="$2"; shift;; --reps) REPS="$2"; shift;;
    --only) ONLY="$2"; shift;; --uid) UID_ARG="$2"; shift;;
    --capacity-mah) CAP="$2"; shift;;
    --minutes-b123) M_SHORT="$2"; shift;; --minutes-b456) M_LONG="$2"; shift;;
    -h|--help) sed -n '3,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac; shift
done

LEGS=(B1 B2 B3 B4 B5 B6)
dur() { case "$1" in B1|B2|B3) echo "$M_SHORT";; *) echo "$M_LONG";; esac; }
desc() {
  case "$1" in
    B1) echo "idle baseline - app STOPPED, screen off, nothing running";;
    B2) echo "sensing, screen OFF - the deployment case";;
    B3) echo "sensing, screen ON at 40% - the operator view";;
    B4) echo "two-handset transit/mesh session - second phone paired and running";;
    B5) echo "sensing with FORCED Doze for the last half of the leg";;
    B6) echo "sensing with system battery saver ON";;
  esac; }
pre() {
  case "$1" in
    B5) echo "dumpsys deviceidle force-idle";;
    B6) echo "cmd power save-mode true";;
    *) ;;
  esac; }
post() {
  case "$1" in
    B5) echo "dumpsys deviceidle unforce";;
    B6) echo "cmd power save-mode false";;
    *) ;;
  esac; }

if [ -n "$ONLY" ]; then
  FILTERED=(); IFS=, read -ra WANT <<< "$ONLY"
  for l in "${LEGS[@]}"; do
    for w in "${WANT[@]}"; do
      key=$(printf '%s' "$w" | tr -d ' ' | tr 'a-z' 'A-Z' | cut -c1-2)
      [ "$l" = "$key" ] && FILTERED+=("$l")
    done
  done
  if [ "${#FILTERED[@]}" -eq 0 ]; then
    echo "no leg matched --only '$ONLY' (choose from ${LEGS[*]})" >&2; exit 2
  fi
  LEGS=("${FILTERED[@]}")
fi
[ "${#LEGS[@]}" -gt 0 ] || { echo "no legs selected"; exit 2; }

command -v adb >/dev/null 2>&1 || [ "$DRY" = 1 ] || { echo "adb not on PATH - install platform-tools, then re-run"; exit 1; }

SEED=$(date +%s)
ORDER=$(LEGS="${LEGS[*]}" REPS="$REPS" SEED="$SEED" SHORT="$M_SHORT" LONG="$M_LONG" python3 -c "
import os, random
legs = os.environ['LEGS'].split(); reps = int(os.environ['REPS'])
short, long_ = int(os.environ['SHORT']), int(os.environ['LONG'])
random.seed(int(os.environ['SEED']))
plan = [(l, r) for l in legs for r in range(1, reps + 1)]
random.shuffle(plan)
print('\n'.join('%s %d %d' % (l, r, short if l in ('B1','B2','B3') else long_) for l, r in plan))")
TOTAL=$(echo "$ORDER" | wc -l | tr -d ' ')
MINS=$(echo "$ORDER" | awk '{s+=$3} END{print s}')
GAP=10; COOL=$(( (TOTAL - 1) * GAP ))

echo "==================== MeshCrowd measurement campaign ===================="
echo "package        : $PKG"
echo "legs selected  : ${LEGS[*]}   repetitions: $REPS"
echo "plan           : $TOTAL legs, ~$MINS min of measurement + ${COOL} min of settling  (~$(( (MINS+COOL)/60 )) h)"
echo "shuffle seed   : $SEED   (quote this in the protocol paragraph)"
echo "order          : (leg, rep, minutes)"
echo "$ORDER" | awk '{printf "  %2d. %s rep %s  %3d min\n", NR, $1, $2, $3}'
[ "$DRY" = 1 ] && echo "MODE           : DRY RUN - no adb calls, no files written except this plan"
echo "======================================================================"

mkdir -p runs
LOG=runs/campaign-log.csv
[ -f "$LOG" ] || echo "seq,leg,rep,label,start,end,notes" > "$LOG"

adb_sh() { if [ "$DRY" = 1 ]; then echo "    [dry] adb $*"; else adb shell "$*" >/dev/null 2>&1 || echo "    ! adb shell '$*' failed"; fi; }

confirm() { # $1 leg
  [ "$AUTO" = 1 ] && return 0
  [ "$DRY" = 1 ] && return 0
  echo
  echo "  ---- $1: $(desc "$1")"
  echo "  checklist (verify on the phone, not by assumption):"
  echo "    [ ] charger UNPLUGGED for the whole leg"
  echo "    [ ] adaptive charging OFF, adaptive battery OFF"
  echo "    [ ] Settings -> Apps -> $PKG -> Battery -> Unrestricted"
  echo "    [ ] brightness 40% (B3 only: screen stays on)"
  echo "    [ ] incoming traffic suppressed WITHOUT killing the radios: mobile data OFF + Do Not"
  echo "        Disturbance. Do NOT use airplane mode on B2-B6 unless you re-enable Wi-Fi and"
  echo "        Bluetooth right after: with Wi-Fi off there are no scan results, and a leg like"
  echo "        that measures your radio switch, not the sensing cost."
  echo "    [ ] leg-log.csv row started (templates/leg-log.csv)"
  if [ -n "$(pre "$1")" ]; then echo "    [ ] runner will apply: adb shell $(pre "$1")"; fi
  if [ -n "$(post "$1")" ]; then echo "    [ ] runner will restore: adb shell $(post "$1")"; fi
  printf "  press Enter when the phone is in this state (ctrl-c to abort) "
  read -r _ || true
}

i=0
while read -r L R MIN; do
  i=$((i + 1))
  [ -z "${MIN:-}" ] && MIN=$(dur "$L")
  LABEL="${L}-r${R}"
  echo
  echo "[$i/$TOTAL] $LABEL  ($MIN min)  $(desc "$L")"
  confirm "$L"
  [ -n "$(pre "$L")" ] && adb_sh "$(pre "$L")"
  if [ "$L" = "B2" ]; then
    if [ "$DRY" = 1 ]; then echo "    [dry] storage_net_snapshot.sh before $LABEL $PKG"
    else bash scripts/storage_net_snapshot.sh before "$LABEL" "$PKG" >/dev/null; fi
  fi
  if [ "$DRY" = 1 ]; then
    echo "    [dry] scripts/run_leg.sh $LABEL $MIN $PKG"
  else
    bash scripts/run_leg.sh "$LABEL" "$MIN" "$PKG" || { echo "    ! run_leg.sh failed for $LABEL - see runs/"; }
  fi
  if [ "$L" = "B2" ]; then
    if [ "$DRY" = 1 ]; then echo "    [dry] storage_net_snapshot.sh after $LABEL $PKG"
    else bash scripts/storage_net_snapshot.sh after "$LABEL" "$PKG" >/dev/null; fi
  fi
  [ -n "$(post "$L")" ] && adb_sh "$(post "$L")"
  echo "$i,$L,$R,$LABEL,$(date -Is),$(date -Is),seed=$SEED" >> "$LOG"
  # a plug check is a real control: an unnoticed charger silently voids the leg
  if [ "$DRY" = 0 ]; then
    PLG=$(adb shell dumpsys battery 2>/dev/null | tr -d '\r' | sed -n 's/.*plugged: \([0-9]*\).*/\1/p')
    [ "${PLG:-0}" != "0" ] && echo "    WARNING: charger was connected at the end of $LABEL - mark this leg void" \
      && echo "$i,$L,$R,$LABEL,VOID,charger connected," >> "$LOG"
  fi
  [ "$i" -lt "$TOTAL" ] && { echo "    settling ${GAP} min (phone idle, untouched)"; [ "$DRY" = 1 ] || sleep $((GAP * 60)); }
done <<< "$ORDER"

if [ "$DRY" = 1 ]; then
  echo
  echo "dry run complete. To actually measure: plug the phone in ONLY to install, then run this"
  echo "without --dry-run. Expect $(( (MINS+COOL)/60 )) hours; splitting over evenings is fine,"
  echo "the plan order is fixed by the seed so you can resume by using --only with the missing legs."
  exit 0
fi

echo
echo "== analysing"
python3 analysis/parse_leg.py runs/*/ ${UID_ARG:+--uid "$UID_ARG"} || echo "parse_leg failed - report the traceback, do not hand-edit the CSVs"
python3 analysis/meter_report.py runs/*/metrics.json --outdir results ${CAP:+--capacity-mah "$CAP"} \
  && echo "  -> results/measurements.tex, results/numbers.md"
echo "done. Fill templates/leg-log.csv and templates/results-worksheet.md from those files."

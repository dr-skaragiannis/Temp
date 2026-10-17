#!/usr/bin/env bash
# sync_probes.sh — keep the Route A copies of the probe classes identical to the canonical ones.
#
#   <kit>/probes/*.kt                                  canonical (what the meter APK compiles)
#   evaluation/android/src/main/java/org/meshcrowd/probes/   the campaign build's copies
#
# Two trees, one source of truth. Run this after editing a probe; run it with --check in CI or
# before a measurement session. A mismatch means the campaign APK and the meter APK would be
# counting different things, which invalidates any comparison between them.
#
# Outside the repository (e.g. a standalone copy of the kit) there is nothing to sync, and saying so
# beats failing with a confusing "no such directory".
set -u -o pipefail
shopt -s nullglob
cd "$(dirname "$0")/.."                       # -> the kit directory

SRC=probes
DST=../android/src/main/java/org/meshcrowd/probes
if [ ! -d "$(dirname "$DST")" ]; then
  if [ "${1:-}" = "--check" ]; then echo "not inside the repo (no evaluation/android tree) - nothing to check"; exit 0; fi
  echo "not inside the repo: $DST does not exist; canonical probes stay in $SRC"; exit 0
fi

case "${1:-}" in
  --check)
    st=0
    for f in "$SRC"/*.kt; do
      b=$(basename "$f")
      cmp -s "$f" "$DST/$b" || { echo "DRIFT: $b differs between $SRC and $DST"; echo "       fix with: scripts/sync_probes.sh"; st=1; }
    done
    for f in "$DST"/*.kt; do
      b=$(basename "$f"); [ -f "$SRC/$b" ] || { echo "STRAY: $DST/$b has no canonical counterpart"; st=1; }
    done
    [ "$st" = 0 ] && echo "probes in sync ($(ls "$SRC"/*.kt | wc -l) files)"
    exit "$st"
    ;;
  ""|--force)
    n=0
    for f in "$SRC"/*.kt; do cp -f "$f" "$DST/$(basename "$f")" && n=$((n + 1)); done
    for f in "$DST"/*.kt; do [ -f "$SRC/$(basename "$f")" ] || { echo "removing stray $(basename "$f")"; rm -f "$f"; }; done
    echo "copied $n file(s) to $DST"
    "$0" --check
    ;;
  *)
    echo "usage: scripts/sync_probes.sh [--check|--force]" >&2
    exit 2
    ;;
esac

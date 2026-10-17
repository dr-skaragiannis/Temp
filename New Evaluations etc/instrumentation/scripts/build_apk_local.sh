#!/usr/bin/env bash
# Build MeshCrowdMeter-debug.apk without Gradle, for sandboxes/CI that only have a JDK,
# kotlinc and the raw SDK zips. The canonical path is still
#   cd meter-app && ./gradlew :app:assembleDebug
# This script produces the same classes + resources + a debug signature, so it can be used
# to prove the sources compile and to put an APK on the handset when Gradle is unavailable.
#
# Env overrides: ANDROID_SDK (needs platforms/android-XX/android.jar + a build-tools dir),
#                KOTLINC, COMPILE_SDK.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK="${ANDROID_SDK:-$HOME/android-sdk}"
KOT="${KOTLINC:-$HOME/kotlinc/bin/kotlinc}"
API="${COMPILE_SDK:-35}"

PLAT="$SDK/platforms/android-$API/android.jar"
BT="$(ls -d "$SDK"/build-tools/* | sort -V | tail -1)"
[ -x "$BT/aapt2" ] || { echo "aapt2 not found under $SDK/build-tools"; exit 1; }
[ -f "$PLAT" ] || { echo "missing $PLAT"; exit 1; }
[ -x "$KOT" ] || { echo "missing kotlinc at $KOT"; exit 1; }

OUT="$ROOT/dist"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/klasses" "$WORK/dex" "$OUT"

SRC=()
while IFS= read -r f; do SRC+=("$f"); done < <(
  find "$ROOT/meter-app/app/src/main/java" -name '*.kt'
  find "$ROOT/probes" -maxdepth 1 -name '*.kt'
)
echo "==> kotlinc, ${#SRC[@]} files, jvm-target 1.8, target $API"
"$KOT" -nowarn -classpath "$PLAT" -jvm-target 1.8 -d "$WORK/klasses" "${SRC[@]}"

echo "==> d8 (app classes + kotlin stdlib)"
CP=()
while IFS= read -r c; do CP+=("$c"); done < <(find "$WORK/klasses" -name '*.class')
STDLIB="$(dirname "$(dirname "$KOT")")/lib"
for j in kotlin-stdlib.jar kotlin-stdlib-jdk7.jar kotlin-stdlib-jdk8.jar; do
  [ -f "$STDLIB/$j" ] && CP+=("$STDLIB/$j")
done
"$BT/d8" --release --min-api 26 --lib "$PLAT" --output "$WORK/dex" "${CP[@]}"

echo "==> aapt2 compile + link"
# Gradle's `namespace` supplies the manifest package; the raw aapt2 path needs it inline,
# so link against a temporary copy instead of editing the committed manifest.
sed -E 's|<manifest xmlns:android="[^"]*">|<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.meshcrowd.meter">|' \
  "$ROOT/meter-app/app/src/main/AndroidManifest.xml" > "$WORK/AndroidManifest.xml"
grep -q 'package="org.meshcrowd.meter"' "$WORK/AndroidManifest.xml" || { echo "could not inject package attribute"; exit 1; }
"$BT/aapt2" compile --dir "$ROOT/meter-app/app/src/main/res" -o "$WORK/res.zip"
"$BT/aapt2" link -o "$WORK/base.apk" -I "$PLAT" \
  --manifest "$WORK/AndroidManifest.xml" \
  --min-sdk-version 26 --target-sdk-version "$API" \
  --version-code 1 --version-name meter-1.0 \
  --java "$WORK/genjava" "$WORK/res.zip"

echo "==> zip + align + sign"
cp "$WORK/base.apk" "$WORK/unsigned.apk"
(cd "$WORK/dex" && zip -q "$WORK/unsigned.apk" classes.dex)
"$BT/zipalign" -f -p 4 "$WORK/unsigned.apk" "$WORK/aligned.apk"
KS="$WORK/debug.keystore"
keytool -genkeypair -keystore "$KS" -alias androiddebugkey -storepass android -keypass android \
  -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
"$BT/apksigner" sign --ks "$KS" --ks-pass pass:android --key-pass pass:android \
  --out "$OUT/MeshCrowdMeter-debug.apk" "$WORK/aligned.apk"

echo "==> verify"
"$BT/apksigner" verify --print-certs "$OUT/MeshCrowdMeter-debug.apk" | head -4
"$BT/aapt2" dump badging "$OUT/MeshCrowdMeter-debug.apk" | grep -E "^(package|sdkVersion|targetSdkVersion|uses-permission|launchable)" | sed 's/^/    /'
ls -l "$OUT/MeshCrowdMeter-debug.apk"

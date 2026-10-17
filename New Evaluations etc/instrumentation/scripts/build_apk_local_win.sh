#!/usr/bin/env bash
# Windows/Git-Bash port of build_apk_local.sh. Same sources, same output; the only
# difference is that the build-tools binaries are .exe/.bat on Windows and must be
# resolved through a helper. The canonical paths remain:
#   cd meter-app && ./gradlew :app:assembleDebug      (any platform)
#   scripts/build_apk_local.sh                       (Linux/macOS)
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

# Resolve a build-tools executable: Linux has `aapt2`, Windows has `aapt2.exe` or
# `foo.bat`. Git Bash appends .exe on its own but never .bat, so try each suffix.
bt() {
  local name="$1"
  for cand in "$BT/$name" "$BT/$name.exe" "$BT/$name.bat"; do
    [ -f "$cand" ] && { printf '%s' "$cand"; return 0; }
  done
  echo "build-tools tool not found: $name under $BT" >&2
  exit 1
}

AAPT2="$(bt aapt2)"; D8="$(bt d8)"; ZIPALIGN="$(bt zipalign)"; APKSIGNER="$(bt apksigner)"
[ -f "$PLAT" ] || { echo "missing $PLAT"; exit 1; }
[ -f "$KOT" ] || [ -x "$KOT" ] || { echo "missing kotlinc at $KOT"; exit 1; }

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
"$D8" --release --min-api 26 --lib "$PLAT" --output "$WORK/dex" "${CP[@]}"

echo "==> aapt2 compile + link"
# Gradle's `namespace` supplies the manifest package; the raw aapt2 path needs it inline,
# so link against a temporary copy instead of editing the committed manifest.
sed -E 's|<manifest xmlns:android="[^"]*">|<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.meshcrowd.meter">|' \
  "$ROOT/meter-app/app/src/main/AndroidManifest.xml" > "$WORK/AndroidManifest.xml"
grep -q 'package="org.meshcrowd.meter"' "$WORK/AndroidManifest.xml" || { echo "could not inject package attribute"; exit 1; }
# `assembleDebug` marks the APK debuggable, which is what makes `run-as` work; run_leg.sh's
# 60 s storage sampler reads app-private bytes through it. The raw path has no build type,
# so set it here to match. This is a measurement harness, not a shippable artifact.
sed -E 's|<application|<application android:debuggable="true"|' "$WORK/AndroidManifest.xml" > "$WORK/AndroidManifest.tmp" \
  && mv "$WORK/AndroidManifest.tmp" "$WORK/AndroidManifest.xml"
"$AAPT2" compile --dir "$ROOT/meter-app/app/src/main/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/base.apk" -I "$PLAT" \
  --manifest "$WORK/AndroidManifest.xml" \
  --min-sdk-version 26 --target-sdk-version "$API" \
  --version-code 1 --version-name meter-1.0 \
  --java "$WORK/genjava" "$WORK/res.zip"

echo "==> zip + align + sign"
cp "$WORK/base.apk" "$WORK/unsigned.apk"
(cd "$WORK/dex" && zip -q "$WORK/unsigned.apk" classes.dex)
"$ZIPALIGN" -f -p 4 "$WORK/unsigned.apk" "$WORK/aligned.apk"
KS="$WORK/debug.keystore"
keytool -genkeypair -keystore "$KS" -alias androiddebugkey -storepass android -keypass android \
  -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
"$APKSIGNER" sign --ks "$KS" --ks-pass pass:android --key-pass pass:android \
  --out "$OUT/MeshCrowdMeter-debug.apk" "$WORK/aligned.apk"

echo "==> verify"
"$APKSIGNER" verify --print-certs "$OUT/MeshCrowdMeter-debug.apk" | head -4
"$AAPT2" dump badging "$OUT/MeshCrowdMeter-debug.apk" | grep -E "^(package|sdkVersion|targetSdkVersion|uses-permission|launchable)" | sed 's/^/    /'
ls -l "$OUT/MeshCrowdMeter-debug.apk"

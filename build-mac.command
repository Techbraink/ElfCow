#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/.venv/bin/python"
MODEL="$PWD/resources/models/m2m100_418M"
TESS="$PWD/resources/tesseract/bin/tesseract"

[ -x "$PY" ] || { echo "Run Install.command first."; exit 1; }
[ -f "$MODEL/config.json" ] || { echo "Translation model missing. Run Install.command."; exit 1; }
[ -x "$TESS" ] || { echo "Bundled Tesseract missing. Run Install.command."; exit 1; }

rm -rf build dist release
mkdir -p release

"$PY" -m PyInstaller \
  --noconfirm \
  --clean \
  installer/PDFTranslator.spec

APP="dist/PDF Translator.app"
[ -d "$APP" ] || { echo "Build failed: $APP not found."; exit 1; }

echo "Checking application architecture and forbidden Tk/Carbon dependency…"
MAIN_EXE="$APP/Contents/MacOS/PDF Translator"
[ -x "$MAIN_EXE" ] || { echo "Main executable missing: $MAIN_EXE"; exit 1; }
file "$MAIN_EXE"
if otool -L "$MAIN_EXE" | grep -Fq "/System/Library/Frameworks/Carbon.framework/Versions/A/Carbon"; then
  echo "ERROR: the app executable directly links to legacy Carbon."
  echo "This build must use the Qt/PySide6 UI and must not contain a Tk/Carbon dependency."
  exit 1
fi
if otool -L "$MAIN_EXE" | grep -Eiq '(^|/)(Tk|Tcl)\.framework|_tkinter'; then
  echo "ERROR: Tk/Tcl dependency detected in the main executable."
  exit 1
fi

cp -R "$APP" "release/"

# Optional Developer ID signing.
# Set SIGN_IDENTITY to your exact Developer ID Application certificate name.
if [ -n "${SIGN_IDENTITY:-}" ]; then
  echo "Signing with: $SIGN_IDENTITY"
  codesign --deep --force --options runtime --timestamp \
    --sign "$SIGN_IDENTITY" "$APP"
  rm -rf "release/PDF Translator.app"
  cp -R "$APP" "release/"
fi

hdiutil create \
  -volname "PDF Translator" \
  -srcfolder "release/PDF Translator.app" \
  -ov \
  -format UDZO \
  "release/PDFTranslator-macOS.dmg" >/dev/null

echo ""
echo "BUILD COMPLETE"
echo "APP: release/PDF Translator.app"
echo "DMG: release/PDFTranslator-macOS.dmg"

if [ -n "${SIGN_IDENTITY:-}" ]; then
  echo ""
  echo "Next: notarize with Apple's notarytool and staple the ticket."
fi

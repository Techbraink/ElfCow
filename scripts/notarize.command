#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

APP="release/PDF Translator.app"
DMG="release/PDFTranslator-macOS.dmg"

if [ -z "${APPLE_NOTARY_PROFILE:-}" ]; then
  echo 'Set APPLE_NOTARY_PROFILE to a notarytool keychain profile name.'
  echo 'Example: xcrun notarytool store-credentials "PDFTranslator" ...'
  exit 1
fi

[ -d "$APP" ] || { echo "Missing $APP. Run build-mac.command first."; exit 1; }

echo "Submitting DMG for notarization…"
xcrun notarytool submit "$DMG" \
  --keychain-profile "$APPLE_NOTARY_PROFILE" \
  --wait

echo "Stapling ticket…"
xcrun stapler staple "$DMG"
xcrun stapler validate "$DMG"

echo "Notarized DMG ready: $DMG"

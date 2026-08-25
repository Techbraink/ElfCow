#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

DEST="$ROOT/resources/tesseract"
DEST_BIN="$DEST/bin"
DEST_DATA="$DEST/share/tessdata"

echo "======================================"
echo " Bundling Tesseract for PDF Translator"
echo "======================================"

rm -rf "$DEST"
mkdir -p "$DEST_BIN"
mkdir -p "$DEST_DATA"

echo ""
echo "Installing Tesseract..."

export HOMEBREW_NO_AUTO_UPDATE=1

if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: Homebrew is not available."
    exit 1
fi

brew install tesseract || true
brew install tesseract-lang || true

echo ""
echo "Finding Tesseract..."

TESSERACT_PREFIX="$(brew --prefix tesseract)"
LANG_PREFIX="$(brew --prefix tesseract-lang)"

echo "Tesseract prefix:"
echo "$TESSERACT_PREFIX"

echo ""
echo "Language package prefix:"
echo "$LANG_PREFIX"

TESSERACT_BIN="$TESSERACT_PREFIX/bin/tesseract"

if [ ! -x "$TESSERACT_BIN" ]; then
    echo "ERROR: Tesseract executable not found:"
    echo "$TESSERACT_BIN"
    exit 1
fi

echo ""
echo "Copying Tesseract executable..."

cp "$TESSERACT_BIN" "$DEST_BIN/tesseract"
chmod +x "$DEST_BIN/tesseract"

echo ""
echo "Finding OCR language files..."

LANGUAGES=(
    eng
    rus
    tha
    ind
    lav
    kat
)

for lang in "${LANGUAGES[@]}"; do

    echo ""
    echo "Searching for: $lang.traineddata"

    FOUND=""

    while IFS= read -r file; do
        if [ -f "$file" ]; then
            FOUND="$file"
            break
        fi
    done < <(find "$LANG_PREFIX" "$TESSERACT_PREFIX" \
        -type f \
        -name "${lang}.traineddata" \
        2>/dev/null)

    if [ -z "$FOUND" ]; then
        echo ""
        echo "ERROR: Missing OCR language data:"
        echo "$lang"
        echo ""
        echo "Searching installed files:"
        find "$LANG_PREFIX" "$TESSERACT_PREFIX" \
            -type f \
            -name "*.traineddata" \
            2>/dev/null | head -100 || true
        exit 1
    fi

    echo "Found:"
    echo "$FOUND"

    cp "$FOUND" "$DEST_DATA/${lang}.traineddata"

done

echo ""
echo "======================================"
echo " Verifying OCR installation"
echo "======================================"

"$DEST_BIN/tesseract" --version

echo ""
echo "OCR languages bundled:"

for lang in "${LANGUAGES[@]}"; do

    FILE="$DEST_DATA/${lang}.traineddata"

    if [ ! -s "$FILE" ]; then
        echo "ERROR: $FILE is missing or empty."
        exit 1
    fi

    SIZE="$(stat -f%z "$FILE")"

    echo "  $lang.traineddata — $SIZE bytes"

done

echo ""
echo "Testing bundled Tesseract..."

"$DEST_BIN/tesseract" \
    --tessdata-dir "$DEST_DATA" \
    --list-langs

echo ""
echo "======================================"
echo " Tesseract bundle complete"
echo "======================================"

echo "Location:"
echo "$DEST"

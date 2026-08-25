#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
PY="$ROOT/.venv/bin/python"

echo "=== PDF Translator — macOS setup ==="

command -v python3 >/dev/null || {
  echo "Python 3 is required. Install Python 3.12 or newer."
  exit 1
}

[ -x "$PY" ] || python3 -m venv "$ROOT/.venv"

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$ROOT/requirements.txt"

echo ""
echo "Downloading the MIT-licensed M2M100 418M translation model."
echo "This is a build-time download. The final application works offline."

"$PY" - <<'PY'
from pathlib import Path
from huggingface_hub import snapshot_download

root = Path.cwd()
dest = root / "resources" / "models" / "m2m100_418M"
dest.mkdir(parents=True, exist_ok=True)

snapshot_download(
    repo_id="facebook/m2m100_418M",
    local_dir=str(dest),
    local_dir_use_symlinks=False,
)

required = ["config.json", "tokenizer_config.json", "sentencepiece.bpe.model"]
missing = [x for x in required if not (dest / x).exists()]
if missing:
    raise SystemExit("Model download incomplete: " + ", ".join(missing))

print("Model ready:", dest)
PY

command -v brew >/dev/null || {
  echo "Homebrew is required only on the BUILD Mac to prepare bundled OCR."
  echo "Install Homebrew, then run Install.command again."
  exit 1
}

brew list tesseract >/dev/null 2>&1 || brew install tesseract
brew list tesseract-lang >/dev/null 2>&1 || brew install tesseract-lang

TPREFIX="$(brew --prefix tesseract)"
mkdir -p "$ROOT/resources/tesseract/bin" \
         "$ROOT/resources/tesseract/share/tessdata" \
         "$ROOT/resources/tesseract/lib"

cp -L "$TPREFIX/bin/tesseract" "$ROOT/resources/tesseract/bin/tesseract"

for l in eng rus tha ind lav kat; do
  test -f "$TPREFIX/share/tessdata/$l.traineddata" || {
    echo "Missing OCR language data: $l"
    exit 1
  }
  cp -L "$TPREFIX/share/tessdata/$l.traineddata" \
    "$ROOT/resources/tesseract/share/tessdata/"
done

"$ROOT/scripts/bundle_tesseract.command"

echo ""
echo "Validating bundled fonts…"
"$PY" - <<'PY'
from pathlib import Path
from fontTools.ttLib import TTFont

root = Path.cwd() / "resources" / "fonts"
for p in root.glob("*.ttf"):
    TTFont(str(p), fontNumber=0).close()
    print("OK:", p.name)
PY

echo ""
echo "SETUP COMPLETE."
echo "Run ./build-mac.command to create the .app and .dmg."

#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

BIN="$PWD/resources/tesseract/bin/tesseract"
LIB="$PWD/resources/tesseract/lib"
mkdir -p "$LIB"

copydeps() {
  local f="$1"
  otool -L "$f" | tail -n +2 | sed 's/^[[:space:]]*//' | cut -d' ' -f1 |
  while read -r d; do
    case "$d" in
      /System/*|/usr/lib/*|@rpath/*|@loader_path/*|@executable_path/*|'') continue ;;
    esac

    local n dest
    n="$(basename "$d")"
    dest="$LIB/$n"

    if [ ! -e "$dest" ]; then
      cp -L "$d" "$dest"
      chmod u+w "$dest" || true
      install_name_tool -id "@loader_path/$n" "$dest" || true
      copydeps "$dest"
    fi

    install_name_tool -change "$d" "@loader_path/../lib/$n" "$f" || true
  done
}

copydeps "$BIN"
chmod +x "$BIN"

echo "Bundled Tesseract:"
file "$BIN"

# PDF Translator — Mac product build

## What this build fixes

- Static Noto TTF files are bundled; no runtime font download.
- Uses Meta's **M2M100 418M** translation model instead of NLLB.
- M2M100 418M is MIT-licensed and lists English, Russian, Thai, Indonesian,
  Latvian, and Georgian among its supported languages.
- Translation model is downloaded into `resources/models/m2m100_418M` at build
  time and loaded with `local_files_only=True`.
- Tesseract and the six OCR language packs are copied into application resources.
- Development packages are installed only into `.venv`.
- The finished app does not require Python, Homebrew, Tesseract, or Internet.
- PyInstaller builds a normal macOS `.app` and a `.dmg`.

## Build on macOS

1. Install Python 3.12+ and Homebrew on the BUILD Mac.
2. Extract this folder.
3. Double-click `Install.command`.
4. Wait for the model and OCR resources to finish.
5. Double-click `build-mac.command`.
6. Get:
   - `release/PDF Translator.app`
   - `release/PDFTranslator-macOS.dmg`

## Important

The build Mac needs Internet access because it downloads the M2M100 model and
Homebrew OCR dependencies. The resulting application is designed to run
without Internet access.

### Commercial licensing

M2M100 418M is listed as MIT on its model card. Verify the model's current
license and all redistributed dependencies before commercial distribution.

This application is a machine translation tool, not a certified translation
service.

### macOS signing and notarization

For public distribution outside the Mac App Store, use an Apple Developer ID
certificate, enable Hardened Runtime, sign all executable code, and notarize
the application. Apple recommends notarization for Developer ID-distributed
software.

Set your signing identity before building:

    export SIGN_IDENTITY="Developer ID Application: Your Company (TEAMID)"
    ./build-mac.command

The build script will sign the `.app`. You must then notarize the final
deliverable with Apple's `notarytool` and staple the ticket.

### Current PDF behavior

The application OCRs PDFs/images and creates a new translated PDF with clean
text layout. It does not yet reconstruct the exact original visual layout,
tables, forms, or image placement.


## macOS crash fix
This release uses PySide6 instead of Tkinter to avoid legacy Tk/Carbon dependencies on modern macOS. The build checks the final executable with `otool -L` and refuses a direct Carbon/Tk/Tcl dependency.

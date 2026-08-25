# macOS crash fix: Carbon.framework missing

The crash report showed:

    Library not loaded:
    /System/Library/Frameworks/Carbon.framework/Versions/A/Carbon

The previous UI used Tkinter. On the affected Apple Silicon/macOS build, the
frozen executable carried a legacy Tk/Carbon dependency. Modern macOS should
not require the application itself to link directly to that legacy Carbon
binary.

This version replaces Tkinter with PySide6 and explicitly excludes tkinter,
_tkinter and FixTk from PyInstaller. The build script also runs `otool -L` and
fails the build if the main executable directly links to Carbon, Tk or Tcl.

Important:
- Rebuild the application from this version. Do not reuse the old `.app`.
- The GitHub workflow must use the `.github/workflows/build-macos.yml` in this
  package.
- A GitHub build produced by an older workflow is still the old app.

If an already-built app is being tested, remove it first and install the new
DMG. A clean build is recommended.

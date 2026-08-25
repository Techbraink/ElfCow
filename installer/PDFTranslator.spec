from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPEC).resolve().parents[1]

datas = []
binaries = []
hidden = []

for package in [
    "PySide6",
    "torch",
    "transformers",
    "sentencepiece",
    "fitz",
    "reportlab",
    "pytesseract",
]:
    try:
        d, b, h = collect_all(package)
        datas += d
        binaries += b
        hidden += h
    except Exception:
        pass

datas.append((str(ROOT / "resources"), "resources"))

a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT / "app")],
    datas=datas,
    binaries=binaries,
    hiddenimports=hidden + [
        "transformers.models.m2m_100",
        "transformers.models.m2m_100.tokenization_m2m_100",
        "transformers.models.m2m_100.modeling_m2m_100",
    ],
    excludes=[
        "tkinter",
        "_tkinter",
        "Tkinter",
        "FixTk",
    ],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PDF Translator",
    console=False,
)

app = BUNDLE(
    exe,
    name="PDF Translator.app",
    bundle_identifier="com.offlinedocumenttranslator.pdftranslator",
    version="1.0.0",
    info_plist={
        "CFBundleName": "PDF Translator",
        "CFBundleDisplayName": "PDF Translator",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "12.0",
    },
)

from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]

fonts = [
    "NotoSans-Regular.ttf",
    "NotoSansThai-Regular.ttf",
    "NotoSansGeorgian-Regular.ttf",
]
for name in fonts:
    p = ROOT / "resources" / "fonts" / name
    if not p.exists():
        raise SystemExit(f"Missing font: {p}")
    TTFont(str(p)).close()

print("Fonts OK.")

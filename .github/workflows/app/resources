from pathlib import Path
import sys

def root():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "resources"
    return Path(__file__).resolve().parents[1] / "resources"

def resource(*parts):
    return root().joinpath(*parts)

import io
import os
import shutil
from pathlib import Path

import fitz
import pytesseract
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.pagesizes import A4

from languages import OCR_CODES
from resources import resource

FONTS = {
    "English": "NotoSans-Regular.ttf",
    "Russian": "NotoSans-Regular.ttf",
    "Indonesian": "NotoSans-Regular.ttf",
    "Latvian": "NotoSans-Regular.ttf",
    "Thai": "NotoSansThai-Regular.ttf",
    "Georgian": "NotoSansGeorgian-Regular.ttf",
}


def configure_ocr():
    exe = resource("tesseract", "bin", "tesseract")
    data = resource("tesseract", "share", "tessdata")

    if exe.exists():
        pytesseract.pytesseract.tesseract_cmd = str(exe)
        os.environ["TESSDATA_PREFIX"] = str(data)
        return

    found = shutil.which("tesseract")
    if found:
        pytesseract.pytesseract.tesseract_cmd = found
        return

    raise RuntimeError("Bundled OCR engine is missing.")


configure_ocr()


def ocr(img, lang):
    try:
        return pytesseract.image_to_string(
            img, lang=lang, config="--psm 3"
        )
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError("Bundled OCR engine is missing.") from exc
    except pytesseract.TesseractError as exc:
        raise RuntimeError(f"OCR failed: {exc}") from exc


def extract_pages(path, src, cb=None):
    cb = cb or (lambda _m: None)
    p = Path(path)
    suffix = p.suffix.lower()
    lang = OCR_CODES[src]

    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
        with Image.open(p) as image:
            image = image.convert("RGB")
            return [[x.strip() for x in ocr(image, lang).splitlines() if x.strip()]]

    if suffix != ".pdf":
        raise ValueError("Please choose a PDF or supported image.")

    doc = fitz.open(p)
    pages = []

    try:
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()

            # OCR only pages that appear to have no useful selectable text.
            if len(text) < 20:
                cb(f"OCR: page {i + 1}/{len(doc)}")
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(2.5, 2.5),
                    alpha=False,
                )
                text = ocr(
                    Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB"),
                    lang,
                ).strip()

            paragraphs = [
                x.strip() for x in text.split("\n\n") if x.strip()
            ]
            if not paragraphs:
                paragraphs = [
                    x.strip() for x in text.splitlines() if x.strip()
                ]

            pages.append(paragraphs or [""])
    finally:
        doc.close()

    return pages


def font_for(target):
    p = resource("fonts", FONTS[target])
    if not p.exists():
        raise RuntimeError("Bundled font missing: " + p.name)

    name = p.stem
    if name not in pdfmetrics.getRegisteredFontNames():
        try:
            pdfmetrics.registerFont(TTFont(name, str(p)))
        except Exception as exc:
            raise RuntimeError(
                f"Bundled font could not be loaded: {p.name}"
            ) from exc

    return name


def wrap(text, font, size, max_width):
    lines = []
    current = ""

    # Preserve whitespace-separated words where possible, but fall back to
    # character wrapping for scripts/long tokens without spaces.
    for word in text.split():
        candidate = (current + " " + word).strip()

        if stringWidth(candidate, font, size) <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
            current = ""

        if stringWidth(word, font, size) <= max_width:
            current = word
            continue

        piece = ""
        for char in word:
            if stringWidth(piece + char, font, size) <= max_width:
                piece += char
            else:
                if piece:
                    lines.append(piece)
                piece = char
        current = piece

    if current:
        lines.append(current)

    return lines or [""]


def write_pdf(path, pages, target):
    font = font_for(target)
    c = canvas.Canvas(str(path), pagesize=A4)

    width, height = A4
    margin = 48
    font_size = 11
    line_height = 16

    for page_paragraphs in pages:
        y = height - margin
        c.setFont(font, font_size)

        for paragraph in page_paragraphs:
            for line in wrap(
                paragraph,
                font,
                font_size,
                width - 2 * margin,
            ):
                if y < margin:
                    c.showPage()
                    c.setFont(font, font_size)
                    y = height - margin

                c.drawString(margin, y, line)
                y -= line_height

            y -= 8

        c.showPage()

    c.save()

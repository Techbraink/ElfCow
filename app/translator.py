import re
from pathlib import Path

import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

from languages import LANG_CODES
from resources import resource

MODEL = resource("models", "m2m100_418M")


class Translator:
    """Offline many-to-many translator using the MIT-licensed M2M100 418M model."""

    def __init__(self, progress_callback=None):
        self.cb = progress_callback or (lambda _m: None)
        if not (MODEL / "config.json").exists():
            raise RuntimeError(
                "Bundled translation model is missing. Run Install.command before building."
            )

        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.cb("Loading offline translation model…")

        self.tokenizer = M2M100Tokenizer.from_pretrained(
            MODEL, local_files_only=True
        )
        self.model = M2M100ForConditionalGeneration.from_pretrained(
            MODEL, local_files_only=True
        ).to(self.device)
        self.model.eval()

        missing = [
            code for code in LANG_CODES.values()
            if code not in self.tokenizer.lang_code_to_token
        ]
        if missing:
            raise RuntimeError(
                "The bundled translation model is missing language codes: "
                + ", ".join(missing)
            )

        self.cb("Translation model ready.")

    def translate(self, text, src, dst):
        if not text.strip():
            return ""

        self.tokenizer.src_lang = LANG_CODES[src]
        target_id = self.tokenizer.get_lang_id(LANG_CODES[dst])

        chunks = self._chunks(text)
        translated = []

        for chunk in chunks:
            encoded = self.tokenizer(
                chunk,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}

            with torch.inference_mode():
                generated = self.model.generate(
                    **encoded,
                    forced_bos_token_id=target_id,
                    max_length=512,
                    num_beams=4,
                    early_stopping=True,
                )

            translated.append(
                self.tokenizer.batch_decode(
                    generated, skip_special_tokens=True
                )[0]
            )

        return " ".join(translated)

    @staticmethod
    def _chunks(text, max_chars=900):
        sentences = re.split(r"(?<=[.!?।！？])\s+", text.strip())
        result, current = [], ""

        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= max_chars:
                current = (current + " " + sentence).strip()
            else:
                if current:
                    result.append(current)
                current = sentence

        if current:
            result.append(current)

        return result or [text]

import os
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from languages import LANG_CODES
from translator import Translator
from pdf_utils import extract_pages, write_pdf


class Worker(QObject):
    status = Signal(str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, path, src, dst):
        super().__init__()
        self.path = path
        self.src = src
        self.dst = dst

    @Slot()
    def run(self):
        try:
            translator = Translator(self.status.emit)
            pages = extract_pages(self.path, self.src, self.status.emit)

            output_pages = []
            total = sum(len(page) for page in pages) or 1
            done = 0

            for page in pages:
                translated_page = []
                for paragraph in page:
                    translated_page.append(
                        translator.translate(paragraph, self.src, self.dst)
                    )
                    done += 1
                    self.status.emit(f"Translating {done}/{total}…")
                output_pages.append(translated_page)

            p = Path(self.path)
            output = p.with_name(f"{p.stem}_{self.dst}.pdf")
            write_pdf(output, output_pages, self.dst)
            self.finished.emit(str(output))
        except Exception as exc:
            self.failed.emit(str(exc))


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Translator")
        self.setMinimumSize(720, 540)
        self.worker_thread = None
        self.worker = None
        self.path = None

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("PDF Translator")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Offline OCR and translation • English • Russian • Thai • "
            "Indonesian • Latvian • Georgian"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.choose_btn = QPushButton("Choose PDF or Image…")
        self.choose_btn.setMinimumHeight(46)
        self.choose_btn.clicked.connect(self.choose)
        layout.addWidget(self.choose_btn)

        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)
        self.file_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.file_label)

        row = QHBoxLayout()
        row.addWidget(QLabel("From:"))
        self.src = QComboBox()
        self.src.addItems(LANG_CODES.keys())
        self.src.setCurrentText("English")
        row.addWidget(self.src, 1)

        row.addWidget(QLabel("To:"))
        self.dst = QComboBox()
        self.dst.addItems(LANG_CODES.keys())
        self.dst.setCurrentText("Russian")
        row.addWidget(self.dst, 1)
        layout.addLayout(row)

        self.translate_btn = QPushButton("Translate Offline")
        self.translate_btn.setMinimumHeight(50)
        self.translate_btn.clicked.connect(self.start)
        layout.addWidget(self.translate_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.status = QLabel("Ready — translation and OCR run locally.")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        layout.addStretch()
        self.setCentralWidget(root)

    def choose(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose PDF or image",
            "",
            "PDF and images (*.pdf *.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp)",
        )
        if path:
            self.path = path
            self.file_label.setText(Path(path).name)

    def start(self):
        if not self.path:
            QMessageBox.warning(self, "Choose a file", "Please choose a PDF or image first.")
            return

        src = self.src.currentText()
        dst = self.dst.currentText()
        if src == dst:
            QMessageBox.warning(self, "Same language", "Choose different source and target languages.")
            return

        self.translate_btn.setEnabled(False)
        self.choose_btn.setEnabled(False)
        self.src.setEnabled(False)
        self.dst.setEnabled(False)
        self.progress.show()
        self.status.setText("Starting offline translation…")

        self.worker = Worker(self.path, src, dst)
        self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)
        self.worker.status.connect(self.set_status)
        self.worker.finished.connect(self.completed)
        self.worker.failed.connect(self.failed)
        self.worker_thread.start()

    @Slot(str)
    def set_status(self, message):
        self.status.setText(message)

    @Slot(str)
    def completed(self, output):
        self.reset_controls()
        self.status.setText("Complete.")
        QMessageBox.information(
            self,
            "Translation complete",
            f"Saved to:\n\n{output}",
        )

    @Slot(str)
    def failed(self, message):
        self.reset_controls()
        self.status.setText("Translation failed.")
        QMessageBox.critical(self, "Translation failed", message)

    def reset_controls(self):
        self.progress.hide()
        self.translate_btn.setEnabled(True)
        self.choose_btn.setEnabled(True)
        self.src.setEnabled(True)
        self.dst.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Translator")
    app.setOrganizationName("PDF Translator")
    window = App()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

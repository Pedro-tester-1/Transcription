import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar, QMessageBox,
    QStackedWidget, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon


# ── Traducciones ──────────────────────────────────────────────────────────────

STRINGS = {
    "en": {
        "app_title":       "Media Converter",
        "subtitle":        "What do you want to convert?",
        "btn_mp4_mp3":     "MP4  ->  MP3",
        "btn_mp4_text":    "MP4  ->  Text",
        "btn_mp3_text":    "MP3  ->  Text",
        "back":            "<- Back",
        "browse":          "Browse file",
        "convert":         "Convert",
        "no_file":         "No file selected",
        "starting":        "Starting...",
        "converting_mp3":  "Converting to MP3...",
        "loading_model":   "Loading transcription model...",
        "transcribing":    "Transcribing... (this may take a few minutes)",
        "converting_vid":  "Converting video to audio...",
        "transcribing2":   "Transcribing audio to text...",
        "done":            "Conversion complete",
        "save_title":      "Save converted file",
        "save_ok":         "File saved at:\n{}",
        "save_skip":       "File available at:\n{}",
        "ready":           "Done",
        "error_title":     "Error",
        "error_msg":       "An error occurred:\n\n{}",
        "filter_mp3":      "MP3 file (*.mp3)",
        "filter_txt":      "Text file (*.txt)",
        "filter_all":      "All files (*)",
        "filter_video":    "Video files (*.mp4)",
        "filter_audio":    "Audio files (*.mp3)",
        "mode_mp4_mp3":    "MP4 -> MP3",
        "mode_mp4_text":   "MP4 -> Text",
        "mode_mp3_text":   "MP3 -> Text",
        "language":        "Language",
    },
    "es": {
        "app_title":       "Media Converter",
        "subtitle":        "Que quieres convertir hoy?",
        "btn_mp4_mp3":     "MP4  ->  MP3",
        "btn_mp4_text":    "MP4  ->  Texto",
        "btn_mp3_text":    "MP3  ->  Texto",
        "back":            "<- Volver",
        "browse":          "Buscar archivo",
        "convert":         "Convertir",
        "no_file":         "Ningun archivo seleccionado",
        "starting":        "Iniciando...",
        "converting_mp3":  "Convirtiendo a MP3...",
        "loading_model":   "Cargando modelo de transcripcion...",
        "transcribing":    "Transcribiendo... (puede tardar unos minutos)",
        "converting_vid":  "Convirtiendo video a audio...",
        "transcribing2":   "Transcribiendo audio a texto...",
        "done":            "Conversion completada",
        "save_title":      "Guardar archivo convertido",
        "save_ok":         "Archivo guardado en:\n{}",
        "save_skip":       "Archivo disponible en:\n{}",
        "ready":           "Listo",
        "error_title":     "Error",
        "error_msg":       "Ocurrio un error:\n\n{}",
        "filter_mp3":      "Archivo MP3 (*.mp3)",
        "filter_txt":      "Archivo de texto (*.txt)",
        "filter_all":      "Todos los archivos (*)",
        "filter_video":    "Archivos de video (*.mp4)",
        "filter_audio":    "Archivos de audio (*.mp3)",
        "mode_mp4_mp3":    "MP4 -> MP3",
        "mode_mp4_text":   "MP4 -> Texto",
        "mode_mp3_text":   "MP3 -> Texto",
        "language":        "Idioma",
    },
}

# Idioma activo global
current_lang = "en"

def t(key):
    return STRINGS[current_lang].get(key, key)


# ── Icono ─────────────────────────────────────────────────────────────────────

def make_icon():
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    return QIcon(icon_path)


# ── Worker thread ──────────────────────────────────────────────────────────────

class ConvertWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, mode, input_path):
        super().__init__()
        self.mode = mode
        self.input_path = input_path

    def run(self):
        try:
            if self.mode == "mp4_mp3":
                result = self._to_mp3(self.input_path)
            elif self.mode == "mp3_text":
                result = self._to_text(self.input_path)
            elif self.mode == "mp4_text":
                self.progress.emit(t("converting_vid"))
                mp3_path = self._to_mp3(self.input_path, temp=True)
                self.progress.emit(t("transcribing2"))
                result = self._to_text(mp3_path)
                os.remove(mp3_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _to_mp3(self, path, temp=False):
        suffix = "_temp.mp3" if temp else ".mp3"
        out = path.rsplit(".", 1)[0] + suffix
        self.progress.emit(t("converting_mp3"))
        subprocess.run(
            ["ffmpeg", "-y", "-i", path, "-q:a", "0", "-map", "a", out],
            check=True, capture_output=True
        )
        return out

    def _to_text(self, path):
        import whisper
        self.progress.emit(t("loading_model"))
        model = whisper.load_model("base")
        self.progress.emit(t("transcribing"))
        result = model.transcribe(path)
        txt_path = path.rsplit(".", 1)[0] + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        return txt_path


# ── Pantalla principal ────────────────────────────────────────────────────────

class ModeSelector(QWidget):
    mode_selected   = pyqtSignal(str)
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(20)
        root.setContentsMargins(40, 30, 40, 40)

        # Barra superior con selector de idioma tipo pill
        top_bar = QHBoxLayout()
        top_bar.addStretch()

        pill_container = QFrame()
        pill_container.setFixedHeight(34)
        pill_container.setStyleSheet("""
            QFrame {
                background: #1e1e2e;
                border-radius: 17px;
                border: 1px solid #37474F;
            }
        """)
        pill_layout = QHBoxLayout(pill_container)
        pill_layout.setContentsMargins(4, 4, 4, 4)
        pill_layout.setSpacing(2)

        self.lang_buttons = {}
        for label, lang in [("EN", "en"), ("ES", "es")]:
            btn = QPushButton(label)
            btn.setFixedSize(44, 24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, l=lang: self._on_lang_change(l))
            pill_layout.addWidget(btn)
            self.lang_buttons[lang] = btn

        self._apply_pill_styles("en")
        top_bar.addWidget(pill_container)
        root.addLayout(top_bar)

        self.title = QLabel(t("app_title"))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.title.setStyleSheet("color: #e0e0e0; margin-bottom: 10px;")
        root.addWidget(self.title)

        self.subtitle = QLabel(t("subtitle"))
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setFont(QFont("Segoe UI", 13))
        self.subtitle.setStyleSheet("color: #9e9e9e; margin-bottom: 20px;")
        root.addWidget(self.subtitle)

        btn_defs = [
            ("btn_mp4_mp3",  "mp4_mp3",  "#1565C0", "#1976D2"),
            ("btn_mp4_text", "mp4_text", "#6A1B9A", "#7B1FA2"),
            ("btn_mp3_text", "mp3_text", "#1B5E20", "#2E7D32"),
        ]
        self.mode_buttons = {}
        for key, mode, color, hover in btn_defs:
            btn = QPushButton(t(key))
            btn.setFixedHeight(70)
            btn.setFont(QFont("Segoe UI", 14))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}; color: white;
                    border-radius: 12px; border: none; padding: 0 20px;
                }}
                QPushButton:hover {{ background-color: {hover}; }}
                QPushButton:pressed {{ background-color: {color}; padding-top: 3px; }}
            """)
            btn.clicked.connect(lambda _, m=mode: self.mode_selected.emit(m))
            root.addWidget(btn)
            self.mode_buttons[key] = btn

        root.addStretch()

    def _apply_pill_styles(self, active_lang):
        for lang, btn in self.lang_buttons.items():
            if lang == active_lang:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #1565C0;
                        color: white;
                        border-radius: 12px;
                        border: none;
                        font-size: 11px;
                        font-weight: bold;
                    }
                """)
                btn.setChecked(True)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #757575;
                        border-radius: 12px;
                        border: none;
                        font-size: 11px;
                    }
                    QPushButton:hover { color: #e0e0e0; }
                """)
                btn.setChecked(False)

    def _on_lang_change(self, lang):
        self._apply_pill_styles(lang)
        self.language_changed.emit(lang)

    def retranslate(self):
        self.title.setText(t("app_title"))
        self.subtitle.setText(t("subtitle"))
        for key, btn in self.mode_buttons.items():
            btn.setText(t(key))


# ── Pantalla de conversion ────────────────────────────────────────────────────

class ConverterScreen(QWidget):
    go_back = pyqtSignal()

    MODE_KEY = {
        "mp4_mp3":  ("mode_mp4_mp3", "filter_video"),
        "mp4_text": ("mode_mp4_text","filter_video"),
        "mp3_text": ("mode_mp3_text","filter_audio"),
    }

    def __init__(self):
        super().__init__()
        self.mode = None
        self.input_path = None
        self.worker = None
        self._converting = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)

        self.back_btn = QPushButton(t("back"))
        self.back_btn.setFixedWidth(110)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #90CAF9; border: none; font-size: 13px; }
            QPushButton:hover { color: #BBDEFB; }
            QPushButton:disabled { color: #455A64; }
        """)
        self.back_btn.clicked.connect(self._handle_back)
        layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.title_label = QLabel()
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #e0e0e0;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        drop_frame = QFrame()
        drop_frame.setFixedHeight(140)
        drop_frame.setStyleSheet("""
            QFrame { border: 2px dashed #555; border-radius: 14px; background: #1e1e2e; }
        """)
        drop_layout = QVBoxLayout(drop_frame)

        self.file_label = QLabel(t("no_file"))
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #757575; font-size: 13px; border: none;")
        drop_layout.addWidget(self.file_label)

        self.browse_btn = QPushButton(t("browse"))
        self.browse_btn.setFixedSize(180, 40)
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.setStyleSheet("""
            QPushButton { background: #37474F; color: #e0e0e0; border-radius: 8px; border: none; font-size: 13px; }
            QPushButton:hover { background: #455A64; }
            QPushButton:disabled { background: #263238; color: #546E7A; }
        """)
        self.browse_btn.clicked.connect(self._browse_file)
        drop_layout.addWidget(self.browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(drop_frame)

        self.convert_btn = QPushButton(t("convert"))
        self.convert_btn.setFixedHeight(55)
        self.convert_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.convert_btn.setEnabled(False)
        self.convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convert_btn.setStyleSheet("""
            QPushButton { background: #0D47A1; color: white; border-radius: 10px; border: none; }
            QPushButton:hover { background: #1565C0; }
            QPushButton:disabled { background: #37474F; color: #757575; }
        """)
        self.convert_btn.clicked.connect(self._start_conversion)
        layout.addWidget(self.convert_btn)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #9e9e9e; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet("""
            QProgressBar { border-radius: 4px; background: #37474F; border: none; }
            QProgressBar::chunk { background: #1976D2; border-radius: 4px; }
        """)
        layout.addWidget(self.progress)
        layout.addStretch()

    def set_mode(self, mode):
        self.mode = mode
        self.input_path = None
        self._converting = False
        self.file_label.setText(t("no_file"))
        self.file_label.setStyleSheet("color: #757575; font-size: 13px; border: none;")
        self.convert_btn.setEnabled(False)
        self.status_label.setText("")
        self.progress.setVisible(False)
        self.back_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.retranslate()

    def retranslate(self):
        self.back_btn.setText(t("back"))
        self.browse_btn.setText(t("browse"))
        self.convert_btn.setText(t("convert"))
        if not self.input_path:
            self.file_label.setText(t("no_file"))
        if self.mode:
            mode_key, _ = self.MODE_KEY[self.mode]
            self.title_label.setText(t(mode_key))

    def _handle_back(self):
        if not self._converting:
            self.go_back.emit()

    def _browse_file(self):
        _, filter_key = self.MODE_KEY[self.mode]
        path, _ = QFileDialog.getOpenFileName(self, t("save_title"), "", t(filter_key))
        if path:
            self.input_path = path
            self.file_label.setText(os.path.basename(path))
            self.file_label.setStyleSheet("color: #e0e0e0; font-size: 13px; border: none;")
            self.convert_btn.setEnabled(True)

    def _set_converting(self, active):
        self._converting = active
        self.back_btn.setEnabled(not active)
        self.browse_btn.setEnabled(not active)
        self.convert_btn.setEnabled(not active)
        self.progress.setVisible(active)

    def _start_conversion(self):
        self._set_converting(True)
        self.status_label.setText(t("starting"))
        self.worker = ConvertWorker(self.mode, self.input_path)
        self.worker.progress.connect(self.status_label.setText)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, result_path):
        self._set_converting(False)
        self.status_label.setText(t("done"))
        ext = os.path.splitext(result_path)[1]
        filt = {".mp3": t("filter_mp3"), ".txt": t("filter_txt")}
        save_path, _ = QFileDialog.getSaveFileName(
            self, t("save_title"), os.path.basename(result_path),
            filt.get(ext, t("filter_all"))
        )
        if save_path:
            import shutil
            shutil.move(result_path, save_path)
            QMessageBox.information(self, t("ready"), t("save_ok").format(save_path))
        else:
            QMessageBox.information(self, t("ready"), t("save_skip").format(result_path))
        self.convert_btn.setEnabled(True)

    def _on_error(self, msg):
        self._set_converting(False)
        self.status_label.setText(t("error_title"))
        self.convert_btn.setEnabled(bool(self.input_path))
        QMessageBox.critical(self, t("error_title"), t("error_msg").format(msg))


# ── Ventana principal ──────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Converter")
        self.setMinimumSize(480, 540)
        self.resize(520, 580)
        self.setWindowIcon(make_icon())
        self.setStyleSheet("QMainWindow { background: #121212; } QWidget { background: #121212; }")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.mode_screen = ModeSelector()
        self.conv_screen = ConverterScreen()

        self.stack.addWidget(self.mode_screen)
        self.stack.addWidget(self.conv_screen)

        self.mode_screen.mode_selected.connect(self._go_to_converter)
        self.mode_screen.language_changed.connect(self._change_language)
        self.conv_screen.go_back.connect(lambda: self.stack.setCurrentIndex(0))

    def _go_to_converter(self, mode):
        self.conv_screen.set_mode(mode)
        self.stack.setCurrentIndex(1)

    def _change_language(self, lang):
        global current_lang
        current_lang = lang
        self.mode_screen.retranslate()
        self.conv_screen.retranslate()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#121212"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e2e"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar, QMessageBox,
    QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon


# ── Icono SVG generado en memoria ─────────────────────────────────────────────

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
                self.progress.emit("Convirtiendo video a audio...")
                mp3_path = self._to_mp3(self.input_path, temp=True)
                self.progress.emit("Transcribiendo audio a texto...")
                result = self._to_text(mp3_path)
                os.remove(mp3_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _to_mp3(self, path, temp=False):
        suffix = "_temp.mp3" if temp else ".mp3"
        out = path.rsplit(".", 1)[0] + suffix
        self.progress.emit("Convirtiendo a MP3...")
        subprocess.run(
            ["ffmpeg", "-y", "-i", path, "-q:a", "0", "-map", "a", out],
            check=True, capture_output=True
        )
        return out

    def _to_text(self, path):
        import whisper
        self.progress.emit("Cargando modelo de transcripcion...")
        model = whisper.load_model("base")
        self.progress.emit("Transcribiendo... (puede tardar unos minutos)")
        result = model.transcribe(path)
        txt_path = path.rsplit(".", 1)[0] + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        return txt_path


# ── Pantalla de seleccion de modo ─────────────────────────────────────────────

class ModeSelector(QWidget):
    mode_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Media Converter")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0e0; margin-bottom: 10px;")
        layout.addWidget(title)

        subtitle = QLabel("Que quieres convertir hoy?")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 13))
        subtitle.setStyleSheet("color: #9e9e9e; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        buttons = [
            ("MP4  ->  MP3",   "mp4_mp3",  "#1565C0", "#1976D2"),
            ("MP4  ->  Texto", "mp4_text", "#6A1B9A", "#7B1FA2"),
            ("MP3  ->  Texto", "mp3_text", "#1B5E20", "#2E7D32"),
        ]

        for label, mode, color, hover in buttons:
            btn = QPushButton(label)
            btn.setFixedHeight(70)
            btn.setFont(QFont("Segoe UI", 14))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border-radius: 12px;
                    border: none;
                    padding: 0 20px;
                }}
                QPushButton:hover {{ background-color: {hover}; }}
                QPushButton:pressed {{ background-color: {color}; padding-top: 3px; }}
            """)
            btn.clicked.connect(lambda _, m=mode: self.mode_selected.emit(m))
            layout.addWidget(btn)

        layout.addStretch()


# ── Pantalla de conversion ────────────────────────────────────────────────────

class ConverterScreen(QWidget):
    go_back = pyqtSignal()

    MODE_LABELS = {
        "mp4_mp3":  ("MP4 -> MP3",   "Archivos de video (*.mp4)"),
        "mp4_text": ("MP4 -> Texto", "Archivos de video (*.mp4)"),
        "mp3_text": ("MP3 -> Texto", "Archivos de audio (*.mp3)"),
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

        self.back_btn = QPushButton("<- Volver")
        self.back_btn.setFixedWidth(100)
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

        # Zona de archivo
        drop_frame = QFrame()
        drop_frame.setFixedHeight(140)
        drop_frame.setStyleSheet("""
            QFrame { border: 2px dashed #555; border-radius: 14px; background: #1e1e2e; }
        """)
        drop_layout = QVBoxLayout(drop_frame)

        self.file_label = QLabel("Ningun archivo seleccionado")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #757575; font-size: 13px; border: none;")
        drop_layout.addWidget(self.file_label)

        self.browse_btn = QPushButton("Buscar archivo")
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

        self.convert_btn = QPushButton("Convertir")
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
        self.file_label.setText("Ningun archivo seleccionado")
        self.file_label.setStyleSheet("color: #757575; font-size: 13px; border: none;")
        self.convert_btn.setEnabled(False)
        self.status_label.setText("")
        self.progress.setVisible(False)
        self.back_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        label, _ = self.MODE_LABELS[mode]
        self.title_label.setText(label)

    def _handle_back(self):
        if self._converting:
            # No deberia llegar aqui porque el boton esta deshabilitado, pero por si acaso
            return
        self.go_back.emit()

    def _browse_file(self):
        _, file_filter = self.MODE_LABELS[self.mode]
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", file_filter)
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
        self.status_label.setText("Iniciando...")

        self.worker = ConvertWorker(self.mode, self.input_path)
        self.worker.progress.connect(self.status_label.setText)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, result_path):
        self._set_converting(False)
        self.status_label.setText("Conversion completada")

        ext = os.path.splitext(result_path)[1]
        filters = {".mp3": "Archivo MP3 (*.mp3)", ".txt": "Archivo de texto (*.txt)"}
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo convertido",
            os.path.basename(result_path),
            filters.get(ext, "Todos los archivos (*)")
        )
        if save_path:
            import shutil
            shutil.move(result_path, save_path)
            QMessageBox.information(self, "Listo", f"Archivo guardado en:\n{save_path}")
        else:
            QMessageBox.information(self, "Listo", f"Archivo disponible en:\n{result_path}")

        self.convert_btn.setEnabled(True)

    def _on_error(self, msg):
        self._set_converting(False)
        self.status_label.setText("Error en la conversion")
        self.convert_btn.setEnabled(bool(self.input_path))
        QMessageBox.critical(self, "Error", f"Ocurrio un error:\n\n{msg}")


# ── Ventana principal ──────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Converter")
        self.setMinimumSize(480, 520)
        self.resize(520, 560)
        self.setWindowIcon(make_icon())
        self.setStyleSheet("QMainWindow { background: #121212; } QWidget { background: #121212; }")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.mode_screen = ModeSelector()
        self.conv_screen = ConverterScreen()

        self.stack.addWidget(self.mode_screen)
        self.stack.addWidget(self.conv_screen)

        self.mode_screen.mode_selected.connect(self._go_to_converter)
        self.conv_screen.go_back.connect(lambda: self.stack.setCurrentIndex(0))

    def _go_to_converter(self, mode):
        self.conv_screen.set_mode(mode)
        self.stack.setCurrentIndex(1)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(make_icon())

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#121212"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e2e"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

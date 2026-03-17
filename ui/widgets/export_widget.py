"""
Export widget for Black Mirror results.
Buttons for TXT/HTML/PDF download + clipboard.
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QVBoxLayout, 
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Signal
from pathlib import Path
from utils.export import Exporter
from core.models import ScanSession
from ui.styles import Colors


class ExportWidget(QWidget):
    """Виджет экспорта с кнопками TXT/HTML/PDF/Copy."""

    session_exported = Signal(str)  # path to file

    def __init__(self, session: ScanSession = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # TXT
        txt_btn = QPushButton("📄 TXT")
        txt_btn.setToolTip("Сохранить как TXT")
        txt_btn.clicked.connect(lambda: self._export("txt"))
        layout.addWidget(txt_btn)

        # HTML
        html_btn = QPushButton("🌐 HTML")
        html_btn.setToolTip("Сохранить как HTML")
        html_btn.clicked.connect(lambda: self._export("html"))
        layout.addWidget(html_btn)

        # PDF
        pdf_btn = QPushButton("📕 PDF")
        pdf_btn.setToolTip("Сохранить как PDF")
        pdf_btn.clicked.connect(lambda: self._export("pdf"))
        layout.addWidget(pdf_btn)

        # Copy TXT
        copy_btn = QPushButton("📋 Copy")
        copy_btn.setToolTip("Копировать TXT в буфер")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        layout.addWidget(copy_btn)

        self.setStyleSheet("""
            QPushButton {
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 4px;
                color: #fff;
                padding: 8px 12px;
                font-size: 12px;
                min-width: 60px;
            }
            QPushButton:hover {
                background: #252525;
                border-color: #2196f3;
            }
        """)

    def set_session(self, session: ScanSession):
        """Update session for export."""
        self.session = session

    def _export(self, fmt: str):
        if not self.session:
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта. Запустите сканирование.")
            return

        path = QFileDialog.getSaveFileName(
            self, "Сохранить отчет", f"report.{fmt}", 
            f"Black Mirror Report (*.{fmt})"
        )[0]

        if path:
            try:
                if fmt == "txt":
                    file_path = Exporter.export_txt(self.session, path)
                elif fmt == "html":
                    file_path = Exporter.export_html(self.session, path)
                elif fmt == "pdf":
                    file_path = Exporter.export_pdf(self.session, path)
                
                self.session_exported.emit(file_path)
                QMessageBox.information(self, "Успех", f"Отчет сохранен: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {e}")

    def _copy_to_clipboard(self):
        if not self.session:
            return

        try:
            from PySide6.QtWidgets import QApplication
            txt_content = Path(Exporter.export_txt(self.session, "/tmp/tmp_report.txt")).read_text()
            QApplication.clipboard().setText(txt_content)
            QMessageBox.information(self, "Успех", "Отчет скопирован в буфер обмена!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка копирования: {e}")


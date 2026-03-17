"""
Виджет прогресса сканирования для Black Mirror UI.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                QProgressBar, QLabel, QFrame)
from PySide6.QtCore import Qt, Signal


class ProgressWidget(QWidget):
    """Виджет отображения прогресса сканирования"""
    
    progress_update = Signal(int, int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Заголовок и статус
        header_layout = QHBoxLayout()
        
        self.status_label = QLabel("Готов к сканированию")
        self.status_label.setObjectName("subtitle")
        
        self.count_label = QLabel("0 / 0")
        self.count_label.setObjectName("subtitle")
        self.count_label.setAlignment(Qt.AlignRight)
        
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        layout.addWidget(self.progress_bar)
        
        # Текущая проверка
        self.current_check_label = QLabel("")
        self.current_check_label.setWordWrap(True)
        self.current_check_label.setStyleSheet("color: #a0a0a0;")
        
        layout.addWidget(self.current_check_label)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #333333;")
        
        layout.addWidget(line)
    
    def on_progress(self, current: int, total: int, message: str):
        """Обработка обновления прогресса"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.progress_bar.setFormat(f"{percent}%")
        
        self.count_label.setText(f"{current} / {total}")
        self.status_label.setText(message)
        self.current_check_label.setText(message)
    
    def reset(self):
        """Сброс виджета"""
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0%")
        self.status_label.setText("Готов к сканированию")
        self.count_label.setText("0 / 0")
        self.current_check_label.setText("")
    
    def set_indeterminate(self, indeterminate: bool):
        """Установить бесконечный прогресс"""
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)


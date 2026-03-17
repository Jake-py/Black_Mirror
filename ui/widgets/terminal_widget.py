"""
Мини-терминал для Black Mirror UI.
Отображает выполнение команд в реальном времени.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                QTextEdit, QLabel, QPushButton)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime
import sys


class TerminalWidget(QWidget):
    """
    Мини-терминал для отображения логов и вывода команд.
    
    Особенности:
    - Автоматическая прокрутка
    - Цветовая подсветка по типам сообщений
    - Очистка по требованию
    """
    
    def __init__(self, parent=None, max_lines: int = 1000):
        super().__init__(parent)
        self.max_lines = max_lines
        self.lines = []
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Заголовок с кнопкой очистки
        header_layout = QHBoxLayout()
        
        title = QLabel("🖥️ Терминал")
        title.setObjectName("subtitle")
        
        clear_btn = QPushButton("Очистить")
        clear_btn.setFixedSize(80, 28)
        clear_btn.clicked.connect(self.clear)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Текстовое поле терминала
        self.terminal = QTextEdit()
        self.terminal.setObjectName("terminal")
        self.terminal.setReadOnly(True)
        self.terminal.setLineWrapMode(QTextEdit.NoWrap)
        
        layout.addWidget(self.terminal)
        
        # Подключаем сигналы для прокрутки
        self.terminal.textChanged.connect(self._auto_scroll)
    
    def _auto_scroll(self):
        """Автоматическая прокрутка к низу"""
        scrollbar = self.terminal.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def log(self, message: str, log_type: str = "info"):
        """
        Добавить сообщение в терминал.
        
        Args:
            message: Текст сообщения
            log_type: Тип сообщения (info, success, warning, error, command)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Цветовые коды для терминала
        colors = {
            "info": "#00ff00",      # Зеленый - обычные сообщения
            "success": "#00ff00",   # Зеленый - успех
            "warning": "#ffff00",   # Желтый - предупреждения
            "error": "#ff0000",     # Красный - ошибки
            "command": "#00ffff",   # Голубой - команды
            "result": "#ffffff",    # Белый - результаты
        }
        
        color = colors.get(log_type, "#00ff00")
        
        formatted = f"[{timestamp}] <span style='color:{color}'>{message}</span><br>"
        self.lines.append(formatted)
        
        # Ограничиваем количество строк
        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines:]
        
        # Обновляем терминал
        self.terminal.setHtml("".join(self.lines))
        self._auto_scroll()
    
    def info(self, message: str):
        """Информационное сообщение"""
        self.log(message, "info")
    
    def success(self, message: str):
        """Сообщение об успехе"""
        self.log(f"✓ {message}", "success")
    
    def warning(self, message: str):
        """Предупреждение"""
        self.log(f"⚠ {message}", "warning")
    
    def error(self, message: str):
        """Ошибка"""
        self.log(f"✗ {message}", "error")
    
    def command(self, cmd: str):
        """Вывод команды"""
        self.log(f"$ {cmd}", "command")
    
    def result(self, message: str):
        """Вывод результата"""
        self.log(f"  → {message}", "result")
    
    def section(self, title: str):
        """Заголовок секции"""
        self.log("─" * 40, "info")
        self.log(f"▶ {title}", "info")
        self.log("─" * 40, "info")
    
    def clear(self):
        """Очистить терминал"""
        self.lines = []
        self.terminal.clear()
    
    def get_html(self) -> str:
        """Получить содержимое в HTML"""
        return "".join(self.lines)
    
    def get_plain_text(self) -> str:
        """Получить содержимое как простой текст"""
        import re
        html = "".join(self.lines)
        # Удаляем HTML теги
        clean = re.sub(r'<[^>]+>', '', html)
        return clean


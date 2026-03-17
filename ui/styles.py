"""
Стили и темы для Black Mirror UI.
"""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication


class Colors:
    """Цветовая палитра Black Mirror"""
    
    # Основные цвета
    BG_DARK = "#0d0d0d"
    BG_CARD = "#1a1a1a"
    BG_HOVER = "#252525"
    BG_INPUT = "#2a2a2a"
    
    # Текст
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0a0"
    TEXT_MUTED = "#666666"
    
    # Статусы
    OK = "#4caf50"
    OK_LIGHT = "#81c784"
    WARN = "#ff9800"
    WARN_LIGHT = "#ffb74d"
    RISK = "#f44336"
    RISK_LIGHT = "#e57373"
    UNKNOWN = "#9e9e9e"
    
    # Акценты
    ACCENT = "#2196f3"
    ACCENT_HOVER = "#1976d2"
    BORDER = "#333333"


class BlackMirrorStyle:
    """
    Стили для Black Mirror приложения.
    Темная тема с акцентом на аналитичность.
    """
    
    @staticmethod
    def get_stylesheet() -> str:
        """Получить полную таблицу стилей"""
        return f"""
            /* Основные настройки приложения */
            QMainWindow, QWidget {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 14px;
            }}
            
            /* Кнопки */
            QPushButton {{
                background-color: {Colors.BG_CARD};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 10px 20px;
                min-width: 120px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
                border-color: {Colors.ACCENT};
            }}
            
            QPushButton:pressed {{
                background-color: {Colors.BG_INPUT};
            }}
            
            QPushButton:disabled {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_MUTED};
                border-color: {Colors.BORDER};
            }}
            
            /* Главная кнопка сканирования */
            QPushButton#scanButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: bold;
                min-width: 200px;
            }}
            
            QPushButton#scanButton:hover {{
                background-color: {Colors.ACCENT_HOVER};
            }}
            
            QPushButton#scanButton:disabled {{
                background-color: {Colors.TEXT_MUTED};
            }}
            
            /* Карточки */
            QFrame#card {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 16px;
            }}
            
            QFrame#card:hover {{
                border-color: {Colors.ACCENT};
            }}
            
            /* Прогресс бар */
            QProgressBar {{
                background-color: {Colors.BG_INPUT};
                border: none;
                border-radius: 4px;
                text-align: center;
                color: {Colors.TEXT_PRIMARY};
                height: 24px;
            }}
            
            QProgressBar::chunk {{
                background-color: {Colors.ACCENT};
                border-radius: 4px;
            }}
            
            /* Списки */
            QListWidget {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            
            QListWidget::item {{
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 4px;
            }}
            
            QListWidget::item:selected {{
                background-color: {Colors.ACCENT};
            }}
            
            /* Метки */
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
            }}
            
            QLabel#statusOK {{
                color: {Colors.OK};
                font-weight: bold;
            }}
            
            QLabel#statusWARN {{
                color: {Colors.WARN};
                font-weight: bold;
            }}
            
            QLabel#statusRISK {{
                color: {Colors.RISK};
                font-weight: bold;
            }}
            
            QLabel#statusUNKNOWN {{
                color: {Colors.UNKNOWN};
                font-weight: bold;
            }}
            
            /* Текстовые поля */
            QTextEdit, QPlainTextEdit {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 10px;
                color: {Colors.TEXT_PRIMARY};
            }}
            
            /* Терминал */
            QTextEdit#terminal {{
                background-color: #000000;
                color: #00ff00;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            
            /* Статусбар */
            QStatusBar {{
                background-color: {Colors.BG_CARD};
                color: {Colors.TEXT_SECONDARY};
                border-top: 1px solid {Colors.BORDER};
            }}
            
            /* Заголовки */
            QLabel#title {{
                font-size: 24px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
            }}
            
            QLabel#subtitle {{
                font-size: 14px;
                color: {Colors.TEXT_SECONDARY};
            }}
            
            /* Вкладки */
            QTabWidget::pane {{
                background-color: {Colors.BG_DARK};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            
            QTabBar::tab {{
                background-color: {Colors.BG_CARD};
                color: {Colors.TEXT_SECONDARY};
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border-bottom: 2px solid {Colors.ACCENT};
            }}
            
            /* Скроллбары */
            QScrollBar:vertical {{
                background-color: {Colors.BG_DARK};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {Colors.TEXT_MUTED};
                border-radius: 5px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {Colors.TEXT_SECONDARY};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            /* Разделители */
            QSplitter::handle {{
                background-color: {Colors.BORDER};
            }}
            
            /* Комбобоксы */
            QComboBox {{
                background-color: {Colors.BG_CARD};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 8px 12px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border: 2px solid {Colors.TEXT_SECONDARY};
                width: 8px;
                height: 8px;
                transform: rotate(45deg);
                margin-right: 8px;
            }}
        """
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Получить цвет по статусу"""
        colors = {
            "OK": Colors.OK,
            "WARN": Colors.WARN,
            "RISK": Colors.RISK,
            "UNKNOWN": Colors.UNKNOWN,
        }
        return colors.get(status, Colors.UNKNOWN)
    
    @staticmethod
    def get_status_icon(status: str) -> str:
        """Получить иконку по статусу"""
        icons = {
            "OK": "✓",
            "WARN": "⚠",
            "RISK": "✗",
            "UNKNOWN": "?",
        }
        return icons.get(status, "?")
    
    @staticmethod
    def get_status_qcolor(status: str) -> QColor:
        """Получить QColor по статусу"""
        return QColor(BlackMirrorStyle.get_status_color(status))
    
    @staticmethod
    def get_category_icon(category: str) -> str:
        """Получить иконку категории"""
        icons = {
            "kernel": "🧠",
            "protections": "🔐",
            "network": "🌐",
            "malware": "🦠",
            "filesystem": "📁",
        }
        return icons.get(category, "📊")


def apply_style(app: QApplication):
    """Применить стили к приложению"""
    app.setStyleSheet(BlackMirrorStyle.get_stylesheet())


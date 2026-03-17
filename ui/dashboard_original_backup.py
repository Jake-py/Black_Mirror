"""
Dashboard для Black Mirror UI.
Главная панель с общим статусом и управлением сканированием.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                QLabel, QPushButton, QFrame, QGridLayout)
from PySide6.QtCore import Qt, Signal
from core.models import ScanSession, CheckStatus
from ui.styles import BlackMirrorStyle, Colors
from ui.widgets.export_widget import ExportWidget


class StatusCard(QFrame):
    """Карточка статуса для dashboard"""
    
    def __init__(self, title: str, value: str, color: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.color = color
        self.icon_label = None
        self.value_label = None
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Colors.BG_CARD};
                border: 2px solid {self.color};
                border-radius: 12px;
                padding: 20px;
            }}
            QFrame#card:hover {{
                border-color: {self.color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Иконка/индикатор
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet(f"font-size: 32px; color: {self.color};")
        
        layout.addWidget(self.icon_label)
        
        # Значение
        self.value_label = QLabel(self.value)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {self.color};
            background-color: transparent;
            padding: 4px;
            border-radius: 4px;
        """)
        
        layout.addWidget(self.value_label)
        
        # Заголовок
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        
        layout.addWidget(title_label)
    
    def update_value(self, value: str):
        """Обновить значение"""
        if self.value_label:
            self.value_label.setText(value)


class DashboardWidget(QWidget):
    """
    Dashboard - главная панель Black Mirror.
    
    Компоненты:
    - Карточка общего статуса
    - Карточки по категориям
    - Кнопка запуска сканирования
    - Информация о системе
    """
    
    scan_requested = Signal()
    scan_completed = Signal(ScanSession)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = None
        self.overall_card = None
        self.ok_card = None
        self.warn_card = None
        self.risk_card = None
        self.unknown_card = None
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Заголовок
        title = QLabel("🛡️ Black Mirror")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        
        subtitle = QLabel("Анализ безопасности Kali Linux")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(subtitle)
        
        # Карточка общего статуса
        self.overall_card = StatusCard(
            "Общий статус", 
            "Готов", 
            Colors.ACCENT
        )
        self.overall_card.setMinimumHeight(150)
        
        layout.addWidget(self.overall_card)
        
        # Сетка счетчиков
        stats_layout = QGridLayout()
        stats_layout.setSpacing(16)
        
        # OK счетчик
        self.ok_card = StatusCard("✓ В норме", "0", Colors.OK)
        self.ok_card.setFixedSize(120, 100)
        stats_layout.addWidget(self.ok_card, 0, 0)
        
        # WARN счетчик
        self.warn_card = StatusCard("⚠ Предупреждения", "0", Colors.WARN)
        self.warn_card.setFixedSize(120, 100)
        stats_layout.addWidget(self.warn_card, 0, 1)
        
        # RISK счетчик
        self.risk_card = StatusCard("✗ Риски", "0", Colors.RISK)
        self.risk_card.setFixedSize(120, 100)
        stats_layout.addWidget(self.risk_card, 0, 2)
        
        # Unknown счетчик
        self.unknown_card = StatusCard("? Неизвестно", "0", Colors.UNKNOWN)
        self.unknown_card.setFixedSize(120, 100)
        stats_layout.addWidget(self.unknown_card, 0, 3)
        
        layout.addLayout(stats_layout)
        
        # Кнопка сканирования
        button_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("🚀 Запустить сканирование")
        self.scan_button.setObjectName("scanButton")
        self.scan_button.setMinimumHeight(50)
        self.scan_button.clicked.connect(self.scan_requested.emit)
        button_layout.addWidget(self.scan_button)
        
        self.export_widget = ExportWidget()
        self.export_widget.hide()
        button_layout.addWidget(self.export_widget)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Информация о системе
        self.system_info = QLabel("")
        self.system_info.setObjectName("subtitle")
        self.system_info.setAlignment(Qt.AlignCenter)
        self.system_info.setWordWrap(True)
        
        layout.addWidget(self.system_info)
        
        layout.addStretch()
    
    def update_session(self, session: ScanSession):
        """Обновить отображение после сканирования"""
        self.session = session
        counts = session.get_counts()
        
        # Обновляем счетчики
        self.ok_card.update_value(str(counts["ok"]))
        self.warn_card.update_value(str(counts["warn"]))
        self.risk_card.update_value(str(counts["risk"]))
        self.unknown_card.update_value(str(counts["unknown"]))
        
        # Обновляем общую карточку
        status = session.status
        if status == CheckStatus.OK:
            self.overall_card.update_value("Все в порядке")
            self.overall_card.color = Colors.OK
        elif status == CheckStatus.WARN:
            self.overall_card.update_value("Есть предупреждения")
            self.overall_card.color = Colors.WARN
        elif status == CheckStatus.RISK:
            self.overall_card.update_value("Обнаружены риски!")
            self.overall_card.color = Colors.RISK
        else:
            self.overall_card.update_value("Готов")
            self.overall_card.color = Colors.ACCENT
        
        # Обновляем стиль карточки
        self.overall_card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Colors.BG_CARD};
                border: 3px solid {self.overall_card.color};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        # Обновляем иконку
        icon = BlackMirrorStyle.get_status_icon(status.value)
        self.overall_card.icon_label.setText(icon)
    
    def set_scanning(self, scanning: bool):
        """Установить состояние сканирования"""
        if scanning:
            self.scan_button.setEnabled(False)
            self.scan_button.setText("⏳ Сканирование...")
            self.overall_card.update_value("Сканирование...")
            self.overall_card.color = Colors.ACCENT
        else:
            self.scan_button.setEnabled(True)
            self.scan_button.setText("🚀 Запустить сканирование")
    
    def set_system_info(self, info: str):
        """Установить информацию о системе"""
        self.system_info.setText(info)
    
    def reset(self):
        """Сброс к начальному состоянию"""
        self.session = None
        self.ok_card.update_value("0")
        self.warn_card.update_value("0")
        self.risk_card.update_value("0")
        self.unknown_card.update_value("0")
        self.overall_card.update_value("Готов")
        self.overall_card.color = Colors.ACCENT
        self.overall_card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Colors.BG_CARD};
                border: 2px solid {Colors.ACCENT};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        self.overall_card.icon_label.setText("🛡️")


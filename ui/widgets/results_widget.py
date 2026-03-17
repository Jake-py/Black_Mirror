"""
Виджет отображения результатов для Black Mirror UI.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                QListWidget, QListWidgetItem, QLabel,
                                QFrame, QPushButton, QScrollArea,
                                QApplication, QToolTip)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QClipboard
from core.models import CheckResult, CheckStatus
from ui.styles import BlackMirrorStyle, Colors


class ResultItemWidget(QWidget):
    """Виджет отдельного результата проверки"""
    
    clicked = Signal(CheckResult)
    fix_requested = Signal(str)   # fix_command
    copy_requested = Signal(str)  # текст для буфера
    
    def __init__(self, result: CheckResult, parent=None):
        super().__init__(parent)
        self.result = result
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Верхняя строка: статус и название
        header_layout = QHBoxLayout()
        
        # Статус (цветной кружок с иконкой)
        self.status_icon = QLabel(BlackMirrorStyle.get_status_icon(self.result.status.value))
        self.status_icon.setStyleSheet(f"""
            font-size: 20px;
            color: {BlackMirrorStyle.get_status_color(self.result.status.value)};
        """)
        
        # Название
        self.name_label = QLabel(self.result.name)
        self.name_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
        """)
        
        header_layout.addWidget(self.status_icon)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        
        # Кнопка Copy (всегда)
        copy_btn = QPushButton("⎘")
        copy_btn.setToolTip("Скопировать результат")
        copy_btn.setFixedSize(28, 28)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 14px;
            }}
            QPushButton:hover {{ border-color: {Colors.ACCENT}; color: {Colors.ACCENT}; }}
        """)
        copy_btn.clicked.connect(self._on_copy)
        header_layout.addWidget(copy_btn)
        
        # Кнопка Fix (только если есть fix_command)
        if getattr(self.result, 'is_fixable', False):
            fix_btn = QPushButton("⚡ Fix")
            fix_btn.setToolTip(f"Выполнить: {self.result.fix_command}")
            fix_btn.setFixedHeight(28)
            fix_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid {Colors.WARN};
                    border-radius: 4px;
                    color: {Colors.WARN};
                    font-size: 11px;
                    padding: 0 8px;
                }}
                QPushButton:hover {{ background: {Colors.WARN}; color: #000; }}
            """)
            fix_btn.clicked.connect(self._on_fix)
            header_layout.addWidget(fix_btn)
        
        # Тег категории
        category_icon = BlackMirrorStyle.get_category_icon(self.result.protection_type.value)
        category_label = QLabel(category_icon)
        category_label.setStyleSheet("color: #666666;")
        
        header_layout.addWidget(category_label)
        
        layout.addLayout(header_layout)
        
        # Описание
        self.desc_label = QLabel(self.result.description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        
        layout.addWidget(self.desc_label)
        
        # Рекомендация (если есть)
        if self.result.recommendation:
            rec_frame = QFrame()
            rec_layout = QVBoxLayout(rec_frame)
            rec_layout.setContentsMargins(8, 4, 8, 4)
            
            rec_label = QLabel(f"💡 {self.result.recommendation}")
            rec_label.setWordWrap(True)
            rec_label.setStyleSheet(f"""
                color: {Colors.ACCENT};
                font-size: 12px;
                font-style: italic;
            """)
            
            rec_layout.addWidget(rec_label)
            layout.addWidget(rec_frame)
        
        # Рамка вокруг элемента
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                margin: 4px;
            }}
            QWidget:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)
    
    def _on_fix(self):
        """Запрос на выполнение fix_command"""
        self.fix_requested.emit(self.result.fix_command)

    def _on_copy(self):
        """Копировать результат в буфер обмена"""
        text = (
            f"[{self.result.status.value}] {self.result.name}\n"
            f"{self.result.description}\n"
        )
        if self.result.recommendation:
            text += f"Рекомендация: {self.result.recommendation}\n"
        if self.result.fix_command:
            text += f"Fix: {self.result.fix_command}\n"
        if self.result.details:
            text += f"Детали: {self.result.details}\n"
        QApplication.clipboard().setText(text)
        self.copy_requested.emit(text)

    def mousePressEvent(self, event):
        """Обработка клика"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.result)
        super().mousePressEvent(event)


class ResultsWidget(QWidget):
    """
    Виджет отображения всех результатов сканирования.
    
    Особенности:
    - Группировка по категориям
    - Фильтрация по статусу
    - Клик для деталей
    """
    
    result_clicked = Signal(CheckResult)
    fix_requested = Signal(str)   # пробрасываем наверх в main_window
    copy_requested = Signal(str)  # для уведомления в терминале
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Заголовок с фильтрами
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 Результаты сканирования")
        title.setObjectName("subtitle")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Кнопки фильтров
        self.filter_all = QPushButton("Все")
        self.filter_all.setCheckable(True)
        self.filter_all.setChecked(True)
        self.filter_all.clicked.connect(lambda: self.apply_filter("all"))
        
        self.filter_ok = QPushButton("✓ OK")
        self.filter_ok.setCheckable(True)
        self.filter_ok.setStyleSheet(f"color: {Colors.OK};")
        self.filter_ok.clicked.connect(lambda: self.apply_filter("OK"))
        
        self.filter_warn = QPushButton("⚠ WARN")
        self.filter_warn.setCheckable(True)
        self.filter_warn.setStyleSheet(f"color: {Colors.WARN};")
        self.filter_warn.clicked.connect(lambda: self.apply_filter("WARN"))
        
        self.filter_risk = QPushButton("✗ RISK")
        self.filter_risk.setCheckable(True)
        self.filter_risk.setStyleSheet(f"color: {Colors.RISK};")
        self.filter_risk.clicked.connect(lambda: self.apply_filter("RISK"))
        
        header_layout.addWidget(self.filter_all)
        header_layout.addWidget(self.filter_ok)
        header_layout.addWidget(self.filter_warn)
        header_layout.addWidget(self.filter_risk)
        
        layout.addLayout(header_layout)
        
        # Список результатов
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.BG_DARK};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
            }}
            QListWidget::item {{
                background-color: transparent;
            }}
        """)
        
        layout.addWidget(self.list_widget)
        
        # Статистика
        self.stats_label = QLabel("")
        self.stats_label.setObjectName("subtitle")
        self.stats_label.setAlignment(Qt.AlignRight)
        
        layout.addWidget(self.stats_label)
    
    def add_result(self, result: CheckResult):
        """Добавить результат"""
        self.results.append(result)
        
    def add_results(self, results: list):
        """Добавить несколько результатов"""
        self.results.extend(results)
        
    def display_results(self):
        """Отобразить все результаты"""
        self.list_widget.clear()
        
        for result in self.results:
            item = QListWidgetItem(self.list_widget)
            
            widget = ResultItemWidget(result)
            widget.clicked.connect(self.result_clicked.emit)
            widget.fix_requested.connect(self.fix_requested.emit)
            widget.copy_requested.connect(self.copy_requested.emit)
            
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
        
        self.update_stats()
    
    def apply_filter(self, status: str):
        """Применить фильтр по статусу"""
        # Сбрасываем все кнопки
        self.filter_all.setChecked(False)
        self.filter_ok.setChecked(False)
        self.filter_warn.setChecked(False)
        self.filter_risk.setChecked(False)
        
        # Активируем нужную
        if status == "all":
            self.filter_all.setChecked(True)
        elif status == "OK":
            self.filter_ok.setChecked(True)
        elif status == "WARN":
            self.filter_warn.setChecked(True)
        elif status == "RISK":
            self.filter_risk.setChecked(True)
        
        # Фильтруем и отображаем
        self.list_widget.clear()
        
        for result in self.results:
            if status == "all" or result.status.value == status:
                item = QListWidgetItem(self.list_widget)
                widget = ResultItemWidget(result)
                widget.clicked.connect(self.result_clicked.emit)
                widget.fix_requested.connect(self.fix_requested.emit)
                widget.copy_requested.connect(self.copy_requested.emit)
                
                item.setSizeHint(widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)
        
        self.update_stats(status)
    
    def update_stats(self, filter_status: str = "all"):
        """Обновить статистику"""
        if filter_status == "all":
            total = len(self.results)
            ok = sum(1 for r in self.results if r.status == CheckStatus.OK)
            warn = sum(1 for r in self.results if r.status == CheckStatus.WARN)
            risk = sum(1 for r in self.results if r.status == CheckStatus.RISK)
            unknown = sum(1 for r in self.results if r.status == CheckStatus.UNKNOWN)
        else:
            total = sum(1 for r in self.results if r.status.value == filter_status)
            ok = warn = risk = unknown = 0
            if filter_status == "OK":
                ok = total
            elif filter_status == "WARN":
                warn = total
            elif filter_status == "RISK":
                risk = total
            elif filter_status == "UNKNOWN":
                unknown = total
        
        self.stats_label.setText(
            f"<span style='color: {Colors.OK}'>✓ {ok}</span> | "
            f"<span style='color: {Colors.WARN}'>⚠ {warn}</span> | "
            f"<span style='color: {Colors.RISK}'>✗ {risk}</span> | "
            f"Всего: {total}"
        )
    
    def clear(self):
        """Очистить результаты"""
        self.results = []
        self.list_widget.clear()
        self.update_stats()
    
    def get_results_by_status(self, status: CheckStatus) -> list:
        """Получить результаты по статусу"""
        return [r for r in self.results if r.status == status]
    
    def get_results_by_type(self, ptype) -> list:
        """Получить результаты по типу"""
        from core.models import ProtectionType
        return [r for r in self.results if r.protection_type == ptype]


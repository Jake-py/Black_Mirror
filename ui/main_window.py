"""
Главное окно приложения Black Mirror.
"""

import subprocess
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QMessageBox, QLabel, QPushButton, QFileDialog)
from PySide6.QtCore import Qt, Slot
from core.models import ScanSession, CheckResult, ProtectionType
from core.runner import ScanRunner
from ui.dashboard import DashboardWidget
from ui.widgets.progress_widget import ProgressWidget
from ui.widgets.terminal_widget import TerminalWidget
from ui.widgets.results_widget import ResultsWidget
from ui.widgets.export_widget import ExportWidget
from ui.styles import apply_style
from utils.system import get_os_info, get_hostname
from utils.export import Exporter


class MainWindow(QMainWindow):
    """
    Главное окно Black Mirror.
    
    Структура:
    - Левая панель: Dashboard + Терминал
    - Правая панель: Прогресс + Результаты + Экспорт
    """

    def __init__(self):
        super().__init__()
        self.runner = ScanRunner()
        self.current_session = None
        self.export_btn = None
        self.setup_ui()
        self.setup_connections()
        self.update_system_info()

    def setup_ui(self):
        self.setWindowTitle("Black Mirror - Анализ безопасности Kali Linux")
        self.setMinimumSize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        # Левая панель
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(16)
        self.dashboard = DashboardWidget()
        left_layout.addWidget(self.dashboard)
        self.terminal = TerminalWidget()
        left_layout.addWidget(self.terminal)
        splitter.addWidget(left_panel)

        # Правая панель
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(16)
        self.progress_widget = ProgressWidget()
        right_layout.addWidget(self.progress_widget)
        self.results_widget = ResultsWidget()
        right_layout.addWidget(self.results_widget)
        
        # Export footer
        export_layout = QHBoxLayout()
        export_label = QLabel("Экспорт:")
        export_layout.addWidget(export_label)
        self.export_btn = QPushButton("📤 Отчет")
        export_layout.addWidget(self.export_btn)
        export_layout.addStretch()
        right_layout.addLayout(export_layout)
        
        splitter.addWidget(right_panel)

        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)
        apply_style(self)

    def setup_connections(self):
        self.dashboard.scan_requested.connect(self.start_scan)
        self.results_widget.result_clicked.connect(self.show_result_details)
        self.results_widget.fix_requested.connect(self.execute_fix)
        self.results_widget.copy_requested.connect(self.on_copy_done)
        self.export_btn.clicked.connect(self.show_export_dialog)

    def update_system_info(self):
        os_info = get_os_info()
        hostname = get_hostname()
        info_text = (
            f"{os_info.get('name', 'Kali Linux')} | "
            f"Ядро: {os_info.get('kernel', 'Unknown')} | "
            f"Хост: {hostname}"
        )
        self.dashboard.set_system_info(info_text)
        self.terminal.log(f"Система: {info_text}", "info")

    def start_scan(self):
        self.terminal.clear()
        self.terminal.section("Начало сканирования")
        os_info = get_os_info()
        self.terminal.log(f"ОС: {os_info.get('name', 'Unknown')}", "info")
        self.terminal.log(f"Версия: {os_info.get('version', 'Unknown')}", "info")
        self.terminal.log(f"Ядро: {os_info.get('kernel', 'Unknown')}", "info")
        self.terminal.log("", "info")

        self.results_widget.clear()
        self.progress_widget.reset()
        self.dashboard.set_scanning(True)
        self.export_btn.setEnabled(False)

        self.runner.start_async(
            progress_receiver=self.on_progress,
            completed_receiver=self.on_scan_completed
        )

    @Slot(int, int, str)
    def on_progress(self, current: int, total: int, message: str):
        self.progress_widget.on_progress(current, total, message)
        if "→" not in message and "✓" not in message and "✗" not in message:
            self.terminal.log(message, "info")

    @Slot('PyQt_PyObject')
    def on_scan_completed(self, session: ScanSession):
        self.current_session = session
        self.dashboard.update_session(session)
        self.dashboard.set_scanning(False)
        self.export_btn.setEnabled(True)

        self.terminal.section("Сканирование завершено")
        self.terminal.log(f"Общий статус: {session.status.value}", "result")

        duration = session.duration
        if duration:
            self.terminal.log(f"Длительность: {duration:.2f} сек", "result")

        counts = session.get_counts()
        self.terminal.log(f"Проверок OK: {counts['ok']}", "success")
        if counts['warn'] > 0:
            self.terminal.log(f"Проверок WARN: {counts['warn']}", "warning")
        if counts['risk'] > 0:
            self.terminal.log(f"Проверок RISK: {counts['risk']}", "error")

        for result in session.results:
            self.results_widget.add_result(result)
        self.results_widget.display_results()

        if session.status.value == "OK":
            self.terminal.success("Сканирование завершено. Все проверки пройдены.")
        elif session.status.value == "WARN":
            self.terminal.warning("Сканирование завершено. Есть предупреждения.")
        else:
            self.terminal.error("Сканирование завершено. Обнаружены риски!")

    @Slot(CheckResult)
    def show_result_details(self, result: CheckResult):
        self.terminal.section(f"Детали: {result.name}")
        self.terminal.log(f"Статус: {result.status.value}", "info")
        self.terminal.log(f"Описание: {result.description}", "info")
        if result.recommendation:
            self.terminal.log(f"Рекомендация: {result.recommendation}", "warning")
        if hasattr(result, 'fix_command') and result.fix_command:
            self.terminal.log(f"Fix: {result.fix_command}", "command")
        if result.details:
            self.terminal.log(f"Детали: {result.details}", "result")

    @Slot(str)
    def execute_fix(self, fix_command: str):
        """
        Выполнить fix_command с подтверждением.
        Использует pkexec для GUI-запроса пароля, fallback на sudo.
        """
        if not fix_command:
            return

        confirm = QMessageBox(self)
        confirm.setWindowTitle("Подтверждение исправления")
        confirm.setText(f"Выполнить команду?\n\n{fix_command}")
        confirm.setInformativeText("Команда будет выполнена с правами root.")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setDefaultButton(QMessageBox.No)
        confirm.setIcon(QMessageBox.Warning)

        if confirm.exec() != QMessageBox.Yes:
            self.terminal.log("Исправление отменено.", "warning")
            return

        self.terminal.section("Выполнение исправления")
        self.terminal.command(fix_command)

        try:
            commands = [cmd.strip() for cmd in fix_command.split("&&")]
            all_ok = True

            for cmd in commands:
                self.terminal.log(f"→ {cmd}", "command")
                proc = subprocess.run(
                    ["pkexec"] + cmd.split(),
                    capture_output=True, text=True, timeout=30
                )
                if proc.returncode == 0:
                    self.terminal.success(f"OK: {cmd}")
                    if proc.stdout.strip():
                        self.terminal.log(proc.stdout.strip(), "result")
                else:
                    all_ok = False
                    self.terminal.error(f"Ошибка: {cmd}")
                    if proc.stderr.strip():
                        self.terminal.log(proc.stderr.strip(), "error")

            if all_ok:
                self.terminal.success("Все команды выполнены.")
            else:
                self.terminal.warning("Часть команд завершилась с ошибкой.")

        except subprocess.TimeoutExpired:
            self.terminal.error("Превышено время ожидания (30 сек).")
        except FileNotFoundError:
            self.terminal.warning("pkexec не найден, пробуем sudo...")
            self._execute_with_sudo(fix_command)
        except Exception as e:
            self.terminal.error(f"Ошибка: {e}")

    def _execute_with_sudo(self, fix_command: str):
        """Fallback через sudo"""
        try:
            for cmd in [c.strip() for c in fix_command.split("&&")]:
                proc = subprocess.run(
                    ["sudo"] + cmd.split(),
                    capture_output=True, text=True, timeout=30
                )
                if proc.returncode == 0:
                    self.terminal.success(f"OK: {cmd}")
                else:
                    self.terminal.error(f"Ошибка ({proc.returncode}): {proc.stderr.strip()}")
        except Exception as e:
            self.terminal.error(f"sudo ошибка: {e}")

    @Slot(str)
    def on_copy_done(self, _text: str):
        self.terminal.log("📋 Скопировано в буфер обмена.", "info")

    def show_export_dialog(self):
        """Показать диалог экспорта"""
        if not self.current_session:
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта. Запустите сканирование.")
            return
        
        path = QFileDialog.getSaveFileName(
            self, "Сохранить отчет", "black_mirror_report", 
            "All Formats (*.txt *.html *.pdf);;TXT (*.txt);;HTML (*.html);;PDF (*.pdf)"
        )[0]
        
        if path:
            fmt = path.split('.')[-1].lower() if '.' in path else 'txt'
            try:
                if fmt == "txt":
                    file_path = Exporter.export_txt(self.current_session, path)
                elif fmt == "html":
                    file_path = Exporter.export_html(self.current_session, path)
                elif fmt == "pdf":
                    file_path = Exporter.export_pdf(self.current_session, path)
                else:
                    file_path = Exporter.export_txt(self.current_session, path)
                
                self.terminal.log(f"📄 Отчет сохранен: {file_path}", "success")
                QMessageBox.information(self, "Успех", f"Отчет сохранен:\n{file_path}")
            except Exception as e:
                self.terminal.error(f"Ошибка экспорта: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта:\n{e}")

    def closeEvent(self, event):
        if hasattr(self.runner, 'stop'):
            self.runner.stop()
        event.accept()


"""
Оркестратор проверок для Black Mirror.
Запускает все проверки и собирает результаты.
"""

from core.models import CheckResult, CheckStatus, ScanSession
from core.checks.kernel import KernelChecker
from core.checks.protections import ProtectionsChecker
from core.checks.network import NetworkChecker
from core.checks.malware import MalwareChecker
from core.checks.filesystem import FilesystemChecker
from datetime import datetime
from typing import Callable, Optional, List
from PySide6.QtCore import QThread, Signal as pyqtSignal, QObject
import time



class ScanWorker(QThread):
    """Worker thread for scanning"""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)

    def __init__(self, runner):
        super().__init__()
        self.runner = runner
        self._stop_flag = False

    def run(self):
        """Override QThread run"""
        self.runner.emitter = self.progress
        self.runner._stop_flag = False
        session = self.runner.run_all_checks()
        self.finished.emit(session)

    def stop(self):
        self.runner._stop_flag = True


class ScanRunner:
    """
    Оркестратор проверок Black Mirror.
    
    Управляет запуском всех модулей проверок,
    собирает результаты и формирует сессию сканирования.
    """
    
    def __init__(self):
        """Инициализация runner"""
        self._stop_flag = False
        
        # Все модули проверок
        self.checkers = {
            "kernel": KernelChecker(),
            "protections": ProtectionsChecker(),
            "network": NetworkChecker(),
            "malware": MalwareChecker(),
            "filesystem": FilesystemChecker(),
        }
        
        # Порядок запуска и названия категорий
        self.scan_order = [
            ("protections", "🔐 Защиты системы"),
            ("kernel", "🧠 Ядро Linux"),
            ("network", "🌐 Сетевые настройки"),
            ("filesystem", "📁 Файловая система"),
            ("malware", "🦠 Malware/Heuristic"),
        ]
        self.worker = None
    
    def _update_progress_worker(self, current, total, message):
        """Emit progress from worker"""
        self.emitter.emit(current, total, message)
    
    def run_single_check(self, checker_name: str) -> List[CheckResult]:
        """Запуск одной категории проверок"""
        checker = self.checkers.get(checker_name)
        if checker:
            return checker.run_all_checks()
        return []
    
    def run_all_checks(self) -> ScanSession:
        """
        Запуск всех проверок.
        
        Returns:
            ScanSession с результатами всех проверок
        """
        session = ScanSession(start_time=datetime.now())
        total_checks = len(self.scan_order) * 10  # Approximate
        current_check = 0
        
        self._stop_flag = False
        
        for checker_name, category_name in self.scan_order:
            if self._stop_flag:
                break
            
            if hasattr(self, 'emitter') and self.emitter:
                self._update_progress_worker(current_check, total_checks, 
                                      f"Проверка: {category_name}")
            
            checker = self.checkers.get(checker_name)
            if checker:
                results = checker.run_all_checks()
                for result in results:
                    if self._stop_flag:
                        break
                    session.add_result(result)
                    current_check += 1
                    # Обновляем прогресс
                    if hasattr(self, 'emitter') and self.emitter:
                        self._update_progress_worker(current_check, total_checks, 
                                              f"{result.name}: {result.status.value}")
            time.sleep(0.01)  # Yield
        
        session.end_time = datetime.now()
        session._recalculate_status()
        
        if hasattr(self, 'emitter') and self.emitter:
            self._update_progress_worker(total_checks, total_checks, "Сканирование завершено")
        
        return session
    
    def start_async(self, progress_receiver, completed_receiver):
        """Start async scan with signal receivers"""
        self.worker = ScanWorker(self)
        self.emitter = self.worker.progress
        self.worker.progress.connect(progress_receiver)
        self.worker.finished.connect(completed_receiver)
        self.worker.finished.connect(self.worker.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()
    
    def stop(self):
        """Остановка проверок"""
        if self.worker:
            self.worker.stop()
        self._stop_flag = True
    
    def get_checker(self, name: str):
        """Получить конкретный checker"""
        return self.checkers.get(name)
    
    def get_all_results(self) -> List[CheckResult]:
        """Получить все результаты из всех checker'ов"""
        all_results = []
        for checker in self.checkers.values():
            if hasattr(checker, 'results'):
                all_results.extend(checker.results)
        return all_results
    
    def get_results_by_category(self, category: str) -> List[CheckResult]:
        """Получить результаты по категории"""
        checker = self.checkers.get(category)
        if checker and hasattr(checker, 'results'):
            return checker.results
        return []
    
    def get_summary(self) -> dict:
        """Получить сводку по всем checker'ам"""
        summary = {}
        for name in self.checkers.keys():
            results = self.get_results_by_category(name)
            ok = sum(1 for r in results if r.status == CheckStatus.OK)
            warn = sum(1 for r in results if r.status == CheckStatus.WARN)
            risk = sum(1 for r in results if r.status == CheckStatus.RISK)
            unknown = sum(1 for r in results if r.status == CheckStatus.UNKNOWN)
            
            summary[name] = {
                "total": len(results),
                "ok": ok,
                "warn": warn,
                "risk": risk,
                "unknown": unknown
            }
        
        return summary
    
    def get_checker(self, name: str):
        """Получить конкретный checker"""
        return self.checkers.get(name)
    
    def get_all_results(self) -> List[CheckResult]:
        """Получить все результаты из всех checker'ов"""
        all_results = []
        for checker in self.checkers.values():
            if hasattr(checker, 'results'):
                all_results.extend(checker.results)
        return all_results
    
    def get_results_by_category(self, category: str) -> List[CheckResult]:
        """Получить результаты по категории"""
        checker = self.checkers.get(category)
        if checker and hasattr(checker, 'results'):
            return checker.results
        return []
    
    def get_summary(self) -> dict:
        """Получить сводку по всем checker'ам"""
        summary = {}
        for name in self.checkers.keys():
            results = self.get_results_by_category(name)
            ok = sum(1 for r in results if r.status == CheckStatus.OK)
            warn = sum(1 for r in results if r.status == CheckStatus.WARN)
            risk = sum(1 for r in results if r.status == CheckStatus.RISK)
            unknown = sum(1 for r in results if r.status == CheckStatus.UNKNOWN)
            
            summary[name] = {
                "total": len(results),
                "ok": ok,
                "warn": warn,
                "risk": risk,
                "unknown": unknown
            }
        
        return summary


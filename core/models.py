"""
Модели данных для Black Mirror.
Каждая проверка возвращает структурированный результат.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


class CheckStatus(Enum):
    """Статус проверки"""
    OK = "OK"          # Все хорошо
    WARN = "WARN"      # Предупреждение
    RISK = "RISK"      # Риск/проблема
    UNKNOWN = "UNKNOWN"


class ProtectionType(Enum):
    """Тип защиты/проверки"""
    KERNEL = "kernel"
    PROTECTIONS = "protections"
    NETWORK = "network"
    MALWARE = "malware"
    FILESYSTEM = "filesystem"


@dataclass
class CheckResult:
    """
    Результат одной проверки
    
    Attributes:
        name: Имя проверки (отображаемое)
        status: Статус OK/WARN/RISK
        description: Что проверили
        recommendation: Рекомендация (если нужна)
        details: Детали (сырой вывод команд, etc)
        protection_type: Категория проверки
    """
    name: str
    status: CheckStatus
    description: str
    recommendation: str = ""
    details: str = ""
    protection_type: ProtectionType = ProtectionType.PROTECTIONS
    fix_command: str = ""  # Команда для автоматического исправления (если применимо)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "description": self.description,
            "recommendation": self.recommendation,
            "details": self.details,
            "type": self.protection_type.value,
            "fix_command": self.fix_command
        }
    
    @property
    def is_fixable(self) -> bool:
        """Можно ли исправить одной командой"""
        return bool(self.fix_command) and self.status in (CheckStatus.WARN, CheckStatus.RISK)


@dataclass
class ScanSession:
    """
    Сессия сканирования
    
    Attributes:
        start_time: Время начала
        end_time: Время окончания
        results: Список результатов
        status: Общий статус
    """
    start_time: datetime
    end_time: Optional[datetime] = None
    results: List[CheckResult] = None
    status: CheckStatus = CheckStatus.UNKNOWN
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
    
    @property
    def duration(self) -> Optional[float]:
        """Длительность сканирования в секундах"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def add_result(self, result: CheckResult):
        """Добавить результат"""
        self.results.append(result)
        self._recalculate_status()
    
    def _recalculate_status(self):
        """Пересчитать общий статус"""
        if not self.results:
            self.status = CheckStatus.UNKNOWN
            return
        
        # Приоритет: RISK > WARN > OK
        has_risk = any(r.status == CheckStatus.RISK for r in self.results)
        has_warn = any(r.status == CheckStatus.WARN for r in self.results)
        
        if has_risk:
            self.status = CheckStatus.RISK
        elif has_warn:
            self.status = CheckStatus.WARN
        else:
            self.status = CheckStatus.OK
    
    def get_by_type(self, ptype: ProtectionType) -> List[CheckResult]:
        """Получить результаты по типу"""
        return [r for r in self.results if r.protection_type == ptype]
    
    def get_counts(self) -> dict:
        """Подсчет результатов по статусам"""
        return {
            "total": len(self.results),
            "ok": sum(1 for r in self.results if r.status == CheckStatus.OK),
            "warn": sum(1 for r in self.results if r.status == CheckStatus.WARN),
            "risk": sum(1 for r in self.results if r.status == CheckStatus.RISK),
            "unknown": sum(1 for r in self.results if r.status == CheckStatus.UNKNOWN),
        }


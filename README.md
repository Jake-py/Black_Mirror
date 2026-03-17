# 🛡️ Black Mirror

> Анализ безопасности Kali Linux — одна кнопка, полная картина.

**Black Mirror** — GUI-инструмент для аудита безопасности Kali Linux. Запускает 50+ проверок ядра, сети, файловой системы и heuristic-анализа на malware. Показывает результаты визуально, объясняет что не так и умеет исправлять одной кнопкой.

![Black Mirror Screenshot](black-mirror.jpeg)

---

## Возможности

- **50 проверок** за ~10 секунд — ядро, сеть, файловая система, malware
- **Fix-кнопка** — безопасные исправления прямо из UI с подтверждением
- **Живой терминал** — видишь что происходит в реальном времени
- **Фильтрация** по статусу: OK / WARN / RISK
- **Copy** — любой результат в буфер одним кликом
- Без ложных срабатываний на легитимные security-инструменты (chkrootkit, rkhunter и др.)

## Статусы

| | Статус | Значение |
|---|---|---|
| ✓ | **OK** | Всё в порядке |
| ⚠ | **WARN** | Есть рекомендации |
| ✗ | **RISK** | Требует внимания |
| ? | **UNKNOWN** | Нужны права root |

---

## Установка

```bash
git clone https://github.com/redice/Black_Mirror.git
cd Black_Mirror

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

sudo venv/bin/python main.py
```

> Kali Linux 2024+ защищает системный Python — виртуальное окружение обязательно.

### Зависимости

```
PySide6 >= 6.5.0
psutil >= 5.9.0
Pillow >= 10.0.0
```

---

## Использование

1. Запустить с правами root
2. Нажать **"Запустить сканирование"**
3. Кликнуть на результат — увидеть детали в терминале
4. Нажать **⚡ Fix** на исправимых проблемах
5. Повторить сканирование для проверки

---

## Структура проекта

```
Black_Mirror/
├── main.py
├── core/
│   ├── models.py          # CheckResult, CheckStatus, ScanSession
│   ├── runner.py          # Оркестратор
│   └── checks/
│       ├── kernel.py
│       ├── protections.py
│       ├── network.py
│       ├── malware.py
│       └── filesystem.py
├── ui/
│   ├── main_window.py
│   ├── dashboard.py
│   ├── styles.py
│   └── widgets/
│       ├── progress_widget.py
│       ├── terminal_widget.py
│       └── results_widget.py
└── utils/
    ├── system.py
    ├── permissions.py
    └── parser.py
```

## Добавление проверок

```python
# core/checks/my_check.py
from core.models import CheckResult, CheckStatus, ProtectionType

class MyChecker:
    def check_something(self) -> CheckResult:
        return CheckResult(
            name="My Check",
            status=CheckStatus.OK,
            description="Всё хорошо",
            fix_command="",  # команда для ⚡ Fix (если применимо)
            protection_type=ProtectionType.SYSTEM
        )

    def run_all_checks(self) -> list:
        return [self.check_something()]
```

Зарегистрировать в `core/runner.py` — добавить в список checkers.

---

## Лицензия

MIT — см. [LICENSE](LICENSE)

---

<div align="center">

**BLACK MIRROR** — проект [TDS (Too Damn Smart)](https://github.com/redice)

Автор: **RED ICE** · Kali Linux · 2026

</div>

#!/usr/bin/env python3
"""
Black Mirror - Анализ безопасности Kali Linux

Одна кнопка → много проверок
Никаких команд → только результат
Никаких "RTFM" → визуальные статусы

Usage:
    sudo python3 main.py
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow


# Путь к иконке приложения
APP_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "icons", "app_icon.png")


def main():
    """Точка входа в приложение"""
    # Создаем приложение
    app = QApplication(sys.argv)
    
    # Настройки приложения
    app.setApplicationName("Black Mirror")
    app.setOrganizationName("Black Mirror Security")
    app.setApplicationVersion("1.0.0")
    
    # Устанавливаем иконку приложения
    if os.path.exists(APP_ICON_PATH):
        app_icon = QIcon(APP_ICON_PATH)
        app.setWindowIcon(app_icon)
    else:
        print(f"Предупреждение: Иконка не найдена по пути {APP_ICON_PATH}")
    
    # Создаем и показываем главное окно
    window = MainWindow()
    
    # Устанавливаем иконку для главного окна
    if os.path.exists(APP_ICON_PATH):
        window.setWindowIcon(QIcon(APP_ICON_PATH))
    
    window.show()
    
    # Запускаем цикл обработки событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


"""
Системные утилиты для Black Mirror.
Работа с процессами, памятью, информацией о системе.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List
import psutil


def get_kernel_version() -> str:
    """Получить версию ядра"""
    try:
        return os.uname().release
    except Exception:
        return "Unknown"


def is_root() -> bool:
    """Проверка на root"""
    return os.geteuid() == 0


def run_command(cmd: List[str], timeout: int = 10) -> Tuple[str, str, int]:
    """
    Безопасное выполнение команды
    
    Returns: (stdout, stderr, returncode)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", -1
    except Exception as e:
        return "", str(e), -1


def read_file_safe(path: str) -> str:
    """Безопасное чтение файла"""
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except Exception:
        return ""


def read_proc_file(path: str) -> str:
    """Чтение файла из /proc"""
    full_path = f"/proc/{path}"
    return read_file_safe(full_path)


def get_memory_info() -> dict:
    """Информация о памяти"""
    try:
        vm = psutil.virtual_memory()
        return {
            "total": vm.total,
            "available": vm.available,
            "percent": vm.percent,
            "used": vm.used
        }
    except Exception:
        return {}


def get_cpu_info() -> dict:
    """Информация о CPU"""
    try:
        cpu = psutil.cpu_freq()
        count = psutil.cpu_count(logical=True)
        return {
            "count": count,
            "frequency": cpu.current if cpu else 0,
            "model": read_file_safe("/proc/cpuinfo").split("\n")[4] if read_file_safe("/proc/cpuinfo") else "Unknown"
        }
    except Exception:
        return {}


def get_disk_info() -> dict:
    """Информация о дисках"""
    try:
        disk = psutil.disk_usage("/")
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    except Exception:
        return {}


def get_hostname() -> str:
    """Имя хоста"""
    return os.uname().nodename


def get_os_info() -> dict:
    """Общая информация об ОС"""
    try:
        with open("/etc/os-release", "r") as f:
            content = f.read()
            info = {}
            for line in content.split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    info[key] = value.strip('"')
            return {
                "name": info.get("PRETTY_NAME", "Unknown"),
                "version": info.get("VERSION", "Unknown"),
                "kernel": get_kernel_version()
            }
    except Exception:
        return {"name": "Unknown", "version": "Unknown", "kernel": "Unknown"}


def check_process_exists(name: str) -> bool:
    """Проверка существования процесса"""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == name:
                return True
        except Exception:
            pass
    return False


def get_running_services() -> List[str]:
    """Получить список запущенных сервисов (systemd)"""
    if not is_root():
        return []
    
    stdout, _, rc = run_command(["systemctl", "list-units", "--type=service", "--state=running", "--no-pager"])
    if rc != 0:
        return []
    
    services = []
    for line in stdout.split("\n"):
        if ".service" in line:
            name = line.split()[0] if line.split() else ""
            if name:
                services.append(name)
    return services


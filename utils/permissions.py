"""
Утилиты для проверки прав доступа в Kali Linux.
"""

import os
import stat
from typing import Tuple


def check_file_permissions(path: str) -> Tuple[bool, bool, bool]:
    """
    Проверка прав доступа к файлу
    
    Returns: (readable, writable, executable)
    """
    try:
        if not os.path.exists(path):
            return False, False, False
        
        mode = os.stat(path).st_mode
        
        readable = bool(mode & stat.S_IRUSR)
        writable = bool(mode & stat.S_IWUSR)
        executable = bool(mode & stat.S_IXUSR)
        
        return readable, writable, executable
    except Exception:
        return False, False, False


def is_world_writable(path: str) -> bool:
    """Проверка на world-writable"""
    try:
        if not os.path.exists(path):
            return False
        mode = os.stat(path).st_mode
        return bool(mode & stat.S_IWOTH)
    except Exception:
        return False


def is_suid_root(path: str) -> bool:
    """Проверка на SUID бит"""
    try:
        if not os.path.exists(path):
            return False
        mode = os.stat(path).st_mode
        return bool(mode & stat.S_ISUID) and os.stat(path).st_uid == 0
    except Exception:
        return False


def check_directory_writable(path: str) -> bool:
    """Проверка что директория writable"""
    try:
        return os.access(path, os.W_OK)
    except Exception:
        return False


def check_sudo_access() -> Tuple[bool, bool]:
    """
    Проверка sudo доступа
    
    Returns: (can_sudo, need_password)
    """
    # Проверяем, есть ли sudo
    try:
        # Пытаемся выполнить sudo -n (не спрашивать пароль)
        result = os.system("sudo -n true 2>/dev/null")
        if result == 0:
            return True, False
        
        # Проверяем, можем ли мы использовать sudo (спросит пароль)
        result = os.system("sudo true 2>/dev/null")
        if result == 0:
            return True, True
            
    except Exception:
        pass
    
    return False, False


def get_user_info() -> dict:
    """Информация о текущем пользователе"""
    return {
        "uid": os.getuid(),
        "euid": os.geteuid(),
        "gid": os.getgid(),
        "egid": os.getegid(),
        "username": os.getenv("USER", "Unknown"),
        "home": os.getenv("HOME", "/root"),
        "is_root": os.geteuid() == 0,
        "can_sudo": check_sudo_access()[0]
    }


def check_protected_paths() -> dict:
    """Проверка защищенных путей"""
    protected = [
        "/etc/shadow",
        "/etc/sudoers",
        "/etc/passwd",
        "/etc/gshadow",
        "/boot",
        "/root"
    ]
    
    results = {}
    for path in protected:
        exists = os.path.exists(path)
        can_read = os.access(path, os.R_OK) if exists else False
        can_write = os.access(path, os.W_OK) if exists else False
        
        results[path] = {
            "exists": exists,
            "readable": can_read,
            "writable": can_write,
            "protected": exists and not can_read
        }
    
    return results


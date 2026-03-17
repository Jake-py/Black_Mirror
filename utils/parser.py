"""
Парсинг выводов команд для Black Mirror.
"""

import re
from typing import List, Dict, Optional


def parse_sysctl_param(output: str, param: str) -> Optional[str]:
    """Парсинг параметра sysctl"""
    for line in output.split("\n"):
        if line.startswith(f"{param} ="):
            return line.split("=", 1)[1].strip()
    return None


def parse_cpuinfo() -> Dict:
    """Парсинг /proc/cpuinfo"""
    result = {}
    current = {}
    
    try:
        with open("/proc/cpuinfo", "r") as f:
            content = f.read()
        
        for line in content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                if key == "processor":
                    if current:
                        result[f"cpu_{current.get('processor', 'unknown')}"] = current
                    current = {"processor": value}
                else:
                    current[key] = value
        
        if current:
            result[f"cpu_{current.get('processor', 'unknown')}"] = current
    
    except Exception:
        pass
    
    return result


def parse_proc_mounts() -> List[Dict]:
    """Парсинг /proc/mounts"""
    mounts = []
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4:
                    mounts.append({
                        "device": parts[0],
                        "mount_point": parts[1],
                        "fs_type": parts[2],
                        "options": parts[3]
                    })
    except Exception:
        pass
    
    return mounts


def parse_proc_modules() -> List[str]:
    """Парсинг загруженных модулей ядра"""
    modules = []
    try:
        with open("/proc/modules", "r") as f:
            for line in f:
                parts = line.split()
                if parts:
                    modules.append(parts[0])
    except Exception:
        pass
    
    return modules


def parse_interfaces() -> Dict[str, Dict]:
    """Парсинг сетевых интерфейсов из /proc/net/dev"""
    interfaces = {}
    
    try:
        with open("/proc/net/dev", "r") as f:
            content = f.read()
        
        # Пропускаем первые две строки (заголовки)
        lines = content.strip().split("\n")[2:]
        
        for line in lines:
            if ":" in line:
                name, data = line.split(":", 1)
                name = name.strip()
                stats = data.strip().split()
                
                if len(stats) >= 16:
                    interfaces[name] = {
                        "rx_bytes": stats[0],
                        "rx_packets": stats[1],
                        "rx_errs": stats[2],
                        "tx_bytes": stats[8],
                        "tx_packets": stats[9],
                        "tx_errs": stats[10]
                    }
    
    except Exception:
        pass
    
    return interfaces


def parse_iptables_rules() -> List[Dict]:
    """Парсинг iptables правил"""
    rules = []
    
    stdout, _, rc = run_command_safe(["iptables", "-L", "-n", "-v"])
    if rc != 0:
        return rules
    
    for line in stdout.split("\n"):
        if "Chain" in line or "target" in line:
            continue
        if line.strip():
            rules.append({"raw": line.strip()})
    
    return rules


def run_command_safe(cmd: List[str]) -> tuple:
    """Безопасное выполнение команды"""
    import subprocess
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1


def parse_version_string(version_str: str) -> tuple:
    """Парсинг версии в tuple (major, minor, patch)"""
    try:
        parts = version_str.split(".")
        return tuple(int(p) for p in parts[:3])
    except:
        return (0, 0, 0)


def parse_cron_jobs() -> List[Dict]:
    """Парсинг cron заданий"""
    jobs = []
    
    # Системный crontab
    stdout, _, rc = run_command_safe(["cat", "/etc/crontab"])
    if rc == 0:
        for line in stdout.split("\n"):
            if line.strip() and not line.strip().startswith("#"):
                parts = line.split()
                if len(parts) >= 7:
                    jobs.append({
                        "source": "/etc/crontab",
                        "schedule": " ".join(parts[:5]),
                        "user": parts[5],
                        "command": " ".join(parts[6:])
                    })
    
    # Пользовательские кроны
    for user in ["/root", "/var/spool/cron"]:
        for path in ["/etc/cron.d"]:
            try:
                stdout, _, rc = run_command_safe(["ls", "-la", path])
                if rc == 0:
                    for line in stdout.split("\n"):
                        if ".cron" in line or "cron" in line:
                            jobs.append({"source": path, "raw": line})
            except:
                pass
    
    return jobs


def parse_systemd_services() -> List[Dict]:
    """Парсинг systemd сервисов"""
    services = []
    
    stdout, _, rc = run_command_safe([
        "systemctl", "list-units", 
        "--type=service", 
        "--all",
        "--no-pager",
        "--plain"
    ])
    
    if rc != 0:
        return services
    
    for line in stdout.split("\n"):
        if ".service" in line:
            parts = line.split()
            if len(parts) >= 4:
                services.append({
                    "name": parts[0],
                    "load": parts[1] if len(parts) > 1 else "",
                    "active": parts[2] if len(parts) > 2 else "",
                    "sub": parts[3] if len(parts) > 3 else "",
                    "description": " ".join(parts[4:]) if len(parts) > 4 else ""
                })
    
    return services


def parse_shadow_file() -> Dict:
    """Парсинг /etc/shadow для анализа паролей"""
    users = []
    
    try:
        with open("/etc/shadow", "r") as f:
            for line in f:
                if ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        users.append({
                            "user": parts[0],
                            "has_password": parts[1] not in ["", "*", "!"],
                            "locked": parts[1].startswith("!") or parts[1].startswith("*")
                        })
    except Exception:
        pass
    
    return {"users": users, "total": len(users)}


def parse_sudoers() -> List[str]:
    """Парсинг sudoers для анализа прав"""
    sudoers_entries = []
    
    files_to_check = [
        "/etc/sudoers",
        "/etc/sudoers.d/"
    ]
    
    for path in files_to_check:
        if path.endswith("/"):
            # Это директория
            stdout, _, rc = run_command_safe(["ls", "-la", path])
            if rc == 0:
                for line in stdout.split("\n"):
                    if not line.startswith("total") and not line.startswith("d"):
                        sudoers_entries.append(f"{path}: {line}")
        else:
            # Это файл
            stdout, _, rc = run_command_safe(["cat", path])
            if rc == 0:
                for line in stdout.split("\n"):
                    if not line.strip().startswith("#") and "ALL" in line.upper():
                        sudoers_entries.append(f"{path}: {line}")
    
    return sudoers_entries


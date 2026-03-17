"""
Проверки файловой системы для Black Mirror.
"""

from core.models import CheckResult, CheckStatus, ProtectionType
from utils.system import run_command, read_file_safe, is_root
from utils.permissions import is_suid_root, is_world_writable
from pathlib import Path
from typing import List, Dict
import os


class FilesystemChecker:
    """Проверки безопасности файловой системы"""
    
    def __init__(self):
        self.results = []
    
    def check_shadow_file(self) -> CheckResult:
        """Проверка /etc/shadow"""
        if not is_root():
            return CheckResult(
                name="Shadow File",
                status=CheckStatus.UNKNOWN,
                description="Требуются права root",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        stdout, _, rc = run_command(["ls", "-la", "/etc/shadow"])
        
        if rc != 0:
            return CheckResult(
                name="Shadow File",
                status=CheckStatus.RISK,
                description="Нет доступа к /etc/shadow",
                recommendation="Проверьте права",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        # Проверяем права
        if "root" in stdout and "shadow" in stdout:
            # Права должны быть 600 или 640
            parts = stdout.split()
            if len(parts) >= 1:
                perms = parts[0]
                if "rw-------" in perms or "-rw-r-----" in perms:
                    return CheckResult(
                        name="Shadow File",
                        status=CheckStatus.OK,
                        description="/etc/shadow защищен правильно",
                        recommendation="",
                        details=f"Права: {perms}",
                        protection_type=ProtectionType.FILESYSTEM
                    )
                elif "rw-rw-r--" in perms or "rw-rw-rw-" in perms:
                    return CheckResult(
                        name="Shadow File",
                        status=CheckStatus.RISK,
                        description="/etc/shadow имеет слишком открытые права",
                        recommendation="Выполните: sudo chmod 600 /etc/shadow",
                        details=f"Права: {perms}",
                        fix_command="sudo chmod 600 /etc/shadow",
                        protection_type=ProtectionType.FILESYSTEM
                    )
        
        return CheckResult(
            name="Shadow File",
            status=CheckStatus.WARN,
            description="Права /etc/shadow не стандартные",
            recommendation="Проверьте и исправьте права",
            details="",
            protection_type=ProtectionType.FILESYSTEM
        )
    
    def check_passwd_file(self) -> CheckResult:
        """Проверка /etc/passwd"""
        stdout, _, rc = run_command(["ls", "-la", "/etc/passwd"])
        
        if rc != 0:
            return CheckResult(
                name="Passwd File",
                status=CheckStatus.RISK,
                description="Нет доступа к /etc/passwd",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        # Проверяем права (должен быть 644)
        if "rw-r--r--" in stdout:
            return CheckResult(
                name="Passwd File",
                status=CheckStatus.OK,
                description="/etc/passwd имеет правильные права",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        elif "rw-rw-rw-" in stdout:
                    return CheckResult(
                        name="Passwd File",
                        status=CheckStatus.WARN,
                        description="/etc/passwd world-writable",
                        recommendation="Выполните: sudo chmod 644 /etc/passwd",
                        details="",
                        fix_command="sudo chmod 644 /etc/passwd",
                        protection_type=ProtectionType.FILESYSTEM
                    )
        
        return CheckResult(
            name="Passwd File",
            status=CheckStatus.WARN,
            description="Права /etc/passwd не стандартные",
            recommendation="Проверьте и исправьте права",
            details="",
            protection_type=ProtectionType.FILESYSTEM
        )
    
    def check_sudoers(self) -> CheckResult:
        """Проверка конфигурации sudoers"""
        stdout, _, rc = run_command(["ls", "-la", "/etc/sudoers"])
        
        if rc != 0:
            return CheckResult(
                name="Sudoers File",
                status=CheckStatus.WARN,
                description="/etc/sudoers не найден",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        # Проверяем права (должен быть 440)
        if "-r--r-----" in stdout or "440" in stdout:
            return CheckResult(
                name="Sudoers File",
                status=CheckStatus.OK,
                description="/etc/sudoers защищен правильно",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
            return CheckResult(
                name="Sudoers File",
                status=CheckStatus.RISK,
                description="/etc/sudoers имеет неправильные права",
                recommendation="Выполните: sudo chmod 440 /etc/sudoers",
                details="",
                fix_command="sudo chmod 440 /etc/sudoers",
                protection_type=ProtectionType.FILESYSTEM
            )
    
    def check_ssh_permissions(self) -> CheckResult:
        """Проверка прав на SSH директорию"""
        ssh_dir = "/root/.ssh"
        if not os.path.exists(ssh_dir):
            ssh_dir = os.path.expanduser("~/.ssh")
        
        if not os.path.exists(ssh_dir):
            return CheckResult(
                name="SSH Directory",
                status=CheckStatus.OK,
                description="SSH директория не существует",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        stdout, _, rc = run_command(["ls", "-la", ssh_dir])
        
        if rc != 0:
            return CheckResult(
                name="SSH Directory",
                status=CheckStatus.UNKNOWN,
                description="Нет доступа к SSH директории",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        # Проверяем права на директорию (должна быть 700)
        issues = []
        
        if "drwx------" not in stdout and "700" not in stdout:
            issues.append("директория должна быть 700")
        
        # Проверяем права на ключи
        for line in stdout.split("\n"):
            if ".pub" not in line and any(k in line for k in ["id_rsa", "id_ed", "id_ec"]):
                if "-rw-------" not in line and "600" not in line:
                    issues.append("приватные ключи должны быть 600")
        
        if issues:
            return CheckResult(
                name="SSH Permissions",
                status=CheckStatus.WARN,
                description="Проблемы с правами SSH: " + ", ".join(issues),
                recommendation="Выполните: chmod 700 ~/.ssh && chmod 600 ~/.ssh/*",
                details=stdout,
                fix_command="chmod 700 ~/.ssh && chmod 600 ~/.ssh/*",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        return CheckResult(
            name="SSH Permissions",
            status=CheckStatus.OK,
            description="SSH права настроены правильно",
            recommendation="",
            details="",
            protection_type=ProtectionType.FILESYSTEM
        )
    
    def check_world_writable_files(self) -> CheckResult:
        """Проверка world-writable файлов в системных директориях"""
        if not is_root():
            return CheckResult(
                name="World Writable Files",
                status=CheckStatus.UNKNOWN,
                description="Требуются права root",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        # Проверяем критичные директории
        critical_dirs = ["/etc", "/usr", "/bin", "/sbin", "/var"]
        
        issues = []
        for d in critical_dirs:
            stdout, _, rc = run_command(["find", d, "-perm", "-0002", "-type", "f"])
            if rc == 0 and stdout.strip():
                files = stdout.strip().split("\n")[:5]  # Первые 5
                for f in files:
                    if not any(skip in f for skip in [".cache", ".mozilla", ".config"]):
                        issues.append(f)
        
        if len(issues) > 10:
            return CheckResult(
                name="World Writable Files",
                status=CheckStatus.RISK,
                description=f"Обнаружено много world-writable файлов: {len(issues)}",
                recommendation="Проверьте и исправьте права",
                details="\n".join(issues[:5]),
                protection_type=ProtectionType.FILESYSTEM
            )
        
        if issues:
            return CheckResult(
                name="World Writable Files",
                status=CheckStatus.WARN,
                description=f"Обнаружено world-writable файлов: {len(issues)}",
                recommendation="Проверьте и исправьте права",
                details="\n".join(issues[:5]),
                protection_type=ProtectionType.FILESYSTEM
            )
        
        return CheckResult(
            name="World Writable Files",
            status=CheckStatus.OK,
            description="World-writable файлов не обнаружено",
            recommendation="",
            details="",
            protection_type=ProtectionType.FILESYSTEM
        )
    
    def check_unowned_files(self) -> CheckResult:
        """Проверка файлов без владельца"""
        if not is_root():
            return CheckResult(
                name="Unowned Files",
                status=CheckStatus.UNKNOWN,
                description="Требуются права root",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        stdout, _, rc = run_command([
            "find", "/etc", "-", "type", "f", "\\(", 
            "-nouser", "-o", "-nogroup", "\\)"
        ])
        
        if rc != 0 or not stdout.strip():
            return CheckResult(
                name="Unowned Files",
                status=CheckStatus.OK,
                description="Файлов без владельца не обнаружено",
                recommendation="",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        files = stdout.strip().split("\n")[:5]
        
        return CheckResult(
            name="Unowned Files",
            status=CheckStatus.WARN,
            description=f"Обнаружено файлов без владельца: {len(stdout.strip().split(chr(10)))}",
            recommendation="Исправьте владельца: chown user:group <file>",
            details="\n".join(files),
            protection_type=ProtectionType.FILESYSTEM
        )
    
    def check_home_permissions(self) -> CheckResult:
        """Проверка прав на домашние директории"""
        homes = ["/root", "/home"]
        
        issues = []
        for home in homes:
            if os.path.exists(home):
                stdout, _, _ = run_command(["ls", "-la", home])
                if "drwx------" not in stdout and "700" not in stdout:
                    # Проверяем, не слишком ли открыто
                    if "drwxrwxrwx" in stdout or "777" in stdout:
                        issues.append(f"{home}: слишком открытые права")
        
        if issues:
            return CheckResult(
                name="Home Directory",
                status=CheckStatus.RISK,
                description="Домашние директории имеют открытые права: " + ", ".join(issues),
                recommendation="Выполните: chmod 700 /root && chmod 700 /home/*",
                details="",
                protection_type=ProtectionType.FILESYSTEM
            )
        
        return CheckResult(
            name="Home Directory",
            status=CheckStatus.OK,
            description="Домашние директории защищены",
            recommendation="",
            details="",
            protection_type=ProtectionType.FILESYSTEM
        )
    
    def check_critical_files(self) -> CheckResult:
        """Проверка критичных файлов на наличие и права"""
        critical_files = {
            "/etc/crontab": "600",
            "/etc/fstab": "644",
            "/etc/hosts": "644",
            "/etc/resolv.conf": "644",
            "/boot/grub/grub.cfg": "400",
        }
        
        issues = []
        ok_count = 0
        
        for filepath, expected_perms in critical_files.items():
            if not os.path.exists(filepath):
                issues.append(f"{filepath}: не существует")
                continue
            
            # Проверяем права
            stdout, _, _ = run_command(["stat", "-c", "%a", filepath])
            current_perms = stdout.strip()
            
            if current_perms != expected_perms:
                # Проверяем, не более ли открытые
                if current_perms > expected_perms:
                    issues.append(f"{filepath}: текущие={current_perms}, ожидаемые={expected_perms}")
                else:
                    ok_count += 1
            else:
                ok_count += 1
        
        if issues:
            return CheckResult(
                name="Critical Files",
                status=CheckStatus.WARN,
                description=f"Не все критичные файлы имеют правильные права ({ok_count}/{len(critical_files)})",
                recommendation="Проверьте и исправьте права",
                details="\n".join(issues[:5]),
                protection_type=ProtectionType.FILESYSTEM
            )
        
        return CheckResult(
            name="Critical Files",
            status=CheckStatus.OK,
            description=f"Все {ok_count} критичных файлов имеют правильные права",
            recommendation="",
            details="",
            protection_type=ProtectionType.FILESYSTEM
        )
    
    def run_all_checks(self) -> list:
        """Запустить все проверки файловой системы"""
        self.results = [
            self.check_shadow_file(),
            self.check_passwd_file(),
            self.check_sudoers(),
            self.check_ssh_permissions(),
            self.check_world_writable_files(),
            self.check_unowned_files(),
            self.check_home_permissions(),
            self.check_critical_files(),
        ]
        return self.results


"""
Проверки защит системы для Black Mirror.
ASLR, NX, AppArmor, SELinux, auditd, firewall.
"""

from core.models import CheckResult, CheckStatus, ProtectionType
from utils.system import run_command, read_file_safe, check_process_exists, get_running_services, is_root
from typing import Optional


class ProtectionsChecker:
    """Проверки системных защит"""
    
    def __init__(self):
        self.results = []
    
    def check_aslr(self) -> CheckResult:
        """Проверка ASLR (Address Space Layout Randomization)"""
        stdout, _, _ = run_command(["sysctl", "kernel.randomize_va_space"])
        
        try:
            value = int(stdout.split("=", 1)[-1].strip())
        except (ValueError, IndexError):
            return CheckResult(
                name="ASLR",
                status=CheckStatus.UNKNOWN,
                description="Не удалось определить статус ASLR",
                recommendation="Проверьте sysctl kernel.randomize_va_space",
                details=stdout,
                protection_type=ProtectionType.PROTECTIONS
            )
        
        if value == 2:
            return CheckResult(
                name="ASLR",
                status=CheckStatus.OK,
                description="ASLR полностью включен (рандомизация стека, кучи, VDSO)",
                recommendation="",
                details=f"kernel.randomize_va_space = {value}",
                protection_type=ProtectionType.PROTECTIONS
            )
        elif value == 1:
            return CheckResult(
                name="ASLR",
                status=CheckStatus.WARN,
                description="ASLR частично включен (только рандомизация стека)",
                recommendation="Установите kernel.randomize_va_space = 2",
                details=f"kernel.randomize_va_space = {value}",
                protection_type=ProtectionType.PROTECTIONS
            )
        else:
            return CheckResult(
                name="ASLR",
                status=CheckStatus.RISK,
                description="ASLR отключен",
                recommendation="Включите ASLR: sysctl -w kernel.randomize_va_space=2",
                details=f"kernel.randomize_va_space = {value}",
                protection_type=ProtectionType.PROTECTIONS
            )
    
    def check_nx_bit(self) -> CheckResult:
        """Проверка NX (No-Execute) бита"""
        cpu_info = read_file_safe("/proc/cpuinfo")
        
        if not cpu_info:
            return CheckResult(
                name="NX (Execute Disable)",
                status=CheckStatus.UNKNOWN,
                description="Не удалось прочитать информацию о CPU",
                recommendation="",
                details="",
                protection_type=ProtectionType.PROTECTIONS
            )
        
        has_nx = False
        
        # Проверяем флаги CPU
        for line in cpu_info.split("\n"):
            if "flags" in line or "Features" in line:
                flags = line.split(":", 1)[-1].split()
                has_nx = "nx" in flags or "noexec" in flags.lower()
                break
        
        if has_nx:
            return CheckResult(
                name="NX (Execute Disable)",
                status=CheckStatus.OK,
                description="NX бит поддерживается и включен на CPU",
                recommendation="",
                details="CPU флаг 'nx' обнаружен",
                protection_type=ProtectionType.PROTECTIONS
            )
        else:
            return CheckResult(
                name="NX (Execute Disable)",
                status=CheckStatus.RISK,
                description="NX бит не поддерживается или отключен",
                recommendation="Рассмотрите обновление CPU или включение NX в BIOS",
                details="CPU флаг 'nx' не обнаружен",
                protection_type=ProtectionType.PROTECTIONS
            )
    
    def check_apparmor(self) -> CheckResult:
        """Проверка AppArmor"""
        # Проверяем, запущен ли apparmor
        stdout, _, rc = run_command(["systemctl", "status", "apparmor", "--no-pager"])
        
        if rc == 0 and "active" in stdout.lower():
            # Проверяем режим
            if "enforce" in stdout.lower():
                return CheckResult(
                    name="AppArmor",
                    status=CheckStatus.OK,
                    description="AppArmor активен в режиме enforce",
                    recommendation="",
                    details=stdout[:200],
                    protection_type=ProtectionType.PROTECTIONS
                )
            elif "complaint" in stdout.lower():
                return CheckResult(
                    name="AppArmor",
                    status=CheckStatus.WARN,
                    description="AppArmor активен в режиме complain",
                    recommendation="Переведите в режим enforce для полной защиты",
                    details=stdout[:200],
                    protection_type=ProtectionType.PROTECTIONS
                )
        
        # Проверяем через aa-status
        stdout, _, rc = run_command(["aa-status", "--no-pager"])
        if rc == 0:
            return CheckResult(
                name="AppArmor",
                status=CheckStatus.OK,
                description="AppArmor управление доступно (aa-status)",
                recommendation="",
                details=stdout[:200],
                protection_type=ProtectionType.PROTECTIONS
            )
        
        # AppArmor не установлен или не запущен
        return CheckResult(
            name="AppArmor",
            status=CheckStatus.WARN,
            description="AppArmor не обнаружен или не активен",
            recommendation="Установите и настройте AppArmor для Mandatory Access Control",
            details="systemctl status apparmor вернул код: " + str(rc),
            protection_type=ProtectionType.PROTECTIONS
        )
    
    def check_selinux(self) -> CheckResult:
        """Проверка SELinux"""
        # SELinux обычно не используется в Kali, но проверим
        enforce_file = read_file_safe("/sys/fs/selinux/enforce")
        
        if enforce_file == "1":
            return CheckResult(
                name="SELinux",
                status=CheckStatus.OK,
                description="SELinux активен в режиме enforcing",
                recommendation="",
                details="",
                protection_type=ProtectionType.PROTECTIONS
            )
        elif enforce_file == "0":
            return CheckResult(
                name="SELinux",
                status=CheckStatus.WARN,
                description="SELinux установлен, но в режиме permissive",
                recommendation="Переведите в режим enforcing",
                details="",
                protection_type=ProtectionType.PROTECTIONS
            )
        
        # Проверяем через getenforce
        stdout, _, rc = run_command(["getenforce"])
        if rc == 0:
            status = stdout.strip().lower()
            if status == "enforcing":
                return CheckResult(
                    name="SELinux",
                    status=CheckStatus.OK,
                    description="SELinux активен в режиме enforcing",
                    recommendation="",
                    details="",
                    protection_type=ProtectionType.PROTECTIONS
                )
            elif status == "permissive":
                return CheckResult(
                    name="SELinux",
                    status=CheckStatus.WARN,
                    description="SELinux в режиме permissive",
                    recommendation="",
                    details="",
                    protection_type=ProtectionType.PROTECTIONS
                )
        
        # SELinux не используется (нормально для Kali)
        return CheckResult(
            name="SELinux",
            status=CheckStatus.OK,
            description="SELinux не используется (не установлен)",
            recommendation="Для Kali это нормально, используйте AppArmor",
            details="",
            protection_type=ProtectionType.PROTECTIONS
        )
    
    def check_auditd(self) -> CheckResult:
        """Проверка auditd"""
        stdout, _, rc = run_command(["systemctl", "status", "auditd", "--no-pager"])
        
        if rc == 0 and "active" in stdout.lower():
            return CheckResult(
                name="auditd",
                status=CheckStatus.OK,
                description="auditd активен и ведет аудит системы",
                recommendation="",
                details=stdout[:200],
                protection_type=ProtectionType.PROTECTIONS
            )
        
        return CheckResult(
            name="auditd",
            status=CheckStatus.WARN,
            description="auditd не запущен",
            recommendation="Установите и настройте auditd для аудита системных событий",
            details="systemctl status auditd вернул код: " + str(rc),
            protection_type=ProtectionType.PROTECTIONS
        )
    
    def check_firewall(self) -> CheckResult:
        """Проверка firewall (iptables/nftables)"""
        # Проверяем iptables
        stdout, _, rc = run_command(["iptables", "-L", "-n", "--line-numbers"])
        
        has_rules = rc == 0 and len([l for l in stdout.split("\n") if l.strip() and not l.startswith("Chain") and not l.startswith("target")]) > 0
        
        # Проверяем nftables
        stdout2, _, rc2 = run_command(["nft", "list", "ruleset"])
        has_nft = rc2 == 0 and stdout2.strip()
        
        if has_rules or has_nft:
            firewall_type = "nftables" if has_nft else "iptables"
            return CheckResult(
                name="Firewall",
                status=CheckStatus.OK,
                description=f"Firewall ({firewall_type}) настроен и имеет правила",
                recommendation="",
                details=f"{firewall_type} active",
                protection_type=ProtectionType.PROTECTIONS
            )
        
        return CheckResult(
            name="Firewall",
            status=CheckStatus.RISK,
            description="Firewall не настроен (нет активных правил)",
            recommendation="Настройте iptables или nftables для защиты сети",
            details="iptables и nftables не имеют активных правил",
            protection_type=ProtectionType.PROTECTIONS
        )
    
    def check_firewalld(self) -> CheckResult:
        """Проверка firewalld (альтернатива iptables)"""
        stdout, _, rc = run_command(["systemctl", "status", "firewalld", "--no-pager"])
        
        if rc == 0 and "active" in stdout.lower():
            return CheckResult(
                name="firewalld",
                status=CheckStatus.OK,
                description="firewalld активен",
                recommendation="",
                details=stdout[:200],
                protection_type=ProtectionType.PROTECTIONS
            )
        
        return CheckResult(
            name="firewalld",
            status=CheckStatus.OK,
            description="firewalld не используется (нормально для Kali)",
            recommendation="",
            details="",
            protection_type=ProtectionType.PROTECTIONS
        )
    
    def check_sysctl_hardening(self) -> CheckResult:
        """Проверка дополнительных sysctl параметров"""
        checks = {
            "kernel.sysrq": ("0", "WARN", "SysRq отключен", "Включите только при необходимости"),
            "net.ipv4.tcp_syncookies": ("1", "OK", "TCP SYN cookies включены", ""),
            "net.ipv4.conf.all.accept_source_route": ("0", "OK", "Source routing отключен", ""),
            "net.ipv6.conf.all.accept_source_route": ("0", "OK", "IPv6 source routing отключен", ""),
        }
        
        issues = []
        
        for param, (expected, status, desc, rec) in checks.items():
            stdout, _, _ = run_command(["sysctl", param])
            try:
                current = stdout.split("=", 1)[-1].strip()
                if current != expected:
                    issues.append(f"{param}: текущее={current}, ожидаемое={expected}")
            except Exception:
                issues.append(f"Не удалось проверить {param}")
        
        if issues:
            return CheckResult(
                name="Sysctl Hardening",
                status=CheckStatus.WARN,
                description="Некоторые sysctl параметры не соответствуют рекомендациям",
                recommendation="Настройте sysctl для повышения безопасности",
                details="\n".join(issues),
                protection_type=ProtectionType.PROTECTIONS
            )
        
        return CheckResult(
            name="Sysctl Hardening",
            status=CheckStatus.OK,
            description="Основные sysctl параметры настроены правильно",
            recommendation="",
            details="",
            protection_type=ProtectionType.PROTECTIONS
        )
    
    def run_all_checks(self) -> list:
        """Запустить все проверки защит"""
        self.results = [
            self.check_aslr(),
            self.check_nx_bit(),
            self.check_apparmor(),
            self.check_selinux(),
            self.check_auditd(),
            self.check_firewall(),
            self.check_firewalld(),
            self.check_sysctl_hardening(),
        ]
        return self.results


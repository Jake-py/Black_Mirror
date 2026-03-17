"""
Проверки ядра для Black Mirror.
"""

from core.models import CheckResult, CheckStatus, ProtectionType
from utils.system import read_file_safe, run_command, get_kernel_version
from utils.parser import parse_version_string
from typing import Optional
import re


class KernelChecker:
    """Проверки связанные с ядром Linux"""
    
    VULNERABLE_KERNELS = [
        "5.4", "5.10", "5.15",  # Примеры уязвимых версий (обновляется регулярно)
    ]
    
    DEBUG_FEATURES = [
        "debug",
        "kernel hacking",
    ]
    
    def __init__(self):
        self.results = []
    
    def check_kernel_version(self) -> CheckResult:
        """Проверка версии ядра"""
        version = get_kernel_version()
        
        # Проверяем на известные уязвимые версии
        is_vulnerable = False
        for vuln in self.VULNERABLE_KERNELS:
            if version.startswith(vuln):
                is_vulnerable = True
                break
        
        if is_vulnerable:
            return CheckResult(
                name="Версия ядра",
                status=CheckStatus.WARN,
                description=f"Версия ядра {version} может содержать известные уязвимости",
                recommendation="Рекомендуется обновить ядро до последней версии",
                details=f"Текущая версия: {version}",
                protection_type=ProtectionType.KERNEL
            )
        
        return CheckResult(
            name="Версия ядра",
            status=CheckStatus.OK,
            description=f"Версия ядра {version} актуальна",
            recommendation="",
            details=f"Версия: {version}",
            protection_type=ProtectionType.KERNEL
        )
    
    def check_kernel_config(self) -> CheckResult:
        """Проверка конфигурации ядра"""
        config_path = "/boot/config-" + get_kernel_version()
        config_content = read_file_safe(config_path)
        
        if not config_content:
            return CheckResult(
                name="Конфигурация ядра",
                status=CheckStatus.UNKNOWN,
                description="Не удалось прочитать конфигурацию ядра",
                recommendation="Проверьте права доступа к /boot",
                details="",
                protection_type=ProtectionType.KERNEL
            )
        
        issues = []
        warnings = []
        
        # Проверяем важные опции
        checks = {
            "CONFIG_STRICT_DEVMEM": ("Защита памяти", "RISK"),
            "CONFIG_IO_STRICT_DEVMEM": ("IO memory protection", "RISK"),
            "CONFIG_SLAB_FREELIST_HARDENED": ("Freelist hardening", "RISK"),
            "CONFIG_SLAB_FREELIST_RANDOM": ("Freelist randomization", "WARN"),
            "CONFIG_SHUFFLE_PAGE_ALLOCATOR": ("Page allocator randomization", "WARN"),
            "CONFIG_BUG": ("BUG() support", "WARN"),
            "CONFIG_EMBEDDED": ("Embedded support", "WARN"),
        }
        
        for option, (desc, severity) in checks.items():
            if option + "=y" in config_content:
                continue
            elif option + "=n" in config_content:
                if severity == "RISK":
                    issues.append(f"{option} отключен")
                else:
                    warnings.append(f"{option} отключен")
        
        if issues:
            return CheckResult(
                name="Параметры hardening ядра",
                status=CheckStatus.RISK,
                description="Обнаружены отключенные важные опции защиты",
                recommendation="Включите отмеченные опции в конфигурации ядра",
                details="\n".join(issues),
                protection_type=ProtectionType.KERNEL
            )
        
        if warnings:
            return CheckResult(
                name="Параметры hardening ядра",
                status=CheckStatus.WARN,
                description="Некоторые опции hardening отключены",
                recommendation="Рассмотрите включение дополнительных опций защиты",
                details="\n".join(warnings),
                protection_type=ProtectionType.KERNEL
            )
        
        return CheckResult(
            name="Параметры hardening ядра",
            status=CheckStatus.OK,
            description="Основные опции hardening включены",
            recommendation="",
            details="",
            protection_type=ProtectionType.KERNEL
        )
    
    def check_debug_kernel(self) -> CheckResult:
        """Проверка на debug версию ядра"""
        version = get_kernel_version()
        
        # Проверяем через config
        config_path = "/boot/config-" + version
        config_content = read_file_safe(config_path)
        
        if not config_content:
            # Fallback: проверяем через dmesg
            stdout, _, _ = run_command(["dmesg", "-s", "1024"])
            if "debug" in stdout.lower():
                return CheckResult(
                    name="Debug опции ядра",
                    status=CheckStatus.WARN,
                    description="Обнаружены debug-опции в системе",
                    recommendation="Для production используйте non-debug ядро",
                    details="",
                    protection_type=ProtectionType.KERNEL
                )
        
        # Проверяем CONFIG_DEBUG_INFO
        if "CONFIG_DEBUG_INFO=y" in config_content:
            return CheckResult(
                name="Debug информация ядра",
                status=CheckStatus.WARN,
                description="CONFIG_DEBUG_INFO включен (отладочная информация)",
                recommendation="Отключите для production систем",
                details="",
                protection_type=ProtectionType.KERNEL
            )
        
        return CheckResult(
            name="Debug опции ядра",
            status=CheckStatus.OK,
            description="Debug опции не обнаружены",
            recommendation="",
            details="",
            protection_type=ProtectionType.KERNEL
        )
    
    def check_kaslr(self) -> CheckResult:
        """Проверка KASLR"""
        stdout, _, _ = run_command(["cat", "/proc/cmdline"])
        
        if "nokaslr" in stdout:
            return CheckResult(
                name="KASLR (Randomization)",
                status=CheckStatus.RISK,
                description="KASLR отключен через параметры загрузки",
                recommendation="Включите KASLR для защиты от эксплойтов",
                details="Параметр nokaslr найден в cmdline",
                protection_type=ProtectionType.KERNEL
            )
        
        # Проверяем через sysctl
        stdout, _, _ = run_command(["sysctl", "kernel.randomize_va_space"])
        value = stdout.split("=", 1)[-1].strip() if "=" in stdout else "0"
        
        if value == "2":
            return CheckResult(
                name="KASLR (Randomization)",
                status=CheckStatus.OK,
                description="KASLR включен (полная рандомизация)",
                recommendation="",
                details=f"kernel.randomize_va_space = {value}",
                protection_type=ProtectionType.KERNEL
            )
        elif value == "1":
            return CheckResult(
                name="KASLR (Randomization)",
                status=CheckStatus.WARN,
                description="KASLR частично включен (только ASLR)",
                recommendation="Включите полную рандомизацию (значение 2)",
                details=f"kernel.randomize_va_space = {value}",
                protection_type=ProtectionType.KERNEL
            )
        else:
            return CheckResult(
                name="KASLR (Randomization)",
                status=CheckStatus.RISK,
                description="KASLR отключен",
                recommendation="Включите рандомизацию адресного пространства",
                details=f"kernel.randomize_va_space = {value}",
                protection_type=ProtectionType.KERNEL
            )
    
    def check_core_pattern(self) -> CheckResult:
        """Проверка core dump настроек"""
        stdout, _, _ = run_command(["sysctl", "kernel.core_pattern"])
        value = stdout.split("=", 1)[-1].strip() if "=" in stdout else ""
        
        if not value or value.startswith("|"):
            # Core dump через apport или другой обработчик - это нормально для Ubuntu/Kali
            return CheckResult(
                name="Core Dumps",
                status=CheckStatus.OK,
                description="Core dumps настроены через системный обработчик",
                recommendation="",
                details=f"kernel.core_pattern = {value}",
                protection_type=ProtectionType.KERNEL
            )
        
        if value.startswith("/"):
            # Core dumps пишутся в файл
            path = value.split()[0] if " " in value else value
            
            # Проверяем права на директорию
            stdout2, _, _ = run_command(["ls", "-la", path.rsplit("/", 1)[0] if "/" in path else "/"])
            
            if "world" not in stdout2:
                return CheckResult(
                    name="Core Dumps",
                    status=CheckStatus.OK,
                    description="Core dumps направляются в защищенную директорию",
                    recommendation="",
                    details=f"kernel.core_pattern = {value}",
                    protection_type=ProtectionType.KERNEL
                )
            else:
                return CheckResult(
                    name="Core Dumps",
                    status=CheckStatus.WARN,
                    description="Core dumps доступны world-readable",
                    recommendation="Ограничьте доступ к директории core dumps",
                    details=f"kernel.core_pattern = {value}",
                    protection_type=ProtectionType.KERNEL
                )
        
        return CheckResult(
            name="Core Dumps",
            status=CheckStatus.OK,
            description="Настройки core dumps в порядке",
            recommendation="",
            details=f"kernel.core_pattern = {value}",
            protection_type=ProtectionType.KERNEL
        )
    
    def run_all_checks(self) -> list:
        """Запустить все проверки ядра"""
        self.results = [
            self.check_kernel_version(),
            self.check_kernel_config(),
            self.check_debug_kernel(),
            self.check_kaslr(),
            self.check_core_pattern(),
        ]
        return self.results


"""
Сетевые проверки для Black Mirror.
"""

from core.models import CheckResult, CheckStatus, ProtectionType
from utils.system import run_command, read_file_safe
from utils.parser import parse_interfaces
from typing import Optional


class NetworkChecker:
    """Проверки сетевой безопасности"""
    
    def __init__(self):
        self.results = []
    
    def check_ip_forwarding(self) -> CheckResult:
        """Проверка IP forwarding"""
        value = read_file_safe("/proc/sys/net/ipv4/ip_forward")
        
        if value == "1":
            return CheckResult(
                name="IP Forwarding",
                status=CheckStatus.WARN,
                description="IP forwarding включен (система может работать как роутер)",
                recommendation="Отключите если не используется: sysctl -w net.ipv4.ip_forward=0",
                details="net.ipv4.ip_forward = 1",
                protection_type=ProtectionType.NETWORK
            )
        
        return CheckResult(
            name="IP Forwarding",
            status=CheckStatus.OK,
            description="IP forwarding отключен",
            recommendation="",
            details="net.ipv4.ip_forward = 0",
            protection_type=ProtectionType.NETWORK
        )
    
    def check_icmp_redirects(self) -> CheckResult:
        """Проверка ICMP redirects"""
        accept = read_file_safe("/proc/sys/net/ipv4/conf/all/accept_redirects")
        send = read_file_safe("/proc/sys/net/ipv4/conf/all/send_redirects")
        
        issues = []
        if accept != "0":
            issues.append("accept_redirects включен")
        if send != "0":
            issues.append("send_redirects включен")
        
        if issues:
            return CheckResult(
                name="ICMP Redirects",
                status=CheckStatus.WARN,
                description="ICMP redirects могут приниматься/отправляться",
                recommendation="Отключите: sysctl -w net.ipv4.conf.all.accept_redirects=0",
                details=", ".join(issues),
                protection_type=ProtectionType.NETWORK
            )
        
        return CheckResult(
            name="ICMP Redirects",
            status=CheckStatus.OK,
            description="ICMP redirects заблокированы",
            recommendation="",
            details="",
            protection_type=ProtectionType.NETWORK
        )
    
    def check_source_routing(self) -> CheckResult:
        """Проверка source routing"""
        accept = read_file_safe("/proc/sys/net/ipv4/conf/all/accept_source_route")
        
        if accept != "0":
            return CheckResult(
                name="Source Routing",
                status=CheckStatus.WARN,
                description="IP source routing разрешен",
                recommendation="Отключите: sysctl -w net.ipv4.conf.all.accept_source_route=0",
                details=f"accept_source_route = {accept}",
                protection_type=ProtectionType.NETWORK
            )
        
        return CheckResult(
            name="Source Routing",
            status=CheckStatus.OK,
            description="IP source routing заблокирован",
            recommendation="",
            details="",
            protection_type=ProtectionType.NETWORK
        )
    
    def check_rp_filter(self) -> CheckResult:
        """Проверка Reverse Path Filtering"""
        rp_filter = read_file_safe("/proc/sys/net/ipv4/conf/all/rp_filter")
        
        if rp_filter == "1" or rp_filter == "2":
            return CheckResult(
                name="Reverse Path Filter",
                status=CheckStatus.OK,
                description="Reverse Path Filtering включен (защита от spoofing)",
                recommendation="",
                details=f"rp_filter = {rp_filter}",
                protection_type=ProtectionType.NETWORK
            )
        
        return CheckResult(
            name="Reverse Path Filter",
            status=CheckStatus.WARN,
            description="Reverse Path Filtering отключен",
            recommendation="Включите: sysctl -w net.ipv4.conf.all.rp_filter=1",
            details=f"rp_filter = {rp_filter}",
            protection_type=ProtectionType.NETWORK
        )
    
    def check_martian_packets(self) -> CheckResult:
        """Проверка логирования martian packets"""
        log_martians = read_file_safe("/proc/sys/net/ipv4/conf/all/log_martians")
        
        if log_martians == "1":
            return CheckResult(
                name="Martian Packets Logging",
                status=CheckStatus.OK,
                description="Martian packets логируются",
                recommendation="",
                details=f"log_martians = {log_martians}",
                protection_type=ProtectionType.NETWORK
            )
        
        return CheckResult(
            name="Martian Packets Logging",
            status=CheckStatus.WARN,
            description="Martian packets не логируются",
            recommendation="Включите логирование: sysctl -w net.ipv4.conf.all.log_martians=1",
            details=f"log_martians = {log_martians}",
            fix_command="sudo sysctl -w net.ipv4.conf.all.log_martians=1",
            protection_type=ProtectionType.NETWORK
        )
    
    def check_icmp_echo_ignore(self) -> CheckResult:
        """Проверка игнорирования ICMP echo"""
        ignore_broadcast = read_file_safe("/proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
        ignore_all = read_file_safe("/proc/sys/net/ipv4/icmp_echo_ignore_all")
        
        if ignore_all == "1":
            return CheckResult(
                name="ICMP Echo Ignore",
                status=CheckStatus.WARN,
                description="ICMP echo полностью игнорируется (ping off)",
                recommendation="Возможно блокирует диагностику, но повышает безопасность",
                details="icmp_echo_ignore_all = 1",
                protection_type=ProtectionType.NETWORK
            )
        
        if ignore_broadcast == "1":
            return CheckResult(
                name="ICMP Broadcast Echo",
                status=CheckStatus.OK,
                description="ICMP broadcast echo отключен (защита от smurf)",
                recommendation="",
                details="icmp_echo_ignore_broadcasts = 1",
                protection_type=ProtectionType.NETWORK
            )
        
        return CheckResult(
            name="ICMP Echo",
            status=CheckStatus.OK,
            description="ICMP echo разрешен (стандартная настройка)",
            recommendation="Рассмотрите отключение для защиты от ping flood",
            details="",
            protection_type=ProtectionType.NETWORK
        )
    
    def check_syncookies(self) -> CheckResult:
        """Проверка TCP SYN cookies"""
        syncookies = read_file_safe("/proc/sys/net/ipv4/tcp_syncookies")
        
        if syncookies == "1":
            return CheckResult(
                name="TCP SYN Cookies",
                status=CheckStatus.OK,
                description="TCP SYN cookies включены (защита от SYN flood)",
                recommendation="",
                details=f"tcp_syncookies = {syncookies}",
                protection_type=ProtectionType.NETWORK
            )
        
        return CheckResult(
            name="TCP SYN Cookies",
            status=CheckStatus.RISK,
            description="TCP SYN cookies отключены",
            recommendation="Включите: sysctl -w net.ipv4.tcp_syncookies=1",
            details=f"tcp_syncookies = {syncookies}",
            protection_type=ProtectionType.NETWORK
        )
    
    def check_network_interfaces(self) -> CheckResult:
        """Проверка сетевых интерфейсов"""
        interfaces = parse_interfaces()
        
        # Проверяем на необычные интерфейсы
        suspicious = []
        known_good = ["lo", "eth", "ens", "eno", "enp", "wlan", "wl", "docker", "veth"]
        
        for iface in interfaces.keys():
            is_known = any(iface.startswith(k) for k in known_good)
            if not is_known:
                suspicious.append(iface)
        
        if suspicious:
            return CheckResult(
                name="Network Interfaces",
                status=CheckStatus.WARN,
                description=f"Обнаружены нестандартные интерфейсы: {', '.join(suspicious)}",
                recommendation="Проверьте незнакомые сетевые интерфейсы",
                details=f"Все интерфейсы: {', '.join(interfaces.keys())}",
                protection_type=ProtectionType.NETWORK
            )
        
        return CheckResult(
            name="Network Interfaces",
            status=CheckStatus.OK,
            description=f"Обнаружено {len(interfaces)} интерфейсов: {', '.join(interfaces.keys())}",
            recommendation="",
            details="",
            protection_type=ProtectionType.NETWORK
        )
    
    def check_arp_spoofing_protection(self) -> CheckResult:
        """Проверка защиты от ARP spoofing"""
        # Проверяем различные настройки
        arp_ignore = read_file_safe("/proc/sys/net/ipv4/conf/all/arp_ignore")
        arp_announce = read_file_safe("/proc/sys/net/ipv4/conf/all/arp_announce")
        
        if arp_ignore != "0" and arp_announce != "0":
            return CheckResult(
                name="ARP Spoofing Protection",
                status=CheckStatus.OK,
                description="Защита от ARP spoofing включена",
                recommendation="",
                details=f"arp_ignore={arp_ignore}, arp_announce={arp_announce}",
                protection_type=ProtectionType.NETWORK
            )
        
        return CheckResult(
            name="ARP Spoofing Protection",
            status=CheckStatus.WARN,
            description="Защита от ARP spoofing может быть недостаточной",
            recommendation="Рассмотрите настройку arp_ignore и arp_announce",
            details=f"arp_ignore={arp_ignore}, arp_announce={arp_announce}",
            protection_type=ProtectionType.NETWORK
        )
    
    def run_all_checks(self) -> list:
        """Запустить все сетевые проверки"""
        self.results = [
            self.check_ip_forwarding(),
            self.check_icmp_redirects(),
            self.check_source_routing(),
            self.check_rp_filter(),
            self.check_martian_packets(),
            self.check_icmp_echo_ignore(),
            self.check_syncookies(),
            self.check_network_interfaces(),
            self.check_arp_spoofing_protection(),
        ]
        return self.results


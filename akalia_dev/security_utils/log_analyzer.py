import re
import logging
import datetime
from collections import defaultdict
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LogAnalyzer:
    def __init__(self, auth_log_path="/var/log/auth.log", iptables_log_path="/var/log/iptables.log"):
        self.auth_log_path = auth_log_path
        self.iptables_log_path = iptables_log_path
        self.banned_ips = set()  # IP-адреса заблокированных пользователей
        self.visit_count = defaultdict(int)  # Счетчик посещений по IP-адресам

    def read_log(self, log_path: str) -> List[str]:
        """Читает лог-файл построчно."""
        try:
            with open(log_path, 'r') as file:
                return file.readlines()
        except FileNotFoundError:
            logging.error(f"Лог-файл {log_path} не найден.")
            return []

    def analyze_auth_log(self) -> Tuple[int, List[str]]:
        """Анализ логов аутентификации для обнаружения неудачных попыток входа и блокировок."""
        failed_attempts = 0
        suspicious_ips = []

        for line in self.read_log(self.auth_log_path):
            if "Failed password" in line:
                failed_attempts += 1
                ip = self.extract_ip(line)
                if ip:
                    suspicious_ips.append(ip)
            elif "banned" in line:
                ip = self.extract_ip(line)
                if ip:
                    self.banned_ips.add(ip)

        logging.info(f"Неудачных попыток входа: {failed_attempts}")
        logging.info(f"Заблокированные IP-адреса: {self.banned_ips}")
        return failed_attempts, suspicious_ips

    def analyze_iptables_log(self) -> int:
        """Анализ логов iptables для учета заблокированных пакетов."""
        blocked_count = 0

        for line in self.read_log(self.iptables_log_path):
            if "IN=" in line and "BLOCK" in line:
                blocked_count += 1
                ip = self.extract_ip(line)
                if ip:
                    self.banned_ips.add(ip)

        logging.info(f"Заблокировано пакетов iptables: {blocked_count}")
        return blocked_count

    def count_visitors(self):
        """Подсчет уникальных посетителей на основе логов iptables."""
        for line in self.read_log(self.iptables_log_path):
            if "IN=" in line:  # Входящие пакеты
                ip = self.extract_ip(line)
                if ip:
                    self.visit_count[ip] += 1

        logging.info(f"Количество уникальных посетителей: {len(self.visit_count)}")
        return len(self.visit_count)

    def extract_ip(self, text: str) -> str:
        """Извлекает IP-адрес из строки текста."""
        match = re.search(r'[0-9]+(?:\.[0-9]+){3}', text)
        return match.group(0) if match else ""

    def generate_report(self):
        """Генерация отчета по всем логам и отправка в Telegram бот."""
        failed_attempts, suspicious_ips = self.analyze_auth_log()
        blocked_packets = self.analyze_iptables_log()
        visitors_count = self.count_visitors()

        report = (
            f"Отчет по безопасности:\n"
            f"Неудачные попытки входа: {failed_attempts}\n"
            f"Заблокированные IP-адреса: {len(self.banned_ips)}\n"
            f"Пакетов заблокировано iptables: {blocked_packets}\n"
            f"Уникальных посетителей: {visitors_count}\n"
            f"Подозрительные IP-адреса: {', '.join(suspicious_ips)}\n"
        )

        logging.info(report)
        # Здесь можно вызвать функцию отправки отчета в Telegram

# Пример использования
if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.generate_report()

import os
import psutil
import time
import logging
import requests
from datetime import datetime
from typing import List
from logging.handlers import RotatingFileHandler

# ========== Configuration ==========

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "your_bot_token_here")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your_chat_id_here")

# Setup logging with rotation
log_handler = RotatingFileHandler(
    "logs/performance_monitor.log", maxBytes=5 * 1024 * 1024, backupCount=5
)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


# ========== Functions ==========


def send_telegram_alert(message: str):
    """Send an alert message to a specified Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram alert: {e}")


def resource_usage() -> str:
    """Check current resource usage: CPU, RAM, and disk."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return f"CPU: {cpu}%, RAM: {ram}%, Disk: {disk}%"


def network_activity() -> str:
    """Get network activity statistics: bytes sent and received."""
    net_io = psutil.net_io_counters()
    return f"Bytes Sent: {net_io.bytes_sent}, Bytes Received: {net_io.bytes_recv}"


def detect_intrusions(
    suspicious_ips: List[str] = ["192.168.1.100"],
    suspicious_ports: List[int] = [22, 23],
) -> str:
    """
    Simple intrusion detection function.
    Checks for connections from suspicious IPs and to suspicious ports.
    """
    intrusions = []
    try:
        connections = psutil.net_connections()
        for conn in connections:
            if conn.raddr:
                remote_ip = conn.raddr.ip
                remote_port = conn.raddr.port
                if remote_ip in suspicious_ips or remote_port in suspicious_ports:
                    intrusions.append(f"IP: {remote_ip}, Port: {remote_port}")
    except psutil.AccessDenied:
        return "Access Denied to network connections."
    except Exception as e:
        return f"Error checking intrusions: {e}"

    if intrusions:
        alert_message = f"Suspicious activity detected from: {', '.join(intrusions)}"
        send_telegram_alert(alert_message)
        return alert_message
    return "No suspicious activity detected."


def monitor_performance(interval: int = 60):
    """Monitor system performance, logging data at the specified interval."""
    logger.info("Starting performance monitoring...")
    try:
        while True:
            usage = resource_usage()
            network = network_activity()
            intrusion_alert = detect_intrusions()

            # Log information
            logger.info(f"System Usage - {usage}")
            logger.info(f"Network Activity - {network}")
            logger.info(f"Intrusion Detection - {intrusion_alert}")

            # Print to console with a single timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{current_time}] {usage}")
            print(f"[{current_time}] {network}")
            print(f"[{current_time}] {intrusion_alert}")

            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Performance monitoring stopped by user.")


# ========== Standalone Execution ==========

if __name__ == "__main__":
    monitor_interval = int(
        os.getenv("MONITOR_INTERVAL", 60)
    )  # Set interval from env or default to 60 seconds
    monitor_performance(interval=monitor_interval)

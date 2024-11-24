import subprocess
import requests
import psutil
import ssl
import socket
from datetime import datetime
from typing import List, Optional

# ========== Network Scanning and Security Functions ==========


def network_scan(ip_range: str, ports: str = "80,443") -> str:
    """Scan network using masscan over IP range and specified ports."""
    try:
        result = subprocess.run(
            ["masscan", ip_range, "-p", ports],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running masscan: {e}"


def check_vulnerabilities(url: str) -> str:
    """Check server vulnerabilities using nikto."""
    try:
        result = subprocess.run(
            ["nikto", "-h", url], capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running nikto: {e}"


def system_health_check() -> str:
    """Check system health: CPU, RAM, and disk usage."""
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage("/").percent
    return (
        f"CPU Usage: {cpu_usage}%, RAM Usage: {ram_usage}%, Disk Usage: {disk_usage}%"
    )


def web_app_vuln_check(url: str) -> str:
    """Check web application availability and basic vulnerability."""
    try:
        response = requests.get(url, timeout=5)
        return (
            f"Web application {url} is accessible."
            if response.status_code == 200
            else f"Web application {url} is not accessible or may be down."
        )
    except requests.ConnectionError:
        return "Connection Error while checking web application vulnerability."
    except requests.Timeout:
        return "Request timed out while checking web application vulnerability."


def port_scan(ip: str, ports: List[int]) -> str:
    """Scan specified ports on a given IP address."""
    open_ports = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
    return (
        f"Open ports on {ip}: {open_ports}" if open_ports else f"No open ports on {ip}"
    )


def ssl_certificate_check(url: str) -> str:
    """Check website SSL certificate details, including issuer and expiry."""
    try:
        hostname = url.replace("https://", "").replace("http://", "").split("/")[0]
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        issuer = cert.get("issuer")
        expiry_date = cert.get("notAfter")
        issuer_info = " ".join(f"{item[0]}: {item[1]}" for item in issuer[0])

        expiry_date_obj = datetime.strptime(expiry_date, "%b %d %H:%M:%S %Y %Z")
        days_left = (expiry_date_obj - datetime.now()).days

        return (
            f"Issuer: {issuer_info}, Expiry Date: {expiry_date} ({days_left} days left)"
        )
    except ssl.SSLError as e:
        return f"SSL Certificate check failed due to SSL error: {e}"
    except (socket.error, ValueError) as e:
        return f"SSL Certificate check failed: {e}"


def security_header_check(url: str) -> str:
    """Check security headers of a website."""
    try:
        response = requests.get(url, timeout=5)
        headers = response.headers

        results = []
        if "Content-Security-Policy" in headers:
            results.append("Content-Security-Policy: Present")
        else:
            results.append("Content-Security-Policy: Missing")

        if "X-Frame-Options" in headers:
            results.append("X-Frame-Options: Present")
        else:
            results.append("X-Frame-Options: Missing")

        if "Strict-Transport-Security" in headers:
            results.append("Strict-Transport-Security: Present")
        else:
            results.append("Strict-Transport-Security: Missing")

        return "\n".join(results)
    except requests.ConnectionError:
        return "Connection Error while checking security headers."
    except requests.Timeout:
        return "Request timed out while checking security headers."


# ========== Example Usage (for testing purposes only) ==========
# print(network_scan("192.168.1.0/24"))
# print(check_vulnerabilities("http://example.com"))
# print(system_health_check())
# print(web_app_vuln_check("http://example.com"))
# print(port_scan("192.168.1.1", [80, 443, 8080]))
# print(ssl_certificate_check("https://example.com"))
# print(security_header_check("https://example.com"))
